"""Conservative platform dependencies over the existing complete production roots."""
from pathlib import Path
import design_contract as d


def model(config, platform):
    if platform not in {'ios', 'android'}:
        raise ValueError('Known source platform required')
    roots = [str(Path(p).resolve()) for p in config['source_roots']]
    if not roots or len(roots) != len(set(roots)):
        raise ValueError('Unique complete production source roots required')
    for root in map(Path, roots):
        paths = root.rglob('*') if root.is_dir() else [root]
        if any(p.is_symlink() for p in paths):
            raise ValueError('Production source symlink needs an explicit dependency provider')
    declared = config.get('platform_source_roots', {})
    if not isinstance(declared, dict) or set(declared) - {'ios', 'android', 'shared'}:
        raise ValueError('Only ios/android/shared dependency groups are supported')
    groups = {}
    for key in ['ios', 'android', 'shared']:
        values = declared.get(key, [])
        if not isinstance(values, list):
            raise ValueError('Platform dependencies must be source-root lists')
        values = [str(Path(p).resolve()) for p in values]
        if len(values) != len(set(values)) or not set(values) <= set(roots):
            raise ValueError('Dependencies must name exact existing complete source roots')
        groups[key] = values
    # Unclassified roots are shared, never silently ignored. Overlap is also
    # conservative: a root used by both platforms invalidates both.
    assigned = set().union(*map(set, groups.values()))
    groups['shared'] = sorted(set(groups['shared']) | (set(roots) - assigned))
    indices = [i for i, root in enumerate(roots) if root in groups[platform] or root in groups['shared']]
    if not indices:
        raise ValueError('A platform cannot certify an empty production dependency set')
    return {'version': 1, 'platform': platform, 'source_roots': roots, 'groups': groups, 'indices': indices}


def select(full, value):
    wanted = {str(i) for i in value['indices']}
    selected = {key: sha for key, sha in full.items() if key.split('/', 1)[0] in wanted}
    if not selected:
        raise ValueError('Actual platform production source set is empty')
    return selected


def fingerprint(config, platform):
    import execution_plan as xp
    return select(xp.source_fingerprint(config['source_roots']), model(config, platform))


def receipt_fingerprint(roots, value=None):
    import execution_plan as xp
    full = xp.source_fingerprint(roots)
    if value is None:
        return full
    expected = model({'source_roots': roots, 'platform_source_roots': value['groups']}, value['platform'])
    if value != expected:
        raise ValueError('Source dependency model changed')
    return select(full, value)


def verify_model(config, receipt, base, platform):
    value = receipt.get('source_model')
    if value is None:
        if config.get('platform_source_roots'):
            raise ValueError('Legacy global capture has no approved platform dependency identity')
        return None
    if value != model(config, platform) or d.digest(value) != receipt.get('source_model_sha256'):
        raise ValueError('Original platform dependency identity differs')
    if d.load(Path(base) / 'source-model.json') != value:
        raise ValueError('Original source dependency file changed')
    return value
