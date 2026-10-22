"""Rendered sRGB samples scoped to original state/target/viewport, not computed styles."""
from __future__ import annotations

from collections import Counter
import hashlib
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(values):
    return all(type(v) in {int, float} and math.isfinite(v) for v in values)


def validate_sampling(spec):
    if set(spec) != {'region', 'minimum_pixels', 'minimum_support', 'channel_tolerance', 'basis', 'visibility'}:
        raise ValueError('Exact independently approved pixel sampling policy required')
    region = spec['region']
    if not isinstance(region, list) or len(region) != 4 or not finite(region) or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1):
        raise ValueError('Pixel region must be a normalized target-local rectangle')
    if type(spec['minimum_pixels']) is not int or spec['minimum_pixels'] < 1:
        raise ValueError('Positive pixel count required')
    if not finite([spec['minimum_support']]) or not .5 < spec['minimum_support'] <= 1:
        raise ValueError('Unique dominant-color support must exceed one half')
    if type(spec['channel_tolerance']) is not int or not 0 <= spec['channel_tolerance'] <= 255:
        raise ValueError('Explicit nonnegative rendered RGB channel tolerance required')
    if spec['basis'] not in {'semantic', 'control'} or spec['visibility'] not in {'fully_visible', 'visible_fragment'}:
        raise ValueError('Explicit native box basis and visibility scope required')


def image_rectangle(snapshot, node, platform, size):
    """Map original native coordinates; prefer an explicit integer viewport packet."""
    width, height = size
    if snapshot.get('screenshot_pixels') != {'width': width, 'height': height}:
        raise ValueError('Original screenshot dimensions differ from native capture')
    if platform == 'ios':
        app, box, viewport = snapshot.get('app_frame', {}), node.get('frame', {}), snapshot.get('viewport', {})
        if any(not all(k in v for k in ['x', 'y', 'width', 'height']) for v in [app, box, viewport]):
            return None
        if not finite([v[k] for v in [app, box, viewport] for k in ['x', 'y', 'width', 'height']]) or app['width'] <= 0 or app['height'] <= 0:
            return None
        sx, sy = width / app['width'], height / app['height']
        convert = lambda r: [(r['x'] - app['x']) * sx, (r['y'] - app['y']) * sy,
                             (r['x'] + r['width'] - app['x']) * sx, (r['y'] + r['height'] - app['y']) * sy]
        box, clip = convert(box), convert(viewport)
    else:
        native = snapshot.get('native_viewport_px')
        geometry = node.get('native_geometry')
        if native is not None and geometry is not None:
            if (set(native) != {'width', 'height', 'density'} or
                    any(type(native[k]) is not int or native[k] <= 0 for k in ['width', 'height']) or
                    geometry.get('version') != 1 or geometry.get('provider') != 'compose_semantics_int_size' or
                    geometry.get('coordinate_unit') != 'px' or geometry.get('density') != native['density']):
                return None
            position, extent = geometry.get('position_px'), geometry.get('size_px')
            if (not isinstance(position, list) or len(position) != 2 or not finite(position) or
                    not isinstance(extent, list) or len(extent) != 2 or any(type(v) is not int or v <= 0 for v in extent)):
                return None
            sx, sy = width / native['width'], height / native['height']
            box = [position[0] * sx, position[1] * sy, (position[0] + extent[0]) * sx, (position[1] + extent[1]) * sy]
            return box, [0, 0, width, height]
        viewport, bounds = snapshot.get('logical_viewport_dp', {}), node.get('unclipped_bounds_dp')
        if not bounds or len(bounds) != 4 or not finite(bounds) or not finite([viewport.get('width'), viewport.get('height')]) or min(viewport['width'], viewport['height']) <= 0:
            return None
        sx, sy = width / viewport['width'], height / viewport['height']
        box = [bounds[0] * sx, bounds[1] * sy, bounds[2] * sx, bounds[3] * sy]
        clip = [0, 0, width, height]
    if box[2] <= box[0] or box[3] <= box[1]:
        return None
    return box, [max(0, clip[0]), max(0, clip[1]), min(width, clip[2]), min(height, clip[3])]


