"""Verify every mapped byte, then remove one exact redundant restore namespace.

Keep its original RESTORED-MAP.json and control records for terminal archival.
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
OUT = ROOT / 'operators/qualification-restore-cleanup-v1'
BASE = ROOT / 'cache/publication-archives/closed-qualification-v1/readonly-restore'
MAP_SHA = '5c6d03b7d31fa586b010081f5f8017d1905e6fcb92e0f89ecd27202630f0c4d1'
INDEX_SHA = 'e00d650e80cc36655bf9526f1071c481352ab2a097642d15f91b4a6d016cb3cc'


def module(name, path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    helpers = module('restore_cleanup_metadata', ROOT / 'operators/cleanup_closed_fixtures_v1.py', 'a834370695c562d04f8168a699ba5b3d26a91593da9e90a0bc6e21f8a5901389')
    helpers.OUT = OUT
    OUT.mkdir(exist_ok=False)
    save, ref = helpers.save, helpers.ref
    started = time.clock_gettime(time.CLOCK_MONOTONIC)
    save('START.json', {'version': 1, 'started_at_unix': time.time(), 'started_at_clock_gettime': started,
        'target': str(BASE / 'files'), 'map_sha256': MAP_SHA, 'index_sha256': INDEX_SHA})
    cache = (ROOT / 'cache').lstat()
    assert stat.S_ISDIR(cache.st_mode) and [cache.st_dev, cache.st_ino] == [16777232, 26682812]
    assert helpers.file_sha(ROOT / 'cache/OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55'
    preservation = module('restore_cleanup_preservation', ROOT / 'publication-actual-preservation-review/preserve.py', '4a1e18ebb43d1cddf82a02f69666d2ec9b898204c131469905b6a96646657a83')
    plan_path = ROOT / 'publication-actual-preservation-review/HOST/FINAL-PLAN.json'
    assert helpers.file_sha(plan_path) == '50ea2874d6afb65e80ccf6927f2b930243444d7be0b9c704431945283a45d9e8'
    plan = json.loads(plan_path.read_text())
    preservation.validate_plan(plan)
    required, _ = preservation.immutable_requirements(plan)
    target = BASE / 'files'
    preservation.cleanup_scope_check(plan, target, meters_closed=False)
    assert not any(Path(p) == target or target in Path(p).parents for p in required)
    transport_path = ROOT / 'publications/closed-qualification-v1/TRANSPORT.json'
    assert helpers.file_sha(transport_path) == '941790690a13b58d05e6a4823f73d954eb441dd8c7958e7b2ae9478b84983ef8'
    for member in json.loads(transport_path.read_text())['files'].values():
        p = transport_path.parent / member['stored']
        assert p.stat().st_size == member['stored_bytes'] and helpers.file_sha(p) == member['stored_sha256']
    session = module('qualification_cleanup_session', ROOT / 'publication-map-session/session.py', '9502fc59697f039021a4a2c9f5046ea2f46d32a235613ceb2c719709573c425c')
    reader = session.MapSessionReader(BASE / 'RESTORED-MAP.json', map_sha256=MAP_SHA, index_sha256=INDEX_SHA)
    count = reader.verify_all()
    assert count == 82407 and reader.namespace == target
    expected = {row['physical_path'] for row in reader._rows.values()}
    namespace_identity = list(reader._namespace_identity)
    seen, directories = set(), []
    logical = allocated = 0
    stack = [target]
    while stack:
        p = stack.pop()
        s = p.lstat()
        if stat.S_ISDIR(s.st_mode):
            directories.append({'path': str(p), 'device': s.st_dev, 'inode': s.st_ino, 'mode': stat.S_IMODE(s.st_mode)})
            stack.extend(Path(e.path) for e in os.scandir(p))
        else:
            assert stat.S_ISREG(s.st_mode) and str(p) in expected
            seen.add(str(p))
            logical += s.st_size
            allocated += s.st_blocks * 512
    assert seen == expected
    reader.close()
    intent = save('INTENT.json', {'version': 1, 'target': str(target), 'namespace_identity': namespace_identity,
        'map': ref(BASE / 'RESTORED-MAP.json'), 'transport': ref(transport_path), 'frozen_session': ref(ROOT / 'publication-map-session/session.py'),
        'all_mapped_files_reverified': count, 'exact_member_set': True, 'required_refs_checked': len(required),
        'required_ref_intersections': 0, 'logical_bytes': logical, 'allocated_file_bytes': allocated,
        'directories': directories, 'original_map_and_original_qualification_retained': True})
    for directory in directories:
        fd = os.open(directory['path'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            s = os.fstat(fd)
            assert [s.st_dev, s.st_ino] == [directory['device'], directory['inode']]
            os.fchmod(fd, directory['mode'] | 0o700)
        finally:
            os.close(fd)
    assert [target.lstat().st_dev, target.lstat().st_ino] == namespace_identity
    assert shutil.rmtree.avoids_symlink_attacks
    shutil.rmtree(target)
    assert helpers.file_sha(BASE / 'RESTORED-MAP.json') == MAP_SHA
    result = {'version': 1, 'status': 'closed', 'intent': intent, 'removed': str(target),
        'logical_bytes_removed': logical, 'recorded_allocated_file_bytes_removed': allocated,
        'disk_freed_is_not_exact_APFS_physical_bytes': True, 'original_qualification_deleted': False,
        'original_business_data_deleted': False, 'original_map_retained': True, 'active_meters_stopped': False,
        'wall_seconds': time.clock_gettime(time.CLOCK_MONOTONIC) - started, 'wall_clock_basis': 'clock_gettime(CLOCK_MONOTONIC)'}
    completion = save('END.json', result)
    print(json.dumps({'completion': completion, **result}, sort_keys=True))


if __name__ == '__main__':
    main()
