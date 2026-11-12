"""Dispose one explicitly owned local publication reader after final replay.

Reuse the frozen helper's READ-ONLY prepare/source validators. Its CI-only
cleanup entry point is not called and no CI environment is simulated. Local
authority is the exact study cache marker and the recorded fresh reader inode.
All compact metadata, including the unchanged full MAP, is retained before
deleting the disposable namespace. No original source or cold bytes deleted.
"""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'cache/final-publication-replay-v1'
OUT = ROOT / 'operators/final-publication-replay-v1'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def main():
    assert not OUT.exists()
    cache = ROOT / 'cache'
    assert (cache.stat().st_dev, cache.stat().st_ino) == (16777232, 26682812)
    assert sha(cache / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55'
    assert not any(p.is_symlink() for p in [TARGET, *TARGET.parents])
    assert (TARGET.stat().st_dev, TARGET.stat().st_ino) == (16777232, 30402768)
    source = ROOT / 'publication-replay-cleanup/cleanup_v2.py'
    assert sha(source) == 'cdbbbe8134df207338a85c580f04f45c19c5910730d60c8f7ec901a23cd9d093'
    spec = importlib.util.spec_from_file_location('final_local_readonly_validator', source)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    with helper.absolute_dir(ROOT) as repo_fd, helper.absolute_dir(cache) as cache_fd:
        root_fd = os.open(TARGET.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=cache_fd)
        try:
            assert os.fstat(root_fd).st_ino == 30402768
            plan = helper.prepare(repo_fd, root_fd, ROOT, TARGET)
            helper.source_check(repo_fd, plan['sources'])
            rows = plan['rows']
            OUT.mkdir()
            copies = []
            for name, expected in plan['protected'].items():
                raw, current = helper.read_path(root_fd, name, collect=True, limit=helper.META_LIMIT)
                assert current['sha256'] == expected['sha256']
                compressed = len(raw) > 5 * 1024 * 1024
                dest = OUT / 'receipts' / (name + '.gz' if compressed else name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open('xb') as f:
                    if compressed:
                        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
                            z.write(raw)
                    else:
                        f.write(raw)
                assert hashlib.sha256(gzip.decompress(dest.read_bytes()) if compressed else dest.read_bytes()).hexdigest() == expected['sha256']
                copies.append({'original_path': str(TARGET / name), 'retained_path': str(dest),
                    'original_sha256': expected['sha256'], 'original_bytes': len(raw),
                    'lossless_gzip': compressed, 'retained_sha256': sha(dest)})
            with (OUT / 'EXACT-MEMBERS.json.gz').open('xb') as f:
                with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
                    z.write((json.dumps(rows, sort_keys=True, separators=(',', ':')) + '\n').encode())
            save('INTENT.json', {'at_unix': time.time(), 'source_sha256': sha(Path(__file__)),
                'readonly_validator_sha256': sha(source), 'manifest_sha256': plan['manifest_sha256'],
                'target': str(TARGET), 'target_inode': 30402768,
                'exact_inventory_sha256': sha(OUT / 'EXACT-MEMBERS.json.gz'), 'retained_metadata': copies,
                'scope': 'One exact fresh local reader under positively owned cache. Frozen read-only validator verifies actual final complete consumer, full pinned cold/INDEX/MAP/readonly payload membership. All metadata copied unchanged (MAP gzip lossless). No CI variables, source edits, SDK or new grading.'})
            removed = 0
            try:
                for name, row in sorted(rows.items(), key=lambda item: (item[0].count('/'), item[0])):
                    if row['kind'] != 'directory':
                        continue
                    with helper.descend(root_fd, PurePosixPath(name).parts if name else (), rows) as fd:
                        st = os.fstat(fd)
                        helper.owned(st, device=16777232)
                        os.fchmod(fd, stat.S_IMODE(st.st_mode) | 0o700)
                        rows[name]['mode'] = stat.S_IMODE(os.fstat(fd).st_mode)
                for name, row in sorted(rows.items(), key=lambda item: (-item[0].count('/'), item[0])):
                    if not name:
                        continue
                    member = PurePosixPath(name)
                    with helper.descend(root_fd, member.parts[:-1], rows) as parent:
                        current = os.stat(member.name, dir_fd=parent, follow_symlinks=False)
                        assert helper.stable(helper.identity(current)) == helper.stable(row)
                        if row['kind'] == 'regular':
                            os.unlink(member.name, dir_fd=parent)
                            removed += 1
                        else:
                            os.rmdir(member.name, dir_fd=parent)
                assert os.stat(TARGET.name, dir_fd=cache_fd, follow_symlinks=False).st_ino == 30402768
                os.rmdir(TARGET.name, dir_fd=cache_fd)
                helper.source_check(repo_fd, plan['sources'])
                for ref in copies:
                    assert sha(Path(ref['retained_path'])) == ref['retained_sha256']
                assert set(p.name for p in cache.iterdir()) == {'OWNER.json'}
                save('END.json', {'status': 'verified', 'at_unix': time.time(), 'manifest_sha256': plan['manifest_sha256'],
                    'removed_disposable_regular_files': removed,
                    'removed_namespace_allocated_file_bytes_before': sum(r['allocated_bytes'] for r in rows.values() if r['kind'] == 'regular'),
                    'protected_metadata_retained_unchanged': len(copies), 'source_and_cold_inputs_reverified': len(plan['sources']),
                    'file_chmod_calls': 0, 'physical_reclaim_measured': False, 'cache_contains_owner_marker_only': True,
                    'current_product_or_sdk_executed': False})
                print(json.dumps({'status': 'verified', 'removed_disposable_files': removed, 'metadata_retained': len(copies)}))
            except BaseException as error:
                save('FAILED.json', {'status': 'failed', 'removed_files': removed, 'type': type(error).__name__, 'message': str(error)})
                raise
        finally:
            os.close(root_fd)


if __name__ == '__main__':
    main()
