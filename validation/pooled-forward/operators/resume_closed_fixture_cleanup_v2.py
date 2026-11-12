"""Resume the recorded cleanup after its owned readonly-directory failure."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import time

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    original = load_module('closed_fixture_cleanup_v1', ROOT / 'operators/cleanup_closed_fixtures_v1.py', 'a834370695c562d04f8168a699ba5b3d26a91593da9e90a0bc6e21f8a5901389')
    previous = ROOT / 'operators/closed-fixture-cleanup-v1'
    assert original.file_sha(previous / 'INTENT.json') == '122e625c67325da72d8de5bcd530548d4c8a7b2792cfdf819b75506719587808'
    assert original.file_sha(ROOT / 'operators/closed-fixture-cleanup-v1.stderr.log') == 'f6fd06670861bf37507e7441f212123ce7ab6c197c847ff72ce7cd52966365dc'
    intent = json.loads((previous / 'INTENT.json').read_text())
    entry = json.loads((ROOT / 'operators/archive-selection/closed-synthetic-host-v1/ENTRY.json').read_text())
    roots = [Path(x) for x in entry['selection']]
    receipts = sorted(previous.glob('REMOVED-*.json'))
    assert len(receipts) == 6
    for root, receipt in zip(roots[:6], receipts):
        value = json.loads(receipt.read_text())
        assert value['path'] == str(root) and value['intent']['sha256'] == '122e625c67325da72d8de5bcd530548d4c8a7b2792cfdf819b75506719587808'
        assert not root.exists() and not root.is_symlink()
    out = ROOT / 'operators/closed-fixture-cleanup-v2'
    out.mkdir(exist_ok=False)
    original.OUT = out
    save, ref = original.save, original.ref
    started = time.clock_gettime(time.CLOCK_MONOTONIC)
    save('START.json', {'version': 2, 'started_at_unix': time.time(), 'started_at_clock_gettime': started,
        'original_intent': ref(previous / 'INTENT.json'), 'original_failure': ref(ROOT / 'operators/closed-fixture-cleanup-v1.stderr.log'),
        'scope': 'Only remaining42 explicitly inventoried roots; chmod verified owned directory handles to permit deletion. Missing members allowed only in the originally interrupted seventh root.'})
    for relative, expected in original.PINS.items():
        assert original.file_sha(ROOT / relative) == expected, relative
    preservation = load_module('closed_fixture_resume_preservation', ROOT / 'publication-actual-preservation-review/preserve.py', '4a1e18ebb43d1cddf82a02f69666d2ec9b898204c131469905b6a96646657a83')
    plan = json.loads((ROOT / 'publication-actual-preservation-review/HOST/FINAL-PLAN.json').read_text())
    preservation.validate_plan(plan)
    required, _ = preservation.immutable_requirements(plan)
    metadata = json.loads((ROOT / 'cache/publication-archives/closed-synthetic-host-v1/metadata/FIXTURE-METADATA.json').read_text())
    dirs = {m['path']: m for m in metadata['directories']}
    files = {m['original']: m for m in metadata['files']}
    special = {m['path']: m for m in metadata['symlink_or_special_metadata_only']}
    observed = []
    verified_files = 0
    for index, root in enumerate(roots[6:], 6):
        assert root.parent.name == 'HOST' and root.is_relative_to(ROOT) and '..' not in root.parts
        assert [root.lstat().st_dev, root.lstat().st_ino] == intent['root_identities'][str(root)]
        preservation.cleanup_scope_check(plan, root, meters_closed=False)
        assert not any(Path(p) == root or root in Path(p).parents for p in required)
        expected = {p for p in set(dirs) | set(files) | set(special) if p == str(root) or p.startswith(str(root) + '/')}
        seen, owned_dirs = set(), []
        stack = [root]
        while stack:
            p = stack.pop()
            key = str(p)
            s = p.lstat()
            assert key in expected and '..' not in p.parts and p.is_relative_to(root), key
            seen.add(key)
            if stat.S_ISDIR(s.st_mode):
                m = dirs[key]
                assert [s.st_dev, s.st_ino] == [m['device'], m['inode']] and format(stat.S_IMODE(s.st_mode), '04o') == m['mode'], key
                owned_dirs.append({'path': key, 'device': s.st_dev, 'inode': s.st_ino, 'mode': stat.S_IMODE(s.st_mode)})
                stack.extend(Path(e.path) for e in os.scandir(p))
            elif stat.S_ISREG(s.st_mode):
                m = files[key]
                assert [s.st_dev, s.st_ino, s.st_size] == [m['device'], m['inode'], m['bytes']], key
                assert format(stat.S_IMODE(s.st_mode), '04o') == m['mode'] and original.file_sha(p) == m['sha256'], key
                verified_files += 1
            else:
                m = special[key]
                assert stat.S_ISLNK(s.st_mode) and m['kind'] == 'symlink' and os.readlink(p) == m['target'], key
        assert seen == expected or index == 6
        observed.append({'root': str(root), 'current_members': len(seen), 'already_removed_members': len(expected - seen), 'owned_directories': owned_dirs})
    permission_intent = save('INTENT.json', {'version': 2, 'original_intent': ref(previous / 'INTENT.json'),
        'original_failure': ref(ROOT / 'operators/closed-fixture-cleanup-v1.stderr.log'), 'remaining_roots': observed,
        'files_reverified': verified_files, 'required_refs_checked': len(required), 'required_ref_intersections': 0,
        'only_directory_permissions_change': True, 'raw_bytes_preserved_by_original_cold_transport': True})
    assert shutil.rmtree.avoids_symlink_attacks
    for i, record in enumerate(observed):
        root = Path(record['root'])
        for directory in record['owned_directories']:
            fd = os.open(directory['path'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                s = os.fstat(fd)
                assert [s.st_dev, s.st_ino] == [directory['device'], directory['inode']]
                os.fchmod(fd, directory['mode'] | 0o700)
            finally:
                os.close(fd)
        assert [root.lstat().st_dev, root.lstat().st_ino] == intent['root_identities'][str(root)]
        shutil.rmtree(root)
        save('REMOVED-%02d.json' % (i + 7), {'path': str(root), 'intent': permission_intent, 'at_unix': time.time()})
    result = {'version': 2, 'kind': 'closed-synthetic-48-root-cleanup-completion', 'status': 'closed',
        'at_unix': time.time(), 'original_intent': ref(previous / 'INTENT.json'), 'resumption_intent': permission_intent,
        'roots_removed_original': 6, 'roots_removed_resumption': 42, 'roots_removed_total': 48,
        'logical_file_bytes_removed_original_inventory': intent['logical_bytes'],
        'allocated_file_bytes_removed_original_inventory': intent['recorded_allocated_file_bytes'],
        'disk_freed_is_not_exact_APFS_physical_bytes': True, 'original_business_data_deleted': False,
        'active_meters_stopped': False, 'publications_unchanged': True,
        'resumption_wall_seconds': time.clock_gettime(time.CLOCK_MONOTONIC) - started}
    completion = save('END.json', result)
    print(json.dumps({'completion': completion, **result}, sort_keys=True))


if __name__ == '__main__':
    main()
