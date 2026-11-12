"""Original-raster strip registration with exact rational native pixel-cell bounds.

This is pixel-registration compatibility, never native geometry/style equality.
Closed-domain admission is separate from the observed-strip certificate. Raw
native metrics and their independently approved assertion tolerances are intact.
"""
import hashlib
import io
import json
import math
from fractions import Fraction
from pathlib import Path

LEAF_ROLES = {9, 48}  # Actual XCUI button/static-text leaves; never a wrapper.
NATIVE_ENCODING = {'version': 1, 'representation': 'ieee754-binary64', 'coordinate_space': 'logical_screen_points',
                   'provider': 'XCUIElementSnapshot.frame_and_native_CGRect', 'mapping': 'app_frame_to_original_screenshot_pixels'}


def number(v):
    if type(v) not in {int, float} or not math.isfinite(v): raise ValueError('Finite IEEE64/integer native coordinate required')
    return Fraction(v)


def rectangle(v):
    if not isinstance(v, dict) or set(v) != {'x', 'y', 'width', 'height'}:
        raise ValueError('Exact native rectangle required')
    r = {k: number(v[k]) for k in v}
    if min(r['width'], r['height']) <= 0: raise ValueError('Positive native rectangle required')
    return r


def inside(box, vp):
    return box['x'] >= vp['x'] and box['y'] >= vp['y'] and box['x'] + box['width'] <= vp['x'] + vp['width'] and box['y'] + box['height'] <= vp['y'] + vp['height']


def cells(value): return math.floor(value), math.ceil(value)
def integers(a, b): return set(range(max(a[0], b[0]), min(a[1], b[1]) + 1))


def lineage(node, by_index):
    result = []; seen = set(); index = node.get('parent_index')
    while index in by_index and index not in seen:
        seen.add(index); parent = by_index[index]
        if parent.get('identifier') == '__observer.scroll': return result
        result.append([parent.get('role_raw'), parent.get('identifier', '')]); index = parent.get('parent_index')
    return None


