"""Generic exact-byte publication closure; case aliases never change a seal."""
import hashlib
from pathlib import Path, PurePosixPath


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(path):
    if not isinstance(path, str) or not path:
        raise ValueError('Canonical relative publication path required')
    p = PurePosixPath(path)
    if p.is_absolute() or '..' in p.parts or str(p) != path:
        raise ValueError('Canonical relative publication path required')
    return path


def audit(required, published):
    if not required:
        raise ValueError('Nonempty sealed dependency set required')
    for path in list(required) + list(published):
        safe(path)
    for value in list(required.values()) + list(published.values()):
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Exact SHA256 required')
    folded = {}
    for path in published:
        folded.setdefault(path.casefold(), []).append(path)
    aliases = []
    direct = 0
    for path, expected in sorted(required.items()):
        if path in published:
            if published[path] != expected:
                raise ValueError('Published sealed bytes changed: ' + path)
            direct += 1
            continue
        candidates = folded.get(path.casefold(), [])
        if len(candidates) != 1:
            raise ValueError('Missing or ambiguous sealed publication dependency: ' + path)
        source = candidates[0]
        if published[source] != expected:
            raise ValueError('Case alias has different original bytes: ' + path)
        aliases.append({'requested': path, 'published': source, 'sha256': expected})
    return {'requiredCount': len(required), 'directCount': direct, 'caseAliases': aliases}


def prepare(root, aliases):
    root = Path(root).resolve()
    for alias in aliases:
        source = root / safe(alias['published'])
        target = root / safe(alias['requested'])
        if not source.resolve().is_relative_to(root) or sha(source) != alias['sha256']:
            raise ValueError('Original alias source missing or changed')
        if target.exists():
            if not target.resolve().is_relative_to(root) or sha(target) != alias['sha256']:
                raise ValueError('Existing alias differs; never overwrite')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.parent.resolve().is_relative_to(root):
                raise ValueError('Alias escapes publication root')
            with target.open('xb') as stream:
                stream.write(source.read_bytes())
