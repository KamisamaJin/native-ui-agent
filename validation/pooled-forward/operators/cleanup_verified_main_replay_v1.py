"""Dispose one local verified readonly main replay, preserving its map/receipts.

Local ownership and exact complete membership are required. Cold transport
members (possibly hardlinked to decoded raw shards) are never chmod'ed/deleted.
"""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'cache/publication-archives/business-precleanup-replay-v1'
BASE = REPLAY / 'business-main/readonly-restore'
OUT = ROOT / 'operators/verified-main-replay-cleanup-v1'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ident(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks * 512]


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def main():
    need(not OUT.exists(), 'Fresh cleanup receipt required')
    need(sha(REPLAY / 'RESULT.json') == '9c15c2d0d67334d6394fd903d0d576a687aea416d10edad2160dea678c8bb75a', 'Actual complete replay result differs')
    need(json.loads((REPLAY / 'RESULT.json').read_text())['status'] == 'verified', 'Unverified replay')
    need((ROOT / 'cache').stat().st_ino == 26682812 and sha(ROOT / 'cache/OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55', 'Owned cache differs')
    source = ROOT / 'publication-map-session/session.py'
    need(sha(source) == '9502fc59697f039021a4a2c9f5046ea2f46d32a235613ceb2c719709573c425c', 'Frozen session code differs')
    spec = importlib.util.spec_from_file_location('local_replay_cleanup_session', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    map_path = BASE / 'RESTORED-MAP.json'
    map_sha = sha(map_path)
    reader = module.MapSessionReader(map_path, map_sha256=map_sha,
        index_sha256='a1e7070ae61999f65cf506c2fe33e6837ea7fc4b073ef01dca9c00603ea379e5')
    need(reader.verify_all() == 104062 and reader.namespace == BASE / 'files', 'Full readonly main payload differs')
    expected = {row['physical_path'] for row in reader._rows.values()}
    target = BASE / 'files'
    rows, seen = [], set()
    for directory, dirs, files in os.walk(target, followlinks=False):
        for path in [Path(directory)] + [Path(directory) / n for n in files]:
            st = path.lstat()
            need(st.st_uid == os.geteuid() and st.st_dev == 16777232, 'Unowned replay member')
            if stat.S_ISREG(st.st_mode):
                need(str(path) in expected and st.st_nlink == 1 and not st.st_mode & 0o222, 'Unexpected/writable/aliased logical payload')
                seen.add(str(path))
            else:
                need(stat.S_ISDIR(st.st_mode), 'Unsafe replay namespace')
            rows.append({'path': str(path), 'identity': ident(st), 'directory': stat.S_ISDIR(st.st_mode)})
        need(all(not (Path(directory) / n).is_symlink() for n in dirs), 'Symlink in replay')
    need(seen == expected, 'Exact complete readonly payload membership differs')
    reader.close()
    OUT.mkdir()
    with (OUT / 'EXACT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
            z.write((json.dumps(rows, sort_keys=True, separators=(',', ':')) + '\n').encode())
    save('INTENT.json', {'at_unix': time.time(), 'map_sha256': map_sha, 'target': str(target),
        'files_verified': len(seen), 'members_sha256': sha(OUT / 'EXACT-MEMBERS.json.gz'),
        'source_sha256': sha(Path(__file__)), 'scope': 'Only this verified independent readonly payload; map, proof, decoded/cold transport bytes and original absolute keys retained'})
    removed = 0
    try:
        for row in rows:
            if not row['directory']:
                continue
            fd = os.open(row['path'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                need(ident(os.fstat(fd))[:5] == row['identity'][:5], 'Replay directory changed')
                os.fchmod(fd, stat.S_IMODE(os.fstat(fd).st_mode) | 0o700)
            finally:
                os.close(fd)
        for row in sorted(rows, key=lambda r: (-r['path'].count('/'), r['path'])):
            path = Path(row['path'])
            if row['directory']:
                need(ident(path.lstat())[:2] == row['identity'][:2], 'Replay directory replaced')
                path.rmdir()
            else:
                need(ident(path.lstat()) == row['identity'], 'Readonly payload changed before unlink')
                path.unlink()
                removed += 1
        need(sha(map_path) == map_sha, 'Preserved map changed')
        save('END.json', {'status': 'verified', 'at_unix': time.time(), 'removed_regular_files': removed,
            'removed_namespace_allocated_file_bytes': sum(r['identity'][8] for r in rows if not r['directory']),
            'file_chmod_calls': 0, 'physical_reclaim_measured': False,
            'original_dataset_and_cold_transport_deleted': False, 'map_and_replay_receipts_retained': True})
        print(json.dumps({'status': 'verified', 'removed': removed}))
    except BaseException as error:
        save('FAILED.json', {'status': 'failed', 'removed_regular_files': removed,
            'type': type(error).__name__, 'message': str(error), 'partial_outputs_retained': True})
        raise


if __name__ == '__main__':
    main()