def native_rows(found, binding):
    if (type(binding.get('pid')) is not int or binding['pid'] <= 0 or not binding.get('instance')
            or not isinstance(binding.get('input_sha256'), str) or len(binding['input_sha256']) != 64
            or any(type(binding.get(k)) is not int or binding[k] < 0 for k in ['fixture_index', 'event_revision'])):
        raise ValueError('Actual native process/input/event identity required')
    if not found or [i for i, _ in found] != list(range(found[0][0], found[-1][0] + 1)):
        raise ValueError('Consecutive original state snapshots required')
    rows = []
    for index, snap in found:
        if snap.get('geometry_encoding') != NATIVE_ENCODING: raise ValueError('Explicit supported lossless native geometry encoding required')
        if snap.get('binding') != binding or snap.get('binding_after_capture') != binding or snap.get('capture_consistent') is not True:
            raise ValueError('Native epoch/image binding drift')
        vp = rectangle(snap.get('viewport')); content = rectangle(snap.get('runtime', {}).get('content_frame'))
        app = rectangle(snap.get('app_frame')); pixels = snap.get('screenshot_pixels', {})
        if any(type(pixels.get(k)) is not int or pixels[k] <= 0 for k in ['width', 'height']): raise ValueError('Actual screenshot extent required')
        sx, sy = Fraction(pixels['width'], app['width']), Fraction(pixels['height'], app['height'])
        edges = ((vp['x']-app['x'])*sx,(vp['y']-app['y'])*sy,(vp['x']+vp['width']-app['x'])*sx,(vp['y']+vp['height']-app['y'])*sy)
        if any(q.denominator != 1 for q in edges): raise ValueError('Original viewport must map to an integral pixel rectangle')
        box = tuple(int(q) for q in edges)
        if min(box[:2]) < 0 or box[2] > pixels['width'] or box[3] > pixels['height']: raise ValueError('Viewport outside original image')
        if content['x'] < vp['x'] or content['x'] + content['width'] > vp['x'] + vp['width']:
            raise ValueError('Content includes unsupported off-axis extent')
        nodes = snap.get('nodes', []); by_index = {n.get('index'): n for n in nodes}
        if len(by_index) != len(nodes) or len([n for n in nodes if n.get('identifier') == '__observer.scroll']) != 1:
            raise ValueError('Unique native scroll root and AX indices required')
        parents = {n.get('parent_index') for n in nodes}; groups = {}; global_ids = {}
        for node in nodes:
            if node.get('identifier'):
                identity_key = json.dumps(['id', node['identifier']])
                global_ids[identity_key] = global_ids.get(identity_key,0)+1
        for node in nodes:
            if node.get('index') in parents or node.get('role_raw') not in LEAF_ROLES: continue
            ancestry = lineage(node, by_index)
            if ancestry is None: continue
            identity = node.get('identifier') or node.get('label')
            if not identity or str(identity).startswith('__observer.'): continue
            # Native IDs are globally unique, regardless of role/container.
            key = json.dumps(['id', identity] if node.get('identifier') else ['label', node.get('role_raw'), identity])
            groups.setdefault(key, []).append(dict(node, _lineage=ancestry))
        offset = (vp['y'] - content['y']) * sy
        rows.append({'index': index, 'snap': snap, 'vp': vp, 'content': content, 'app': app, 'sx': sx, 'sy': sy,
                     'viewport_pixels': box, 'offset_cells': cells(offset), 'groups': groups, 'global_ids': global_ids})
    first, last = rows[0], rows[-1]
    if first['vp']['y'] != first['content']['y']: raise ValueError('Actual top extent not observed')
    sentinel = [n for n in last['snap'].get('nodes', []) if n.get('identifier') == '__observer.bottom']
    if len(sentinel) != 1 or sentinel[0].get('fully_within_viewport') is not True or last['snap'].get('bottom_sentinel_visible') is not True:
        raise ValueError('Unique fully observed native terminal sentinel required')
    by_index = {n.get('index'): n for n in last['snap']['nodes']}
    if lineage(sentinel[0], by_index) is None or not inside(rectangle(sentinel[0].get('frame')), last['vp']):
        raise ValueError('Actual terminal sentinel geometry/root membership not established')
    boundary = last['snap'].get('bottom_boundary',{})
    if (boundary.get('queried') is not True or boundary.get('match_count')!=1 or boundary.get('hittable') is not True
            or boundary.get('method')!='XCUIElement.isHittable' or boundary.get('binding')!=binding
            or boundary.get('identifier')!='__observer.bottom' or not inside(rectangle(boundary.get('frame')),last['vp'])):
        raise ValueError('Executed unique current native terminal hittability guard is unavailable')
    if not (solutions(projected(last,sentinel[0],0)) & solutions(projected(last,boundary,0))):
        raise ValueError('Native terminal guard geometry conflicts with original snapshot')
    terminal = (last['content']['y'] + last['content']['height'] - last['app']['y']) * last['sy']
    if math.ceil(terminal) > last['viewport_pixels'][3]: raise ValueError('Actual terminal content extent not observed')
    ambiguous = {key for row in rows for key, values in row['groups'].items() if len(values) != 1}
    ambiguous.update(key for row in rows for key,count in row['global_ids'].items() if count != 1)
    for row in rows:
        row['anchors'] = {key: values[0] for key, values in row['groups'].items() if key not in ambiguous
                          and values[0].get('fully_within_viewport') is True and inside(rectangle(values[0].get('frame')), row['vp'])}
    return rows


def projected(row, node, registered):
    r = rectangle(node.get('frame')); app = row['app']; sx, sy = row['sx'], row['sy']; vp = row['viewport_pixels']
    return {'left': cells((r['x']-app['x'])*sx - vp[0]), 'right': cells((r['x']+r['width']-app['x'])*sx - vp[0]),
            'top': cells((r['y']-app['y'])*sy - vp[1] + registered),
            'bottom': cells((r['y']+r['height']-app['y'])*sy - vp[1] + registered),
            'width': cells(r['width']*sx), 'height': cells(r['height']*sy)}


