"""Resume the retained exact cleanup after a self-induced hardlink-count change.

The first attempt correctly stopped on a copied JDK module shared by 30 names.
Only link-count/ctime changes explained by already removed inventoried aliases
are admitted. Inode, bytes, hash, mode, owner and mtime remain exact throughout.
"""
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'operators/residual-original-cleanup-v1'
OUT = ROOT / 'operators/residual-original-cleanup-v2'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def ident(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks * 512]


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def main():
    need(not OUT.exists(), 'Fresh exact resume receipt required')
    members = OLD / 'EXACT-MEMBERS.json.gz'
    need(sha(members) == 'c8ee30e34645275858dc8592a7e91e9db84edd1deabe465fae488c0b319a491e', 'Original exact cleanup inventory differs')
    failed = json.loads((OLD / 'FAILED.json').read_text())
    need(failed['removed_members'] == 16902 and failed['message'] == 'Original changed before exact unlink', 'Original partial failure differs')
    proof = ROOT / 'operators/residual-originals-v1/COLD-VERIFICATION.json'
    need(sha(proof) == '75eb9d870d227457926d741f08c50bd2ebc2f5014f427c985c029a955ff58007', 'Original verified cold retention differs')
    for ref in json.loads(proof.read_text())['cold_members']:
        need(sha(Path(ref['path'])) == ref['sha256'], 'Retained cold member differs')
    cache = ROOT / 'cache'
    need(cache.stat().st_ino == 26682812 and sha(cache / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55', 'Cache identity differs')
    rows = json.loads(gzip.decompress(members.read_bytes()))
    prior = collections.Counter()
    for row in rows[:16902]:
        need(not os.path.lexists(row['path']), 'Previously removed name reappeared')
        prior[tuple(row['identity'][:2])] += 1
    remaining = rows[16902:]
    def check(row, aliases):
        p = Path(row['path'])
        need(p.is_relative_to(cache) and not any(x.is_symlink() for x in p.parents), 'Unsafe resume boundary')
        old, now = row['identity'], ident(p.lstat())
        key = tuple(old[:2])
        # Metadata changed only by earlier exact unlink operations on this inode.
        need(now[:4] == old[:4] and now[5:7] == old[5:7] and now[8] == old[8], 'Original inode/content metadata changed')
        need(now[4] == old[4] - aliases[key], 'Link count differs from exact own-unlink ledger')
        need(aliases[key] > 0 or now[7] == old[7], 'Unexplained ctime change')
        if row['kind'] == 'regular':
            need(stat.S_ISREG(now[2]) and sha(p) == row['sha256'], 'Original bytes changed')
        elif row['kind'] == 'symlink':
            need(stat.S_ISLNK(now[2]) and os.readlink(p) == row['target'], 'Original structural link changed')
        return now
    current = [{'path': r['path'], 'identity': check(r, prior)} for r in remaining]
    OUT.mkdir()
    with (OUT / 'CURRENT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
            z.write((json.dumps(current, sort_keys=True, separators=(',', ':')) + '\n').encode())
    save('INTENT.json', {'at_unix': time.time(), 'original_removed_members': 16902,
        'remaining_members': len(remaining), 'current_members_sha256': sha(OUT / 'CURRENT-MEMBERS.json.gz'),
        'source_sha256': sha(Path(__file__)), 'basis': 'Exact prior inventory and verified cold retain all originals; admit only own-unlink ledger changes to link count and ctime. Never chmod any regular file or follow links.'})
    removed = 0
    try:
        for row in remaining:
            check(row, prior)
            Path(row['path']).unlink()
            prior[tuple(row['identity'][:2])] += 1
            removed += 1
        save('END.json', {'status': 'verified', 'at_unix': time.time(), 'removed_members_this_resume': removed,
            'total_removed_members_both_attempts': 16902 + removed,
            'total_removed_regular_files_both_attempts': sum(r['kind'] == 'regular' for r in rows),
            'removed_namespace_allocated_file_bytes_both_attempts': sum(r['identity'][8] for r in rows if r['kind'] == 'regular'),
            'removed_namespace_unique_inode_allocated_bytes_both_attempts': sum({tuple(r['identity'][:2]): r['identity'][8] for r in rows if r['kind'] == 'regular'}.values()),
            'file_chmod_calls': 0, 'physical_reclaim_measured': False, 'original_failure_preserved': True,
            'meter_manifest_events_and_shells_retained': True, 'retained_cold_or_user_sdk_modified': False})
        print(json.dumps({'status': 'verified', 'removed_members': 16902 + removed}))
    except BaseException as error:
        save('FAILED.json', {'status': 'failed', 'removed_this_resume': removed, 'type': type(error).__name__, 'message': str(error)})
        raise


if __name__ == '__main__':
    main()
