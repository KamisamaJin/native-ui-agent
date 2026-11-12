"""Remove exactly inventoried, archived residual originals in six owned roots.

Also disposes explicitly declared regenerable SDK/Git/DerivedData exclusions.
The active meter's controller manifest/events and directory shells remain.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'operators/residual-originals-v1'
CACHE = ROOT / 'cache'
OUT = ROOT / 'operators/residual-original-cleanup-v1'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def ident(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks * 512]


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification-sha256', required=True)
    args = parser.parse_args()
    proof_path = INVENTORY / 'COLD-VERIFICATION.json'
    need(sha(proof_path) == args.verification_sha256, 'External verification pin differs')
    proof = json.loads(proof_path.read_text())
    need(proof['status'] == 'verified' and proof['files'] == 29324
         and proof['index_sha256'] == 'ee6ae7ae820c3f76987c787db8790403b39a587e00530dd757c514ebfa601c8d', 'Original-data byte verification missing')
    need(sha(INVENTORY / 'SPEC.json') == proof['spec_sha256'], 'Supplement selection changed')
    for ref in proof['cold_members']:
        need(sha(Path(ref['path'])) == ref['sha256'], 'Retained cold member changed')
    need(not OUT.exists(), 'Fresh cleanup receipt required')
    need((CACHE.stat().st_dev, CACHE.stat().st_ino) == (16777232, 26682812)
         and sha(CACHE / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55', 'Owned cache differs')
    closure = ROOT / 'operators/final-owned-resource-closure-v1/CLOSURE.json'
    need(sha(closure) == 'd1cf78942d7fde653068bd6c6f8c759a77c994633efb55dcfdd1389026bb46c5'
         and not json.loads(closure.read_text())['pending'], 'Original resource closure missing')
    spec = json.loads((INVENTORY / 'SPEC.json').read_text())
    selected = {r['path']: r for r in spec['files']}
    exclusions = json.loads((INVENTORY / 'EXCLUSIONS.json').read_text())['entries']
    excluded_roots = [Path(r['path']) for r in exclusions if 'sha256' not in r]
    excluded_files = {r['path']: r for r in exclusions if 'sha256' in r}
    structures = {r['path']: r for r in json.loads((INVENTORY / 'STRUCTURE.json').read_text())['entries']}
    keep = CACHE / 'business/run-cohort2'
    rows = []
    for boundary in spec['roots']:
        root = Path(boundary['path'])
        need(root.is_relative_to(CACHE) and not root.is_symlink(), 'Unsafe owned original boundary')
        for directory, dirs, files in os.walk(root, followlinks=False):
            for name in dirs + files:
                path = Path(directory) / name
                st = path.lstat()
                if stat.S_ISDIR(st.st_mode):
                    continue
                key = str(path)
                regenerable = any(path.is_relative_to(p) for p in excluded_roots) or key in excluded_files
                if stat.S_ISREG(st.st_mode):
                    digest = sha(path)
                    if key in selected:
                        need(st.st_size == selected[key]['bytes'] and digest == selected[key]['sha256'], 'Archived original changed')
                    elif key in excluded_files:
                        need(digest == excluded_files[key]['sha256'], 'Excluded SDK copy changed')
                    else:
                        need(regenerable, 'Unpreserved original refuses cleanup: ' + key)
                    row = {'path': key, 'identity': ident(st), 'sha256': digest, 'kind': 'regular', 'regenerable': regenerable}
                elif stat.S_ISLNK(st.st_mode):
                    need(regenerable or (key in structures and structures[key]['kind'] == 'symlink'
                         and os.readlink(path) == structures[key]['target']), 'Unknown structural link refuses cleanup')
                    row = {'path': key, 'identity': ident(st), 'target': os.readlink(path), 'kind': 'symlink', 'regenerable': regenerable}
                else:
                    need(key in structures or regenerable, 'Unknown special file')
                    row = {'path': key, 'identity': ident(st), 'kind': 'special', 'regenerable': regenerable}
                if path == keep / 'manifest.json' or path.is_relative_to(keep / 'events'):
                    continue
                need(st.st_uid == os.geteuid() and st.st_dev == 16777232, 'Unowned cleanup member')
                rows.append(row)
    OUT.mkdir()
    with (OUT / 'EXACT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
            z.write((json.dumps(rows, separators=(',', ':'), sort_keys=True) + '\n').encode())
    save('INTENT.json', {'at_unix': time.time(), 'verification_sha256': args.verification_sha256,
        'members_sha256': sha(OUT / 'EXACT-MEMBERS.json.gz'), 'source_sha256': sha(Path(__file__)),
        'count': len(rows), 'kept_meter_controller': str(keep), 'directory_shells_retained': True,
        'scope': 'Only inventoried original bytes backed by the verified supplement, plus explicit regenerable exclusions in owned cache. No cold/publication/project/SDK/user device targets.'})
    removed = 0
    try:
        parents = {Path(r['path']).parent for r in rows}
        for parent in parents:
            need(not any(p.is_symlink() for p in [parent, *parent.parents]), 'Unsafe cleanup parent')
            fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                st = os.fstat(fd)
                need(st.st_uid == os.geteuid(), 'Unowned parent')
                if not st.st_mode & stat.S_IWUSR:
                    os.fchmod(fd, stat.S_IMODE(st.st_mode) | 0o700)
            finally:
                os.close(fd)
        for row in rows:
            path = Path(row['path'])
            need(ident(path.lstat()) == row['identity'], 'Original changed before exact unlink')
            if row['kind'] == 'regular':
                need(sha(path) == row['sha256'], 'Original bytes changed before unlink')
            elif row['kind'] == 'symlink':
                need(os.readlink(path) == row['target'], 'Structural link changed')
            path.unlink()
            removed += 1
        save('END.json', {'status': 'verified', 'at_unix': time.time(), 'removed_members': removed,
            'removed_regular_files': sum(r['kind'] == 'regular' for r in rows),
            'removed_namespace_allocated_file_bytes': sum(r['identity'][8] for r in rows if r['kind'] == 'regular'),
            'physical_reclaim_measured': False, 'file_chmod_calls': 0,
            'meter_manifest_events_and_shells_retained': True, 'project_sdk_and_cold_bytes_modified': False})
        print(json.dumps({'status': 'verified', 'removed_members': removed}))
    except BaseException as error:
        save('FAILED.json', {'status': 'failed', 'removed_members': removed, 'type': type(error).__name__,
            'message': str(error), 'partial_outputs_retained': True})
        raise


if __name__ == '__main__':
    main()
