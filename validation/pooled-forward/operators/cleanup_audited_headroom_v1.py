"""Delete only independently inventoried excluded scratch/closed duplicates.

Fresh ownership, identity, bytes, stock equality and protection checks precede
the durable intent. No selected main-study file or production root is a target.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'operators/regenerable-headroom-independent-v1'
FREEZE_SHA = 'be58b48b5e775fc0f7513fd8c570ae6db798b953c93f7201b404f0533c3ff394'
OUTPUT = ROOT / 'operators/audited-headroom-cleanup-v1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts
         and not any(p.is_symlink() for p in (path, *path.parents)), 'Unsafe original path')
    return path


def sha(path):
    digest = hashlib.sha256()
    with safe(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(reference):
    path = safe(reference['path'])
    need(sha(path) == reference['sha256'], 'Independent input pin differs')
    return json.loads(path.read_text())


def sig(path):
    value = safe(path).lstat()
    return [value.st_dev, value.st_ino, stat.S_IMODE(value.st_mode), value.st_uid,
            value.st_gid, value.st_nlink, value.st_size, value.st_blocks * 512,
            value.st_mtime_ns, value.st_ctime_ns]


def from_entry(value):
    return [value['device'], value['inode'], int(value['mode'], 8), value['uid'],
            value['gid'], value['nlink'], value['size_bytes'], value['allocated_file_bytes'],
            value['mtime_ns'], value['ctime_ns']]


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def main():
    freeze = read({'path': str(REVIEW / 'REVIEW-FREEZE.json'), 'sha256': FREEZE_SHA})
    for row in freeze['artifact_manifest']:
        path = safe(row['path'])
        need(sha(path) == row['sha256'] and path.stat().st_size == row['size_bytes']
             and format(stat.S_IMODE(path.stat().st_mode), '04o') == row['sealed_mode'], 'Review member changed')
    result = read(freeze['result'])
    inventory = read(result['inventory'])
    expanded = read(result['expanded_current_byte_review'])
    protection = read(result['protection'])
    plan = read(inventory['main_plan'])
    read(inventory['main_spec'])
    authority = read(inventory['cache_identity_authority'])
    cache = safe(authority['path'])
    need((cache.stat().st_dev, cache.stat().st_ino) == (authority['device'], authority['inode'])
         and sha(cache / 'OWNER.json') == authority['marker_sha256'], 'Positive cache ownership changed')
    protected_paths = {row[0] for row in protection['rows']}
    protected_inodes = set()
    for raw in protected_paths:
        path = safe(raw)
        if path.is_file():
            st = path.stat()
            protected_inodes.add((st.st_dev, st.st_ino))
    protected_roots = [Path(p) for p in plan['source_roots'] + plan['protected_plain_code_roots']]
    files, directories = {}, {}

    def add_file(raw, expected, category, expected_sha=None, stock=None):
        path = safe(raw)
        need(stat.S_ISREG(path.lstat().st_mode) and sig(path) == expected and expected[5] == 1,
             'Candidate file identity/type/link count changed')
        need(raw not in protected_paths and (expected[0], expected[1]) not in protected_inodes
             and not any(path == p or path.is_relative_to(p) for p in protected_roots), 'Protected path or inode intersects cleanup')
        actual = sha(path)
        need(expected_sha is None or actual == expected_sha, 'Candidate bytes changed')
        if stock is not None:
            need(sig(Path(stock[0])) == stock[1] and sha(Path(stock[0])) == actual, 'Retained stock proof changed')
        need(raw not in files, 'Overlapping deletion candidates')
        files[raw] = {'identity': expected, 'sha256': actual, 'category': category}

    for target in inventory['targets']:
        need(not target['blockers'] and target['root_identity_unchanged'], 'Blocked cache target')
        entries = read(target['inventory'])['entries']
        root = safe(target['path'])
        need(root.is_relative_to(cache), 'Scratch outside owned cache')
        need(not any(Path(p) == root or Path(p).is_relative_to(root) for p in protected_paths)
             and not any(root == p or root.is_relative_to(p) or p.is_relative_to(root) for p in protected_roots),
             'Cache directory overlaps a protected original/root')
        observed = {str(root)}
        for base, dirs, names in os.walk(root, followlinks=False):
            for name in dirs + names:
                observed.add(str(Path(base) / name))
        need(observed == {row['path'] for row in entries}, 'Cache member set changed')
        for row in entries:
            expected = from_entry(row)
            need(sig(Path(row['path'])) == expected, 'Cache member identity changed')
            if row['kind'] == 'regular':
                add_file(row['path'], expected, target['kind'])
            elif row['kind'] == 'directory':
                directories[row['path']] = expected
            else:
                raise ValueError('Nonregular cache candidate refused')
    pristine = read(expanded['workspace_pristine'])
    for row in pristine['rows']:
        add_file(row[0], row[2], 'current-stock-equal-excluded-checkout', row[1], (row[3], row[5]))
    for row in expanded['qualification_archive_candidates']:
        add_file(row['path'], row['identity'], 'already-cold-qualification-container', row['current_sha256'])
    need(sum(row['identity'][7] for row in files.values()) == 3471007744, 'Exact reviewed allocation differs')
    for raw_path in files:
        parent = Path(raw_path).parent
        need(str(parent) in directories or bool(parent.stat().st_mode & stat.S_IWUSR),
             'Unowned/read-only parent permission change would be required')
    need(not OUTPUT.exists(), 'Fresh cleanup receipt namespace required')
    OUTPUT.mkdir()
    raw = (json.dumps({'files': files, 'directories': directories}, sort_keys=True, separators=(',', ':')) + '\n').encode()
    with (OUTPUT / 'FRESH-MEMBERS.json.gz').open('xb') as out:
        with gzip.GzipFile(filename='', fileobj=out, mode='wb', mtime=0) as stream:
            stream.write(raw)
        out.flush()
        os.fsync(out.fileno())
    save(OUTPUT / 'INTENT.json', {'version': 1, 'kind': 'positive-excluded-headroom-cleanup-intent',
        'at_unix': time.time(), 'source_sha256': sha(Path(__file__)), 'independent_freeze_sha256': FREEZE_SHA,
        'fresh_members_sha256': sha(OUTPUT / 'FRESH-MEMBERS.json.gz'), 'files': len(files),
        'allocated_file_bytes': 3471007744, 'all_main_protected_path_or_inode_intersections': 0,
        'scope': 'Excluded regenerable SDK caches/current-stock-equal non-production checkout files plus9 already byte-preserved qualification containers. Original current production, commands, sources, logs and xcresult remain.'})
    removed = 0
    try:
        for raw_path, expected in sorted(directories.items(), key=lambda pair: len(Path(pair[0]).parts)):
            path = Path(raw_path)
            need(sig(path)[:5] == expected[:5], 'Owned cache directory changed before write permission')
            path.chmod(expected[2] | 0o700)
        for raw_path, row in files.items():
            path = Path(raw_path)
            need(sig(path) == row['identity'] and sha(path) == row['sha256'], 'Candidate changed before exact unlink')
            need(path.parent.stat().st_mode & stat.S_IWUSR, 'Candidate parent is readonly; refuse broad permission repair')
            path.unlink()
            removed += 1
        for raw_path, expected in sorted(directories.items(), key=lambda pair: len(Path(pair[0]).parts), reverse=True):
            path = Path(raw_path)
            need((path.stat().st_dev, path.stat().st_ino) == (expected[0], expected[1]), 'Owned empty cache directory replaced')
            path.rmdir()
        need(all(Path(p).exists() for p in protected_paths), 'Protected original became absent')
        save(OUTPUT / 'END.json', {'version': 1, 'status': 'verified', 'at_unix': time.time(),
            'removed_regular_files': removed, 'removed_directory_count': len(directories),
            'removed_allocated_file_bytes': 3471007744, 'main_selected_files_deleted': 0,
            'live_sdk_or_original_product_modified': False,
            'scope': 'Allocated-file accounting only; no exact APFS physical-free claim. Benchmarks, symlinks, unknown/mismatched stock, all loose qualification code/reports and primary main-study evidence remain.'})
        print(json.dumps({'status': 'verified', 'removed_files': removed, 'allocated_file_bytes': 3471007744}))
    except BaseException as error:
        save(OUTPUT / 'FAILED.json', {'status': 'failed', 'at_unix': time.time(), 'removed_files': removed,
                                     'type': type(error).__name__, 'message': str(error), 'partial_cleanup_retained': True})
        raise


if __name__ == '__main__':
    main()