def solutions(projection):
    p = projection; result = set()
    for left in range(p['left'][0], p['left'][1]+1):
        for right in range(p['right'][0], p['right'][1]+1):
            if not p['width'][0] <= right-left <= p['width'][1] or right <= left: continue
            for top in range(p['top'][0], p['top'][1]+1):
                for bottom in range(p['bottom'][0], p['bottom'][1]+1):
                    if p['height'][0] <= bottom-top <= p['height'][1] and bottom > top: result.add((left, top, right, bottom))
    return result


def traits(node): return {k: node.get(k) for k in ['identifier', 'label', 'value', 'role_raw', 'enabled', 'selected', '_lineage']}


def extend(registry, row, registered, orderings):
    current = dict(registry); orders = dict(orderings)
    keys = sorted(row['anchors'])
    for i,key in enumerate(keys):
        for other in keys[i+1:]:
            a = number(row['anchors'][key]['frame']['y']); b = number(row['anchors'][other]['frame']['y'])
            order = (a > b) - (a < b)
            if (key,other) in orders and orders[(key,other)] != order: raise ValueError('Repeated native leaf order changed')
            orders[(key,other)] = order
    for key, node in row['anchors'].items():
        possible = solutions(projected(row, node, registered)); attributes = traits(node)
        if key in current:
            previous = current[key]
            if previous['traits'] != attributes: raise ValueError('Repeated native leaf traits/root/order changed')
            possible &= previous['rectangles']
        if not possible: raise ValueError('Repeated native leaf edge/width/height enclosures contradict registration')
        current[key] = {'traits': attributes, 'rectangles': possible}
    return current,orders


