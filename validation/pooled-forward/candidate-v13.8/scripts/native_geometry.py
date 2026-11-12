"""Geometry from actual native samples; no implicit design tolerance or epsilon."""
from fractions import Fraction
import math


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Finite native number required')
    return Fraction(value)


def native_box(node, platform):
    if platform == 'android':
        sample = node.get('native_geometry')
        if sample is None:
            return None
        if (not isinstance(sample, dict) or sample.get('version') != 1 or sample.get('provider') != 'compose_semantics_int_size'
                or sample.get('coordinate_unit') != 'px'):
            raise ValueError('Unknown native geometry provider')
        density = number(sample.get('density'))
        position, size = sample.get('position_px'), sample.get('size_px')
        if (density <= 0 or not isinstance(position, list) or len(position) != 2
                or not isinstance(size, list) or len(size) != 2
                or any(type(v) is not int or v <= 0 for v in size)):
            raise ValueError('Invalid native pixel sample')
        x, y = (number(v) / density for v in position)
        width, height = (Fraction(v) / density for v in size)
        return (x, y, width, height), {'provider': sample['provider'], 'sample': sample,
                'unit': 'dp', 'scope': 'Observed semantics rectangle; not full layout allocation or OS hit region.'}
    frame = node.get('frame')
    if frame is None:
        return None
    if not isinstance(frame, dict):
        raise ValueError('Invalid native AX rectangle')
    x, y, width, height = (number(frame.get(k)) for k in ('x', 'y', 'width', 'height'))
    if width <= 0 or height <= 0:
        raise ValueError('Invalid native AX rectangle')
    return (x, y, width, height), {'provider': 'xcui_cgrect', 'sample': frame, 'unit': 'pt',
            'scope': 'Public AX rectangle; not full layout allocation or OS hit region.'}


def measure(snapshot, item, platform, resolve):
    if item.get('measurement') == 'layout_box':
        return None
    proofs = []
    def box(selector):
        resolved = resolve(snapshot, selector, platform)
        node = resolved.get(item.get('basis', 'semantic'), {})
        if (not resolved['facts'].get('unique') or not node.get('intersects_viewport')
                or not node.get('fully_within_viewport', node.get('fully_visible', False))):
            return None
        result = native_box(node, platform)
        if result is None:
            return None
        value, proof = result
        proofs.append(dict(proof, selector=selector, node_id=node.get('node_id')))
        return value
    a = box(item['target'])
    if a is None:
        return None
    prop = item['property']
    if prop == 'width': value = a[2]
    elif prop == 'height': value = a[3]
    else:
        b = box(item['reference_target'])
        if b is None: return None
        value = {'gap_x': a[0] - b[0] - b[2], 'gap_y': a[1] - b[1] - b[3],
                 'inset_left': a[0] - b[0], 'inset_right': b[0] + b[2] - a[0] - a[2],
                 'inset_top': a[1] - b[1], 'inset_bottom': b[1] + b[3] - a[1] - a[3]}[prop]
    return {'value': float(value), 'ratio': [value.numerator, value.denominator],
            'method': 'exact_operations_on_recorded_native_samples', 'sources': proofs,
            'policy': 'No implicit epsilon, pixel snapping or design tolerance. Missing native samples do not certify legacy rounded bounds.'}


def compare(measurement, expected, op, tolerance=None):
    value = Fraction(*measurement['ratio']); wanted = number(expected)
    if op == 'eq': return value == wanted
    if op == 'gte': return value >= wanted
    if op == 'lte': return value <= wanted
    if op == 'near': return abs(value - wanted) <= number(tolerance)
    raise ValueError('Numeric geometry comparator required')
