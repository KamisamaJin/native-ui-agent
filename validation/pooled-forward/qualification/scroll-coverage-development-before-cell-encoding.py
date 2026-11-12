"""Conservative original-raster/AX overlap proof for a vertical native sweep.

Estimated lazy content height is not an actual terminal extent. A changing
estimate alone cannot establish or refute full observed scroll coverage. This
provider requires a connected original-pixel strip and independent native leaf
landmarks. It never infers computed styles, hidden branches or live-data closure.
"""
import hashlib
import io
import json
import math
from pathlib import Path


EPS = 1e-6  # Arithmetic noise only; no image/geometry acceptance tolerance.
LEAF_ROLES = {9, 48}  # Actual XCUI button and static-text leaves, not wrappers.


def finite(values):
    return all(type(v) in {int, float} and math.isfinite(v) for v in values)


def rectangle(v):
    if not isinstance(v, dict) or not finite([v.get(k) for k in ['x', 'y', 'width', 'height']]):
        raise ValueError('Finite native rectangle required')
    if min(v['width'], v['height']) <= 0: raise ValueError('Positive native rectangle required')
    return v


def inside(box, viewport):
    return (box['x'] >= viewport['x'] and box['y'] >= viewport['y'] and
            box['x'] + box['width'] <= viewport['x'] + viewport['width'] and
            box['y'] + box['height'] <= viewport['y'] + viewport['height'])


def in_scroll(node, by_index):
    index = node.get('parent_index'); seen = set()
    while index in by_index and index not in seen:
        seen.add(index); parent = by_index[index]
        if parent.get('identifier') == '__observer.scroll': return True
        index = parent.get('parent_index')
    return False


def anchors(snapshot):
    nodes = snapshot.get('nodes', []); by_index = {n.get('index'): n for n in nodes}
    if len(by_index) != len(nodes): raise ValueError('Unique AX indices required')
    parent_indices = {n.get('parent_index') for n in nodes}
    candidates = {}; identity_counts = {}
    for node in nodes:
        # An identifier on a container is not a leaf/visual landmark.
        if node['index'] in parent_indices or node.get('role_raw') not in LEAF_ROLES: continue
        lineage = []; index = node.get('parent_index'); seen = set(); in_scroll = False
        while index in by_index and index not in seen:
            seen.add(index); parent = by_index[index]
            if parent.get('identifier') == '__observer.scroll': in_scroll = True; break
            lineage.append([parent.get('role_raw'), parent.get('identifier', '')])
            index = parent.get('parent_index')
        if not in_scroll: continue
        identity = node.get('identifier') or node.get('label')
        if not identity or str(identity).startswith('__observer.'): continue
        global_identity = ('id', identity) if node.get('identifier') else ('label', node.get('role_raw'), identity)
        identity_counts[global_identity] = identity_counts.get(global_identity, 0) + 1
        key = json.dumps([node.get('role_raw'), 'id' if node.get('identifier') else 'label', identity], sort_keys=True)
        node = dict(node, _global_identity=global_identity, _lineage=lineage)
        candidates.setdefault(key, []).append(node)
    # Repeated labels/IDs never acquire identity through ordering or geometry.
    viewport = rectangle(snapshot.get('viewport'))
    return {key: rows[0] for key, rows in candidates.items() if len(rows) == 1
            and identity_counts[rows[0]['_global_identity']] == 1 and rows[0].get('fully_within_viewport') is True
            and inside(rectangle(rows[0].get('frame')), viewport)}


