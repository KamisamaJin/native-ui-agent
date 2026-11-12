"""Close only original empty scratch shells after retained v2 interruption.

Outside boundary parents get temporary held-dirfd write permission for rmdir
of an exact owned child; original modes are restored immediately. No regular
file, unknown child, source byte or external symlink target is deleted here.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'operators/terminal-scratch-cleanup-v1'
OUT = ROOT / 'operators/terminal-scratch-cleanup-v3'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    assert not OUT.exists()
    intent = json.loads((OLD / 'INTENT.json').read_text())
    members = OLD / 'EXACT-MEMBERS.json.gz'
    assert sha(members) == intent['members_sha256']
    exact = json.loads(gzip.decompress(members.read_bytes()))
    assert all(not os.path.lexists(r['path']) for r in exact['members'])
    v2 = json.loads((ROOT / 'operators/terminal-scratch-cleanup-v2/FAILED.json').read_text())
    assert v2['removed_this_resume'] + 551 == len(exact['members']) and v2['type'] == 'PermissionError'
    OUT.mkdir()
    removed = 0
    permission_changes = []
    remaining = []
    for raw, old in sorted(exact['directories'].items(), key=lambda item: -item[0].count('/')):
        p = Path(raw)
        if p == ROOT / 'cache' or not p.exists():
            continue
        assert p.is_relative_to(ROOT) and not any(q.is_symlink() for q in [p, *p.parents])
        s = p.lstat()
        assert [s.st_dev, s.st_ino] == old[:2] and s.st_uid == os.geteuid() and stat.S_ISDIR(s.st_mode)
        assert not list(p.iterdir()), 'Unknown/nonempty shell refuses rmdir: ' + str(p)
        remaining.append({'path': raw, 'device': s.st_dev, 'inode': s.st_ino})
    (OUT / 'INTENT.json').write_text(json.dumps({'at_unix': time.time(), 'source_sha256': sha(Path(__file__)),
        'original_inventory_sha256': intent['members_sha256'], 'all_original_file_names_absent': len(exact['members']),
        'remaining_exact_empty_shells': remaining, 'scope': 'Exact empty directories only; parent permission restored after each held-fd rmdir. Original two interrupted attempts retained.'}, indent=2, sort_keys=True) + '\n')
    # Parent shells are processed after their children; fresh emptiness is
    # required immediately before every operation as well.
    for row in remaining:
        p = Path(row['path'])
        fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        original = stat.S_IMODE(os.fstat(fd).st_mode)
        changed = False
        try:
            assert os.fstat(fd).st_uid == os.geteuid()
            current = os.stat(p.name, dir_fd=fd, follow_symlinks=False)
            assert (current.st_dev, current.st_ino) == (row['device'], row['inode']) and stat.S_ISDIR(current.st_mode)
            if not original & stat.S_IWUSR:
                os.fchmod(fd, original | 0o700)
                changed = True
            os.rmdir(p.name, dir_fd=fd)
            removed += 1
        finally:
            if changed:
                os.fchmod(fd, original)
                assert stat.S_IMODE(os.fstat(fd).st_mode) == original
                permission_changes.append({'parent': str(p.parent), 'restored_mode': original})
            os.close(fd)
    for ref in intent['retained_cold_inputs']:
        assert sha(Path(ref['path'])) == ref['sha256']
    assert set(p.name for p in (ROOT / 'cache').iterdir()) == {'OWNER.json'}
    result = {'status': 'verified', 'at_unix': time.time(), 'all_original_members_removed': len(exact['members']),
        'regular_files_removed': sum(r['kind'] == 'regular' for r in exact['members']),
        'original_inventory_allocated_file_bytes_of_removed_names': sum(r['identity'][9] for r in exact['members'] if r['kind'] == 'regular'),
        'exact_directories_removed_all_attempts': len(exact['directories']) - 1,
        'empty_shells_removed_this_attempt': removed, 'temporary_parent_modes_restored': permission_changes,
        'file_chmod_calls': 0, 'physical_reclaim_measured': False, 'original_failure_records_preserved': True,
        'cache_contains_owner_marker_only': True, 'retained_cold_inputs_reverified': len(intent['retained_cold_inputs'])}
    (OUT / 'END.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'verified', 'all_original_members_removed': len(exact['members']), 'empty_shells_removed': removed}))


if __name__ == '__main__':
    main()
