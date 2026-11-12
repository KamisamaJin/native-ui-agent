"""Remove four exact, transport-verified redundant archive scratch directories.

This operator does not clean original study evidence, fixtures, restored files,
failed archive inputs, SDKs, devices, meters, source, publications or Git.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'operators/closed-cold-duplicate-cleanup-v1'
PINS = {
    'operators/cache-current-identity.json': None,
    'PUBLICATION-AND-CLEANUP-POLICY-v1.json': None,
    'publication-actual-preservation-review/preserve.py': '4a1e18ebb43d1cddf82a02f69666d2ec9b898204c131469905b6a96646657a83',
    'publication-actual-preservation-review/HOST/FINAL-PLAN.json': '50ea2874d6afb65e80ccf6927f2b930243444d7be0b9c704431945283a45d9e8',
    'operators/cold-revalidation-v1/END.json': 'fefef4b2fb333a4a9a0c81c8e75f43bd45335922e9789a64ce10f6d84f2aa214',
    'publications/closed-synthetic-host-v1/TRANSPORT.json': 'a6641b4e42d8ea542db0cafa91d5677c7b344ad6de79b10ff512fdf7e1bc9a21',
    'publications/closed-qualification-v1/TRANSPORT.json': '941790690a13b58d05e6a4823f73d954eb441dd8c7958e7b2ae9478b84983ef8',
    'cache/business/independent-evaluation/continuation-collection-v3/END.json': 'c46ee5cb38310d81784a2aa3163acfeaf408d4f32c6798f016ca32ea02842215',
}
TRANSPORTS = [
    ('closed-synthetic-host-v1', 'closed-synthetic-host-v2'),
    ('closed-qualification-v1', 'closed-qualification-v1'),
]


def identity(s):
    return [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def checked_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        first = os.fstat(fd)
        assert stat.S_ISREG(first.st_mode), str(path)
        with os.fdopen(os.dup(fd), 'rb') as f:
            raw = f.read()
        assert identity(first) == identity(os.fstat(fd)), str(path)
        return raw, first
    finally:
        os.close(fd)


def reference(path):
    raw, _ = checked_bytes(path)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, value):
    path = OUT / name
    with path.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')
    path.chmod(0o444)
    return reference(path)


def cache_owner():
    meta = json.loads((ROOT / 'operators/cache-current-identity.json').read_text())
    assert meta['path'] == str(ROOT / 'cache')
    current = (ROOT / 'cache').lstat()
    assert stat.S_ISDIR(current.st_mode)
    assert [current.st_dev, current.st_ino] == [16777232, 26682812]
    marker = reference(ROOT / 'cache/OWNER.json')
    assert marker['sha256'] == meta['marker_sha256'] == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55'
    return {'root': str(ROOT / 'cache'), 'device': current.st_dev,
            'inode': current.st_ino, 'marker': marker}


def main():
    OUT.mkdir(exist_ok=False)
    pins = {}
    for relative, expected in PINS.items():
        ref = reference(ROOT / relative)
        assert expected is None or ref['sha256'] == expected, relative
        pins[relative] = ref
    owner = cache_owner()
    assert json.loads((ROOT / 'operators/cold-revalidation-v1/END.json').read_text())['status'] == 'verified'
    assert json.loads((ROOT / 'cache/business/independent-evaluation/continuation-collection-v3/END.json').read_text())['status'] == 'closed'
    stopped = ROOT / 'operators/cohort2/queue-service/STOPPED.json'
    assert stopped.is_file() and (ROOT / 'operators/cohort2/queue-service.stop').is_file()
    pins['public_queue_stopped'] = reference(stopped)
    spec = importlib.util.spec_from_file_location('owned_duplicate_preservation', ROOT / 'publication-actual-preservation-review/preserve.py')
    preservation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preservation)
    plan = json.loads((ROOT / 'publication-actual-preservation-review/HOST/FINAL-PLAN.json').read_text())
    preservation.validate_plan(plan)
    required, _ = preservation.immutable_requirements(plan)
    targets = []
    for public, scratch in TRANSPORTS:
        transport = ROOT / 'publications' / public / 'TRANSPORT.json'
        manifest = json.loads(transport.read_text())
        for member in manifest['files'].values():
            path = transport.parent / member['stored']
            raw, _ = checked_bytes(path)
            assert len(raw) == member['stored_bytes'] and hashlib.sha256(raw).hexdigest() == member['stored_sha256']
        for leaf in ['archive', 'cold-decoded']:
            root = ROOT / 'cache/publication-archives' / scratch / leaf
            for parent in [root.parent.parent, root.parent, root]:
                assert stat.S_ISDIR(parent.lstat().st_mode), str(parent)
            preservation.cleanup_scope_check(plan, root, meters_closed=False)
            assert not any(Path(p) == root or root in Path(p).parents for p in required)
            names = sorted(x.name for x in root.iterdir())
            assert names == sorted(manifest['files']), str(root)
            files = []
            for name in names:
                raw, s = checked_bytes(root / name)
                expected = manifest['files'][name]
                sha = hashlib.sha256(raw).hexdigest()
                assert sha == expected['sha256'] and len(raw) == expected['bytes'], str(root / name)
                files.append({'name': name, 'sha256': sha, 'bytes': len(raw),
                              'allocated_bytes': s.st_blocks * 512, 'identity': identity(s)})
            targets.append({'path': str(root), 'device': root.stat().st_dev,
                            'inode': root.stat().st_ino, 'files': files, 'transport': reference(transport)})
    intent = save('INTENT.json', {'version': 1, 'kind': 'four-exact-redundant-cold-scratch-cleanup-intent',
        'at_unix': time.time(), 'owner': owner, 'pins': pins, 'targets': targets,
        'required_refs_checked': len(required), 'required_ref_intersections': 0,
        'scope': 'Only these four complete duplicate archive/decoded containers. Public cold bytes, original study/qualification data, restored files, first failed SPEC/metadata, all source and active meters remain.'})
    removed = []
    for target in targets:
        assert cache_owner() == owner
        root = Path(target['path'])
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            s = os.fstat(fd)
            assert [s.st_dev, s.st_ino] == [target['device'], target['inode']]
            assert sorted(os.listdir(fd)) == [x['name'] for x in target['files']]
            for member in target['files']:
                current = os.stat(member['name'], dir_fd=fd, follow_symlinks=False)
                assert identity(current) == member['identity']
                os.unlink(member['name'], dir_fd=fd)
        finally:
            os.close(fd)
        assert [root.lstat().st_dev, root.lstat().st_ino] == [target['device'], target['inode']]
        root.rmdir()
        removed.append(target['path'])
        save('REMOVED-%02d.json' % len(removed), {'path': target['path'], 'at_unix': time.time(), 'intent': intent})
    result = {'version': 1, 'kind': 'four-exact-redundant-cold-scratch-cleanup-completion',
        'status': 'closed', 'at_unix': time.time(), 'intent': intent, 'removed': removed,
        'logical_bytes_removed': sum(f['bytes'] for t in targets for f in t['files']),
        'recorded_allocated_bytes_removed': sum(f['allocated_bytes'] for t in targets for f in t['files']),
        'disk_freed_is_not_exact_APFS_physical_bytes': True,
        'original_study_data_deleted': False, 'active_meters_stopped': False,
        'publications_unchanged': True}
    completion = save('END.json', result)
    print(json.dumps({'completion': completion, **result}, sort_keys=True))


if __name__ == '__main__':
    main()
