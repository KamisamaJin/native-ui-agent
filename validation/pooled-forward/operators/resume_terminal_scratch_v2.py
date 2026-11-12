"""Resume the exact terminal cleanup after APFS allocation-only drift.

Original intent and first failure remain; no target discovery or expansion.
"""
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time
from cleanup_identity_v1 import unchanged

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'operators/terminal-scratch-cleanup-v1'
OUT = ROOT / 'operators/terminal-scratch-cleanup-v2'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def ident(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid,
            st.st_nlink, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks * 512]


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def main():
    need(not OUT.exists(), 'Fresh terminal resume receipt required')
    intent = json.loads((OLD / 'INTENT.json').read_text())
    members = OLD / 'EXACT-MEMBERS.json.gz'
    need(sha(members) == intent['members_sha256'], 'Original exact members differ')
    failed = json.loads((OLD / 'FAILED.json').read_text())
    need(failed['removed_members'] == 551 and failed['message'] == 'Unexplained scratch member replacement/change', 'Original interruption differs')
    cache = ROOT / 'cache'
    need(cache.stat().st_ino == 26682812 and sha(cache / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55', 'Owned cache differs')
    for ref in intent['retained_cold_inputs']:
        need(sha(Path(ref['path'])) == ref['sha256'], 'Retained cold bytes differ')
    exact = json.loads(gzip.decompress(members.read_bytes()))
    rows = exact['members']
    aliases = collections.Counter()
    for row in rows[:551]:
        need(not os.path.lexists(row['path']), 'Removed member reappeared')
        aliases[tuple(row['identity'][:2])] += 1
    remaining = rows[551:]
    def check(row):
        p = Path(row['path'])
        need(p.is_relative_to(ROOT) and not p.is_relative_to(ROOT / 'publications')
             and not any(parent.is_symlink() for parent in p.parents), 'Unsafe exact member')
        now = ident(p.lstat())
        need(unchanged(row['identity'], now, aliases[tuple(row['identity'][:2])]), 'Content/namespace identity changed')
        if row['kind'] == 'regular':
            need(sha(p) == row['sha256'], 'Original exact bytes differ')
        elif row['kind'] == 'symlink':
            need(os.readlink(p) == row['target'], 'Inert structural link changed')
        return now
    current = [{'path': row['path'], 'identity': check(row), 'original_allocated_bytes': row['identity'][9]} for row in remaining]
    OUT.mkdir()
    with (OUT / 'CURRENT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
            z.write((json.dumps(current, sort_keys=True, separators=(',', ':')) + '\n').encode())
    save('INTENT.json', {'at_unix': time.time(), 'source_sha256': sha(Path(__file__)),
        'original_intent_sha256': sha(OLD / 'INTENT.json'), 'current_inventory_sha256': sha(OUT / 'CURRENT-MEMBERS.json.gz'),
        'remaining_members': len(remaining), 'selection_expanded': False,
        'allocation_only_changed_members': sum(r['identity'][9] != r['original_allocated_bytes'] for r in current),
        'basis': 'APFS allocated blocks are observations, not content identity. All original exact dev/inode/mode/uid/gid/size/mtime/bytes/hash still required; nlink/ctime only admit exact own-unlink ledger. No file chmod or new selection.'})
    removed = 0
    try:
        for row in remaining:
            check(row)
            p = Path(row['path'])
            fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                need(ident(os.fstat(fd))[:2] == exact['file_parents'][str(p.parent)][:2], 'Exact parent replaced')
                os.unlink(p.name, dir_fd=fd)
            finally:
                os.close(fd)
            aliases[tuple(row['identity'][:2])] += 1
            removed += 1
        for path, old in sorted(exact['directories'].items(), key=lambda item: -item[0].count('/')):
            p = Path(path)
            if p == cache:
                continue
            need(ident(p.lstat())[:2] == old[:2], 'Empty directory replaced')
            p.rmdir()
        for ref in intent['retained_cold_inputs']:
            need(sha(Path(ref['path'])) == ref['sha256'], 'Retained cold bytes changed')
        need(set(p.name for p in cache.iterdir()) == {'OWNER.json'}, 'Unexplained cache residue')
        save('END.json', {'status': 'verified', 'at_unix': time.time(), 'removed_members_this_resume': removed,
            'total_removed_members_both_attempts': removed + 551, 'removed_directories': len(exact['directories']) - 1,
            'total_removed_regular_files_both_attempts': sum(r['kind'] == 'regular' for r in rows),
            'original_inventory_allocated_file_bytes_of_removed_names': sum(r['identity'][9] for r in rows if r['kind'] == 'regular'),
            'fresh_resume_allocated_file_bytes_of_remaining_names': sum(r['identity'][9] for r in current),
            'physical_reclaim_measured': False, 'file_chmod_calls': 0, 'original_failure_preserved': True,
            'retained_cold_inputs_reverified': len(intent['retained_cold_inputs']), 'cache_contains_owner_marker_only': True})
        print(json.dumps({'status': 'verified', 'removed_members_both_attempts': removed + 551}))
    except BaseException as error:
        save('FAILED.json', {'status': 'failed', 'removed_this_resume': removed, 'type': type(error).__name__, 'message': str(error)})
        raise


if __name__ == '__main__':
    main()