def certify(found, binding, root):
    result = {'version': 2, 'proof_strategy': 'observed-strip-chain-1', 'geometry_encoding': 'native-rect-pixel-cell-enclosure-v1',
              'complete': False, 'links': [], 'scope': 'Observed closed main-scroll viewport strip; no native geometry/style equality or hidden/live/off-axis branch guarantee.'}
    try:
        if root is None: raise ValueError('Original screenshot root is unavailable')
        from PIL import Image, ImageChops
        root = Path(root).resolve(); rows = native_rows(found, binding)
        encoding = None
        for row in rows:
            path = (root / row['snap'].get('screenshot', '')).resolve()
            if not path.is_relative_to(root) or not path.is_file(): raise ValueError('Original screenshot missing/outside root')
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as original:
                if original.format != 'PNG' or original.mode not in {'RGB', 'RGBA'}: raise ValueError('Supported lossless 8-bit RGB/RGBA PNG required')
                info = {'mode': original.mode, 'icc_sha256': hashlib.sha256(original.info['icc_profile']).hexdigest() if original.info.get('icc_profile') else None,
                        'gamma': original.info.get('gamma'), 'srgb': original.info.get('srgb')}
                if encoding is not None and info != encoding: raise ValueError('Original image color/alpha encodings differ')
                encoding = info; row['image'] = original.convert('RGBA')
            if row['image'].size != (row['snap']['screenshot_pixels']['width'], row['snap']['screenshot_pixels']['height']): raise ValueError('Native/image size mismatch')
            row['image_sha256'] = hashlib.sha256(raw).hexdigest()
        registered = 0; registry,orders = extend({}, rows[0], 0, {})
        for before, after in zip(rows, rows[1:]):
            if before['vp'] != after['vp'] or before['app'] != after['app'] or before['viewport_pixels'] != after['viewport_pixels'] or (before['sx'],before['sy']) != (after['sx'],after['sy']):
                raise ValueError('Viewport/native-image mapping changed')
            vp = before['viewport_pixels']; width, height = vp[2]-vp[0], vp[3]-vp[1]
            common = sorted(set(before['anchors']) & set(after['anchors']))
            if len(common) < 2: raise ValueError('Two globally unique native typed leaves required')
            lo = max(1, after['offset_cells'][0] - before['offset_cells'][1]); hi = min(height-1, after['offset_cells'][1] - before['offset_cells'][0])
            # Raw native enclosure candidates only constrain the lossless raster
            # search. They never choose a translation or alter a style rule.
            candidates = []; valid = []
            for delta in range(lo, hi+1):
                row = {'translation_pixels': delta}; candidates.append(row)
                try:
                    new_registry,new_orders = extend(registry, after, registered+delta, orders)
                    witnesses = []
                    for key in common:
                        if traits(before['anchors'][key]) != traits(after['anchors'][key]): raise ValueError('Adjacent native leaf traits differ')
                        choices = solutions(projected(before,before['anchors'][key],registered)) & new_registry[key]['rectangles']
                        if not choices: raise ValueError('Adjacent native leaf geometry enclosures contradict motion')
                        witnesses.append({'identity': json.loads(key), 'before_index': before['anchors'][key]['index'],
                                          'after_index': after['anchors'][key]['index'], 'common_pixel_rectangles': sorted(choices)})
                    def disjoint_native(ka,kb):
                        for r in [before,after]:
                            a,b = (rectangle(r['anchors'][key]['frame']) for key in [ka,kb])
                            if not (a['y']+a['height'] <= b['y'] or b['y']+b['height'] <= a['y']): return False
                        return True
                    if not any(disjoint_native(common[i],common[j]) and (a[3] <= b[1] or b[3] <= a[1])
                               for i,w in enumerate(witnesses) for j,z in enumerate(witnesses) if j>i
                               for a in w['common_pixel_rectangles'] for b in z['common_pixel_rectangles']):
                        raise ValueError('Two vertically non-overlapping witness rectangles required')
                    abox = (vp[0],vp[1]+delta,vp[2],vp[3]); bbox = (vp[0],vp[1],vp[2],vp[3]-delta)
                    a = before['image'].crop(abox); b = after['image'].crop(bbox)
                    channels = ImageChops.difference(a,b).split(); boxes = [c.getbbox() for c in channels]
                    row.update(before_pixels=abox,after_pixels=bbox,overlap_pixels=a.size,
                               before_strip_sha256=hashlib.sha256(a.tobytes()).hexdigest(),after_strip_sha256=hashlib.sha256(b.tobytes()).hexdigest(),
                               channel_difference_bounds=boxes,exact=not any(boxes))
                    if any(boxes): raise ValueError('Original full-width overlapping pixels differ')
                    row['native_leaf_witnesses'] = witnesses; valid.append((delta,new_registry,new_orders,row))
                except ValueError as exc: row['rejection_reason'] = str(exc)
            result['links'].append({'before':before['index'],'after':after['index'], 'before_image_sha256':before['image_sha256'],
                                    'after_image_sha256':after['image_sha256'],'candidate_translations':candidates})
            if len(valid) != 1: raise ValueError('Unique exact raster translation with all native enclosures not established')
            delta,registry,orders,proof = valid[0]; registered += delta
            result['links'][-1].update(unique_translation_pixels=delta,registered_end_pixels=registered+height)
        result.update(complete=True,reason='Original top-to-terminal raster strip has unique coherent native leaf registration',
                      observed_terminal_height=rows[-1]['snap']['runtime']['content_frame']['height'],
                      estimated_heights=[r['snap']['runtime']['content_frame']['height'] for r in rows],image_encoding=encoding,
                      repeated_leaf_compatible_rectangles={k:sorted(v['rectangles'])for k,v in registry.items()})
    except (ValueError,OSError,KeyError,TypeError,ImportError,OverflowError) as exc: result['reason'] = str(exc)
    return result
