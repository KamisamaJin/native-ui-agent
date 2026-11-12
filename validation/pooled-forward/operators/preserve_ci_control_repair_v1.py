"""Retain tiny CI fixture repair evidence and remove only its two fresh roots.

Separate engineering supplement: does not change the frozen five-transport
study manifest, native code, judgments, expected values or business metrics.
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
HERE = ROOT / 'publication-replay-cleanup'
OUT = ROOT / 'operators/ci-final-23fc8d2f-failure-v1/control-repair-v3'
TARGETS = [HERE / 'HOST-v3-mac39-control', HERE / 'HOST-path-dispatch-v1']


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def scan(root):
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(directory) / name
            s = p.lstat()
            row = {'device': s.st_dev, 'inode': s.st_ino, 'uid': s.st_uid, 'mode': stat.S_IMODE(s.st_mode)}
            assert s.st_uid == os.geteuid()
            if stat.S_ISREG(s.st_mode):
                row.update(kind='regular', bytes=s.st_size, sha256=sha(p), mtime_ns=s.st_mtime_ns)
            elif stat.S_ISDIR(s.st_mode):
                row.update(kind='directory')
            elif stat.S_ISLNK(s.st_mode):
                row.update(kind='symlink', target=os.readlink(p))
            else:
                row.update(kind='special', file_type=stat.S_IFMT(s.st_mode))
            result[str(p)] = row
    return result


def main():
    assert not OUT.exists()
    assert sha(HERE / 'cleanup_v2.py') == 'cdbbbe8134df207338a85c580f04f45c19c5910730d60c8f7ec901a23cd9d093'
    assert json.loads((TARGETS[0] / 'RESULT.json').read_text())['passed'] == 34
    assert json.loads((TARGETS[0] / 'RESULT.json').read_text())['failed'] == 0
    assert json.loads((TARGETS[1] / 'RESULT.json').read_text())['status'] == 'verified'
    members = {}
    root_ids = {}
    for root in TARGETS:
        assert root.parent == HERE and not root.is_symlink()
        root_ids[str(root)] = [root.stat().st_dev, root.stat().st_ino]
        members.update(scan(root))
    OUT.mkdir()
    save('STRUCTURE.json', {'version': 1, 'root_identities': root_ids, 'members': members,
        'links_and_specials': 'Inert metadata only; targets never followed or recreated'})
    files = []
    for i, root in enumerate(TARGETS):
        for key, row in members.items():
            p = Path(key)
            if row['kind'] == 'regular' and p.is_relative_to(root):
                files.append({'root': 'fixture%d' % i, 'path': key,
                    'logical_path': 'fixture%d/' % i + p.relative_to(root).as_posix(),
                    'bytes': row['bytes'], 'sha256': row['sha256'], 'mode': format(row['mode'], '04o')})
    p = OUT / 'STRUCTURE.json'
    files.append({'root': 'metadata', 'path': str(p), 'logical_path': 'metadata/STRUCTURE.json',
                  'bytes': p.stat().st_size, 'sha256': sha(p), 'mode': '0644'})
    spec = {'version': 1, 'roots': [{'id': 'fixture%d' % i, 'kind': 'evidence', 'path': str(p)} for i, p in enumerate(TARGETS)]
             + [{'id': 'metadata', 'kind': 'evidence', 'path': str(OUT)}], 'files': files}
    save('SPEC.json', spec)
    source = ROOT / 'publication-tools/archive.py'
    assert sha(source) == 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8'
    loader = importlib.util.spec_from_file_location('ci_controls_original_archive', source)
    archive = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(archive)
    packed = archive.pack(OUT / 'SPEC.json', OUT / 'archive', 4)
    save('PACKED.json', {'at_unix': time.time(), 'source_sha256': sha(Path(__file__)), 'result': packed,
        'scope': '34 same controls on actual local3.9 plus old/new Path.chmod dispatch regression. Dispatch shim is not an actual Linux/3.11 run; final CI still required. No SDK or product dataset accessed.'})
    # Recheck the complete original member set before any deletion.
    fresh = {}
    for root in TARGETS:
        assert [root.stat().st_dev, root.stat().st_ino] == root_ids[str(root)]
        fresh.update(scan(root))
    assert fresh == members and shutil.rmtree.avoids_symlink_attacks
    save('CLEANUP-INTENT.json', {'at_unix': time.time(), 'roots': root_ids,
        'archive_index_sha256': packed['index_sha256'], 'regular_originals_byte_verified': len(files) - 1,
        'structure_sha256': sha(OUT / 'STRUCTURE.json'), 'file_chmod_calls': 0})
    for root in TARGETS:
        for directory, dirs, names in os.walk(root, followlinks=False):
            p = Path(directory)
            fd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fchmod(fd, stat.S_IMODE(os.fstat(fd).st_mode) | 0o700)
            finally:
                os.close(fd)
        shutil.rmtree(root)
    save('END.json', {'status': 'verified', 'at_unix': time.time(), 'temporary_roots_removed': len(TARGETS),
        'regular_originals_preserved': len(files) - 1, 'archive_index_sha256': packed['index_sha256'],
        'core_helper_sha256': sha(HERE / 'cleanup_v2.py'), 'study_manifest_unchanged': True, 'file_chmod_calls': 0})
    print(json.dumps({'status': 'verified', 'preserved_originals': len(files) - 1, 'temporary_roots_removed': 2}))


if __name__ == '__main__':
    main()