def certify(found, binding, root):
    result = {'version': 1, 'method': 'original_pixels_and_native_leaf_overlap', 'complete': False, 'links': [],
              'scope': 'Observed vertical component viewport strip in one native epoch; no hidden-branch, style, business or arbitrary asynchronous-content guarantee.'}
    try:
        if root is None: raise ValueError('Original screenshot root is unavailable')
        from PIL import Image, ImageChops
        root = Path(root).resolve()
        if (type(binding.get('pid')) is not int or binding['pid'] <= 0 or not binding.get('instance')
                or not isinstance(binding.get('input_sha256'), str) or len(binding['input_sha256']) != 64
                or any(type(binding.get(k)) is not int or binding[k] < 0 for k in ['fixture_index', 'event_revision'])):
            raise ValueError('Actual native process/input/event identity required')
        if not found or [i for i, _ in found] != list(range(found[0][0], found[-1][0] + 1)):
            raise ValueError('Consecutive original state snapshots required')
        rows = []
        for index, snap in found:
            if snap.get('binding') != binding or snap.get('binding_after_capture') != binding or snap.get('capture_consistent') is not True:
                raise ValueError('Native epoch/image binding drift')
            vp = rectangle(snap.get('viewport')); content = rectangle(snap.get('runtime', {}).get('content_frame'))
            if content['width'] > vp['width'] or content['x'] < vp['x'] or content['x'] + content['width'] > vp['x'] + vp['width']:
                raise ValueError('Content includes unsupported off-axis extent')
            app = rectangle(snap.get('app_frame')); pixels = snap.get('screenshot_pixels', {})
            if any(type(pixels.get(k)) is not int or pixels[k] <= 0 for k in ['width', 'height']):
                raise ValueError('Actual screenshot extent required')
            sx, sy = pixels['width'] / app['width'], pixels['height'] / app['height']
            path = (root / snap.get('screenshot', '')).resolve()
            if not path.is_relative_to(root) or not path.is_file(): raise ValueError('Original screenshot missing/outside root')
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as original: image = original.convert('RGBA')
            if image.size != (pixels['width'], pixels['height']): raise ValueError('Native/image size mismatch')
            offset = vp['y'] - content['y']
            rows.append({'index': index, 'snap': snap, 'vp': vp, 'content': content, 'app': app, 'sx': sx, 'sy': sy,
                         'offset': offset, 'image': image, 'sha256': hashlib.sha256(raw).hexdigest(), 'anchors': anchors(snap)})
        first, last = rows[0], rows[-1]
        if abs(first['offset']) > EPS: raise ValueError('Actual top extent not observed')
        sentinel = [n for n in last['snap'].get('nodes', []) if n.get('identifier') == '__observer.bottom']
        if len(sentinel) != 1 or sentinel[0].get('fully_within_viewport') is not True or last['snap'].get('bottom_sentinel_visible') is not True:
            raise ValueError('Unique fully observed native terminal sentinel required')
        by_index = {n.get('index'): n for n in last['snap']['nodes']}
        if not in_scroll(sentinel[0], by_index) or not inside(rectangle(sentinel[0].get('frame')), last['vp']):
            raise ValueError('Actual terminal sentinel geometry/root membership not established')
        if last['offset'] + last['vp']['height'] < last['content']['height'] - EPS:
            raise ValueError('Actual terminal content extent not observed')
        for before, after in zip(rows, rows[1:]):
            if before['vp'] != after['vp'] or before['app'] != after['app'] or (before['sx'], before['sy']) != (after['sx'], after['sy']):
                raise ValueError('Viewport/native-image mapping changed')
            shift = (after['offset'] - before['offset']) * before['sy']
            if shift <= 0 or abs(shift - round(shift)) > EPS: raise ValueError('Positive integral-pixel native scroll displacement required')
            lower = max(before['offset'], after['offset']); upper = min(before['offset'] + before['vp']['height'], after['offset'] + after['vp']['height'])
            if (upper - lower) * before['sy'] < 2: raise ValueError('No actual viewport pixel overlap')
            common = sorted(set(before['anchors']) & set(after['anchors'])); matched = []
            for key in common:
                a, b = before['anchors'][key], after['anchors'][key]
                if any(a.get(k) != b.get(k) for k in ['identifier', 'label', 'value', 'role_raw', 'enabled', 'selected', '_lineage']):
                    raise ValueError('Shared native leaf content/traits changed')
                af, bf = rectangle(a.get('frame')), rectangle(b.get('frame'))
                comparisons = [(af['x'] - before['content']['x'], bf['x'] - after['content']['x']),
                               (af['y'] - before['content']['y'], bf['y'] - after['content']['y']),
                               (af['width'], bf['width']), (af['height'], bf['height'])]
                if any(abs(x - y) > EPS for x, y in comparisons): raise ValueError('Native leaf reflow/projected position changed')
                matched.append({'identity': json.loads(key), 'before_index': a['index'], 'after_index': b['index'],
                                'content_y': af['y'] - before['content']['y'], 'height': af['height']})
            if not any(a['content_y'] + a['height'] <= b['content_y'] or b['content_y'] + b['height'] <= a['content_y']
                       for i, a in enumerate(matched) for b in matched[i + 1:]):
                raise ValueError('Two unambiguous vertically non-overlapping shared native leaves required')
            def overlap(row):
                vp, app = row['vp'], row['app']
                coordinates = [(vp['x'] - app['x']) * row['sx'],
                               (vp['y'] + lower - row['offset'] - app['y']) * row['sy'],
                               (vp['x'] + vp['width'] - app['x']) * row['sx'],
                               (vp['y'] + upper - row['offset'] - app['y']) * row['sy']]
                if any(abs(v - round(v)) > EPS for v in coordinates): raise ValueError('Viewport overlap not on actual pixel grid')
                box = tuple(round(v) for v in coordinates)
                if min(box[:2]) < 0 or box[2] > row['image'].width or box[3] > row['image'].height:
                    raise ValueError('Viewport overlap outside original image')
                return row['image'].crop(box), box
            a, abox = overlap(before); b, bbox = overlap(after)
            if a.size != b.size or any(channel.getbbox() is not None for channel in ImageChops.difference(a, b).split()):
                raise ValueError('Original overlapping pixels changed; no masking/resampling/tolerance allowed')
            result['links'].append({'before': before['index'], 'after': after['index'], 'before_image_sha256': before['sha256'],
                                    'after_image_sha256': after['sha256'], 'before_pixels': abox, 'after_pixels': bbox,
                                    'overlap_pixels': a.size, 'native_leaf_anchors': matched})
        result.update(complete=True, reason='Original top-to-terminal pixel strip has coherent native leaf overlap',
                      observed_terminal_height=last['content']['height'], estimated_heights=[r['content']['height'] for r in rows])
    except (ValueError, OSError, KeyError, TypeError, ImportError) as exc:
        result['reason'] = str(exc)
    return result
