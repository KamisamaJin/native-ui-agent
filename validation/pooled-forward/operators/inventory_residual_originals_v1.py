"""Inventory surviving original cache records without following links.

This is a storage supplement, not a new product evaluation or source authority.
The main selected originals have already passed the complete readonly replay.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'cache'
OUTPUT = ROOT / 'operators/residual-originals-v1'
ROOTS = ['benchmark', 'qualification', 'business', 'business-rejected-cohort1', 'hosts', 'supervision']
DERIVED = {
    'business-rejected-cohort1/initial/T1/compile-attempt-1/ios/DerivedData',
    'business-rejected-cohort1/initial/T2/compile-attempt-1/ios/DerivedData',
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(st):
    return {'dev': st.st_dev, 'ino': st.st_ino, 'uid': st.st_uid,
            'mode': stat.S_IMODE(st.st_mode), 'bytes': st.st_size,
            'mtime_ns': st.st_mtime_ns, 'ctime_ns': st.st_ctime_ns,
            'nlink': st.st_nlink, 'allocated': st.st_blocks * 512}


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')
    path.chmod(0o444)


def main():
    need(not OUTPUT.exists(), 'Fresh supplement inventory required')
    need(not CACHE.is_symlink() and (CACHE.stat().st_dev, CACHE.stat().st_ino) == (16777232, 26682812),
         'Owned cache root differs')
    need(sha(CACHE / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55',
         'Cache owner differs')
    sdk = CACHE / 'hosts/reply/Reply/.native-ui/java-desktop.jar'
    sdk_sha = sha(sdk)
    rows, exact, structures, excluded = [], [], [], []
    for root_id in ROOTS:
        root = CACHE / root_id
        need(root.is_dir() and not root.is_symlink(), 'Original cache boundary differs')
        for directory, dirs, files in os.walk(root, followlinks=False):
            parent = Path(directory)
            for name in sorted(dirs + files):
                path = parent / name
                rel = path.relative_to(CACHE).as_posix()
                st = path.lstat()
                info = {'path': str(path), 'identity': identity(st)}
                if stat.S_ISLNK(st.st_mode):
                    info.update(kind='symlink', target=os.readlink(path))
                    structures.append(info)
                    if name in dirs:
                        dirs.remove(name)
                    continue
                if stat.S_ISDIR(st.st_mode):
                    if name == '.git' or rel in DERIVED:
                        info.update(reason='regenerable Git object database' if name == '.git' else 'regenerable Apple DerivedData; commands/logs/status/xcresult outside this root retained')
                        excluded.append(info)
                        dirs.remove(name)
                    else:
                        structures.append(dict(info, kind='directory'))
                    continue
                if not stat.S_ISREG(st.st_mode):
                    structures.append(dict(info, kind='special', file_type=stat.S_IFMT(st.st_mode)))
                    continue
                digest = sha(path)
                need(identity(path.lstat()) == info['identity'], 'Original changed during inventory')
                if path.name == 'java-desktop.jar' and path.parent.name == '.native-ui':
                    need(st.st_size == sdk.stat().st_size and digest == sdk_sha, 'Unknown SDK copy retained for diagnosis')
                    excluded.append(dict(info, reason='exact host JDK module copy; shared SDK and source commands retained', sha256=digest))
                    continue
                rows.append({'root': root_id, 'path': str(path), 'logical_path': 'originals/' + rel,
                             'sha256': digest, 'bytes': st.st_size, 'mode': format(stat.S_IMODE(st.st_mode), '04o')})
                exact.append(dict(info, sha256=digest))
    OUTPUT.mkdir()
    spec = {'version': 1, 'roots': [{'id': k, 'kind': 'evidence', 'path': str(CACHE / k)} for k in ROOTS], 'files': rows}
    save(OUTPUT / 'SPEC.json', spec)
    save(OUTPUT / 'STRUCTURE.json', {'version': 1, 'entries': structures, 'symlink_policy': 'Inert metadata only; no targets followed or materialized'})
    save(OUTPUT / 'EXCLUSIONS.json', {'version': 1, 'entries': excluded, 'scope': 'Only listed generated SDK/Git/DerivedData objects excluded; no original evidence filename exclusions'})
    with (OUTPUT / 'EXACT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
            z.write((json.dumps(exact, sort_keys=True, separators=(',', ':')) + '\n').encode())
    save(OUTPUT / 'INVENTORY.json', {'version': 1, 'at_unix': time.time(), 'kind': 'surviving-original-data-supplement',
        'files': len(rows), 'source_bytes': sum(r['bytes'] for r in rows), 'structures': len(structures),
        'excluded_roots_or_sdk_copies': len(excluded), 'source_sha256': sha(Path(__file__)),
        'pins': {p.name: sha(p) for p in OUTPUT.iterdir() if p.is_file()},
        'scope': 'Retain surviving benchmark, qualification, rejected-cohort, business, host and supervision originals. Original absolute keys and bytes are unchanged. This supplements the main archive and does not rerun or alter any original judgment.'})
    print(json.dumps({'status': 'inventoried', 'files': len(rows), 'bytes': sum(r['bytes'] for r in rows)}))


if __name__ == '__main__':
    main()
