"""Clean the exact 48 closed synthetic roots after lossless preservation.

The original fixture inventory supplies device/inode, hashes and inert special
entry metadata. Every current member must match before any root is removed.
Business evidence, source, cold publications, SDKs and meters are not targets.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'operators/closed-fixture-cleanup-v1'
PINS = {
    'operators/archive-selection/closed-synthetic-host-v1/ENTRY.json': '2fe55bb6528d9e0584533d946532636ebe90d4b532b16f6f782b821998e2c7ec',
    'cache/publication-archives/closed-synthetic-host-v1/metadata/FIXTURE-METADATA.json': 'bbe9a16c349aa9c56e08e8cc49c1b90f435bc5b24092733db74450eff9090eb5',
    'publications/closed-synthetic-host-v1/TRANSPORT.json': 'a6641b4e42d8ea542db0cafa91d5677c7b344ad6de79b10ff512fdf7e1bc9a21',
    'operators/cold-revalidation-v1/END.json': 'fefef4b2fb333a4a9a0c81c8e75f43bd45335922e9789a64ce10f6d84f2aa214',
    'publication-actual-preservation-review/preserve.py': '4a1e18ebb43d1cddf82a02f69666d2ec9b898204c131469905b6a96646657a83',
    'publication-actual-preservation-review/HOST/FINAL-PLAN.json': '50ea2874d6afb65e80ccf6927f2b930243444d7be0b9c704431945283a45d9e8',
}


def file_sha(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode), str(path)
        h = hashlib.sha256()
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            h.update(block)
        after = os.fstat(fd)
        assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        return h.hexdigest()
    finally:
        os.close(fd)


def ref(path):
    return {'path': str(path), 'sha256': file_sha(path)}


def save(name, value):
    p = OUT / name
    with p.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')
    p.chmod(0o444)
    return ref(p)


def main():
    assert shutil.rmtree.avoids_symlink_attacks
    OUT.mkdir(exist_ok=False)
    started = time.clock_gettime(time.CLOCK_MONOTONIC)
    pins = {}
    for relative, expected in PINS.items():
        pins[relative] = ref(ROOT / relative)
        assert pins[relative]['sha256'] == expected, relative
    save('START.json', {'version': 1, 'started_at_unix': time.time(),
        'started_at_clock_gettime': started, 'shared_clock_basis': 'clock_gettime(CLOCK_MONOTONIC)', 'pins': pins})
    entry = json.loads((ROOT / 'operators/archive-selection/closed-synthetic-host-v1/ENTRY.json').read_text())
    metadata = json.loads((ROOT / 'cache/publication-archives/closed-synthetic-host-v1/metadata/FIXTURE-METADATA.json').read_text())
    roots = [Path(p) for p in entry['selection']]
    assert len(roots) == len(set(roots)) == 48
    spec = importlib.util.spec_from_file_location('closed_fixture_preservation', ROOT / 'publication-actual-preservation-review/preserve.py')
    preservation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preservation)
    plan = json.loads((ROOT / 'publication-actual-preservation-review/HOST/FINAL-PLAN.json').read_text())
    preservation.validate_plan(plan)
    assert set(map(str, roots)) == set(plan['already_cold_roots'])
    required, _ = preservation.immutable_requirements(plan)
    for root in roots:
        assert root.is_relative_to(ROOT) and root.parent.name == 'HOST' and '..' not in root.parts
        preservation.cleanup_scope_check(plan, root, meters_closed=False)
        assert not any(Path(p) == root or root in Path(p).parents for p in required)
        for parent in [root.parent, root]:
            assert stat.S_ISDIR(parent.lstat().st_mode)
    transport_path = ROOT / 'publications/closed-synthetic-host-v1/TRANSPORT.json'
    transport = json.loads(transport_path.read_text())
    for member in transport['files'].values():
        p = transport_path.parent / member['stored']
        assert p.stat().st_size == member['stored_bytes'] and file_sha(p) == member['stored_sha256']
    assert json.loads((ROOT / 'operators/cold-revalidation-v1/END.json').read_text())['status'] == 'verified'
    expected_dirs = {m['path']: m for m in metadata['directories']}
    expected_files = {m['original']: m for m in metadata['files']}
    expected_special = {m['path']: m for m in metadata['symlink_or_special_metadata_only']}
    assert len(expected_files) == len(metadata['files']) == 375470
    assert len(expected_dirs) == len(metadata['directories']) == 147396
    seen_dirs, seen_files, seen_special = set(), set(), set()
    logical = allocated = 0
    for root in roots:
        stack = [root]
        while stack:
            p = stack.pop()
            s = p.lstat()
            key = str(p)
            if stat.S_ISDIR(s.st_mode):
                m = expected_dirs[key]
                assert [s.st_dev, s.st_ino] == [m['device'], m['inode']], key
                assert format(stat.S_IMODE(s.st_mode), '04o') == m['mode'], key
                seen_dirs.add(key)
                stack.extend(Path(e.path) for e in os.scandir(p))
            elif stat.S_ISREG(s.st_mode):
                m = expected_files[key]
                assert '..' not in p.parts and p.is_relative_to(root)
                assert [s.st_dev, s.st_ino, s.st_size] == [m['device'], m['inode'], m['bytes']], key
                assert format(stat.S_IMODE(s.st_mode), '04o') == m['mode'] and file_sha(p) == m['sha256'], key
                seen_files.add(key)
                logical += s.st_size
                allocated += s.st_blocks * 512
            else:
                m = expected_special[key]
                assert m['kind'] == 'symlink' and stat.S_ISLNK(s.st_mode), key
                assert os.readlink(p) == m['target'] and format(stat.S_IMODE(s.st_mode), '04o') == m['mode'], key
                seen_special.add(key)
    assert seen_dirs == set(expected_dirs) and seen_files == set(expected_files) and seen_special == set(expected_special)
    root_ids = {str(p): [p.lstat().st_dev, p.lstat().st_ino] for p in roots}
    intent = save('INTENT.json', {'version': 1, 'kind': 'closed-synthetic-48-exact-root-cleanup-intent',
        'at_unix': time.time(), 'pins': pins, 'root_identities': root_ids,
        'all_current_members_match_original_inventory': True,
        'regular_files_verified': len(seen_files), 'directories_verified': len(seen_dirs),
        'inert_special_entries_verified': len(seen_special), 'required_refs_checked': len(required),
        'required_ref_intersections': 0, 'logical_bytes': logical, 'recorded_allocated_file_bytes': allocated,
        'archive_scope': 'All regular original bytes retained through fixed cold transport; special targets remain inert metadata. This does not claim a full synthetic tree extraction or product replay.'})
    for i, p in enumerate(roots):
        assert [p.lstat().st_dev, p.lstat().st_ino] == root_ids[str(p)]
        shutil.rmtree(p)
        save('REMOVED-%02d.json' % (i + 1), {'path': str(p), 'identity': root_ids[str(p)], 'intent': intent, 'at_unix': time.time()})
    ended = time.clock_gettime(time.CLOCK_MONOTONIC)
    result = {'version': 1, 'kind': 'closed-synthetic-48-root-cleanup-completion', 'status': 'closed',
        'at_unix': time.time(), 'intent': intent, 'roots_removed': len(roots),
        'logical_bytes_removed': logical, 'recorded_allocated_file_bytes_removed': allocated,
        'disk_freed_is_not_exact_APFS_physical_bytes': True,
        'original_business_data_deleted': False, 'active_meters_stopped': False,
        'publications_unchanged': True, 'wall_seconds': ended - started,
        'wall_clock_basis': 'clock_gettime(CLOCK_MONOTONIC)'}
    completion = save('END.json', result)
    print(json.dumps({'completion': completion, **result}, sort_keys=True))


if __name__ == '__main__':
    main()
