"""Read-only byte/namespace verification of this review using an external seal pin.

Fixture modes/identities are recorded evidence, not portable immutable claims.
This checker does not execute the SUT, follow fixture symlinks, or open any
original dataset path. The caller supplies the trusted SHA of SEAL.json.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


def need(ok, message):
    if not ok: raise ValueError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def inventory(root):
    rows = {}
    for folder, directories, names in os.walk(root, followlinks=False):
        base = Path(folder)
        for name in list(directories):
            if (base / name).is_symlink():
                directories.remove(name); names.append(name)
        for name in names:
            path = base / name; relative = path.relative_to(root).as_posix()
            if relative == 'SEAL.json': continue
            value = path.lstat()
            if stat.S_ISLNK(value.st_mode):
                rows[relative] = {'kind': 'symlink', 'target': os.readlink(path)}
            else:
                need(stat.S_ISREG(value.st_mode), 'Unregistered special file: ' + relative)
                raw = path.read_bytes()
                rows[relative] = {'kind': 'regular', 'bytes': len(raw), 'sha256': digest(raw)}
    return rows


def verify(root, external_seal_sha256):
    need(re.fullmatch('[0-9a-f]{64}', external_seal_sha256), 'External exact seal SHA required')
    root = Path(root)
    need(root.is_absolute(), 'Absolute review root required')
    for part in [root, *root.parents]: need(not part.is_symlink(), 'Review root has a symlink ancestor')
    seal_path = root / 'SEAL.json'
    need(stat.S_ISREG(seal_path.lstat().st_mode), 'Regular seal required')
    raw = seal_path.read_bytes(); need(digest(raw) == external_seal_sha256, 'External seal pin differs')
    value = json.loads(raw)
    need(value['version'] == 1 and value['kind'] == 'independent-common-publication-cold-link-review-seal', 'Wrong review seal kind')
    for relative in value['inventory']:
        name = PurePosixPath(relative)
        need(str(name) == relative and not name.is_absolute() and '..' not in name.parts,
             'Noncanonical inventory member')
    actual = inventory(root)
    need(actual == value['inventory'], 'Review byte/namespace inventory differs')
    return {'status': 'verified', 'seal_sha256': external_seal_sha256,
            'regular_files': sum(v['kind'] == 'regular' for v in actual.values()),
            'symlinks': sum(v['kind'] == 'symlink' for v in actual.values()),
            'scope': 'Byte/namespace integrity only; fixture mode/history facts remain in pinned records.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True); parser.add_argument('--seal-sha256', required=True)
    args = parser.parse_args(); print(json.dumps(verify(args.root, args.seal_sha256), sort_keys=True))


if __name__ == '__main__': main()