def sample(snapshot, selector, platform, root, spec):
    from PIL import Image
    from native_checks import resolve
    validate_sampling(spec)
    resolved = resolve(snapshot, selector, platform)
    if not resolved['facts']['unique']:
        return {'status': 'unassessed', 'reason': 'Target is missing or ambiguous'}
    node = resolved[spec['basis']]
    if not node or not node.get('intersects_viewport'):
        return {'status': 'unassessed', 'reason': 'Approved native box is unavailable'}
    if spec['visibility'] == 'fully_visible' and not node.get('fully_within_viewport', node.get('fully_visible', False)):
        return {'status': 'unassessed', 'reason': 'Target is not fully visible'}
    path = (root / snapshot['screenshot']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Pixel evidence missing or outside original observation root')
    with Image.open(path) as image:
        mapping = image_rectangle(snapshot, node, platform, image.size)
        if mapping is None:
            return {'status': 'unassessed', 'reason': 'Native-to-image mapping unavailable'}
        box, clip = mapping
        x0, y0, x1, y1 = spec['region']
        region = [box[0] + x0 * (box[2] - box[0]), box[1] + y0 * (box[3] - box[1]),
                  box[0] + x1 * (box[2] - box[0]), box[1] + y1 * (box[3] - box[1])]
        # Sample only pixel centers strictly within the approved region and viewport.
        roi = [math.ceil(max(region[0], clip[0]) - .5), math.ceil(max(region[1], clip[1]) - .5),
               math.ceil(min(region[2], clip[2]) - .5), math.ceil(min(region[3], clip[3]) - .5)]
        if roi[2] <= roi[0] or roi[3] <= roi[1]:
            return {'status': 'unassessed', 'reason': 'Approved pixel region is outside captured viewport'}
        # Native screenshots are sRGB/RGB; do not silently color-convert profiles.
        if image.info.get('icc_profile'):
            return {'status': 'unassessed', 'reason': 'Embedded color profile needs an explicit approved conversion'}
        rgba = image.convert('RGBA').crop(tuple(roi))
        histogram = Counter(rgba.getdata())
        count = sum(histogram.values())
        ordered = sorted(histogram.items(), key=lambda p: (-p[1], p[0]))
        proof = {'path': str(path.relative_to(root.resolve())), 'sha256': sha(path), 'image_size': list(image.size),
                 'native_selector': selector, 'native_box_basis': spec['basis'], 'native_box_in_image': box,
                 'native_geometry': node.get('native_geometry'), 'native_viewport_px': snapshot.get('native_viewport_px'),
                 'viewport_in_image': clip, 'region_pixels': roi, 'sample_count': count,
                 'histogram': [{'rgba': list(color), 'count': n} for color, n in ordered], 'sampling_policy': spec}
        if count < spec['minimum_pixels'] or not ordered or ordered[0][1] / count < spec['minimum_support']:
            return {'status': 'unassessed', 'reason': 'Insufficient unambiguous solid-color support', 'proof': proof}
        color = ordered[0][0]
        if color[3] != 255:
            return {'status': 'unassessed', 'reason': 'Transparent screenshot samples need an explicit compositing model', 'proof': proof}
        return {'status': 'measured', 'argb': (255 << 24) | (color[0] << 16) | (color[1] << 8) | color[2],
                'reason': 'Dominant rendered sRGB in approved native-target region', 'proof': proof}


def matches(actual, expected, channel_tolerance):
    """Tolerance is on rendered RGB channels; never use packed-integer distance."""
    if type(expected) is not int or not 0 <= expected <= 0xffffffff or expected >> 24 != 255:
        raise ValueError('Opaque ARGB expectation required for rendered screenshot color')
    return all(abs(((actual >> shift) & 255) - ((expected >> shift) & 255)) <= channel_tolerance for shift in [16, 8, 0])
