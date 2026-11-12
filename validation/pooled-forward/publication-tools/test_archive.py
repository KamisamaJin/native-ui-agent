#!/usr/bin/env python3
"""HOST-only explicit archive tests. Every attempt/fixture remains retained."""
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('publication_archive', HERE / 'archive.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
HOST = HERE / 'HOST'; HOST.mkdir(exist_ok=True)


def put(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode())
    return path


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='attempt-', dir=HOST)); self.src = self.root / 'source'; self.src.mkdir()
        put(self.root / 'ATTEMPT.json', {'test': self.id(), 'created_at_unix': time.time(), 'scope': 'Synthetic HOST attempt; retained permanently, no actual dataset/SDK'})
        self.run = patch.object(subprocess, 'run', side_effect=AssertionError('HOST: no process/SDK execution'))
        self.popen = patch.object(subprocess, 'Popen', side_effect=AssertionError('HOST: no process/SDK execution'))
        self.run.start(); self.popen.start()

    def tearDown(self):
        self.popen.stop(); self.run.stop()
        # Deliberately keep successful and failed fixtures and raw attempts.

    def inventory(self, files=None):
        if files is None:
            put(self.src / 'nested/receipt.json', b'{  "original": "/ORIGINAL/NEVER/OPEN/a.json", "v": 1 }\n')
            put(self.src / 'empty.txt', b''); put(self.src / '이름 file.bin', b'\x00\xffHOST\n')
            (self.src / 'nested/receipt.json').chmod(0o640)
            files = [self.src / 'nested/receipt.json', self.src / 'empty.txt', self.src / '이름 file.bin']
        rows = [{'root': 'owned', 'path': str(p), 'logical_path': 'virtual/' + p.relative_to(self.src).as_posix(),
                 'sha256': a.file_hash(p), 'bytes': p.stat().st_size, 'mode': format(stat.S_IMODE(p.stat().st_mode), '04o')} for p in files]
        return {'version': 1, 'roots': [{'id': 'owned', 'kind': 'positive_owned', 'path': str(self.src)}], 'files': rows}

    def pack(self, spec=None, mib=1):
        spec = self.inventory() if spec is None else spec
        path = put(self.root / 'inventory.json', spec); out = self.root / 'archive'
        result = a.pack(path, out, mib); return spec, out, result

    def reseal(self, out, mutate=None):
        index = json.loads((out / 'INDEX.json').read_text())
        if mutate: mutate(index)
        put(out / 'INDEX.json', index)
        seal = json.loads((out / 'SEAL.json').read_text()); seal['index_sha256'] = a.file_hash(out / 'INDEX.json'); put(out / 'SEAL.json', seal)
        return index

    def replace_tar(self, out, transform):
        index = json.loads((out / 'INDEX.json').read_text()); shard = out / index['shards'][0]['file']
        original = shard.read_bytes(); put(self.root / 'original-shard.tar.gz', original)
        raw = gzip.decompress(original); changed = gzip.compress(transform(raw), mtime=0); shard.write_bytes(changed)
        def adjust(i): i['shards'][0].update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
        self.reseal(out, adjust)

    def test_lossless_json_names_permissions_and_virtual_map(self):
        spec, out, packed = self.pack(); before = {r['path']: Path(r['path']).read_bytes() for r in spec['files']}
        result = a.restore(out, self.root / 'restored', packed['index_sha256'])
        mapping = json.loads(Path(result['mapping']).read_text())['mappings']
        self.assertEqual(set(mapping), set(before))
        for row in spec['files']:
            physical = Path(mapping[row['path']]['physical_path'])
            self.assertNotEqual(str(physical), row['path']); self.assertEqual(physical.read_bytes(), before[row['path']])
            self.assertEqual(physical.name, Path(row['path']).name); self.assertEqual(format(stat.S_IMODE(physical.stat().st_mode), '04o'), row['mode'])
            self.assertEqual(Path(row['path']).read_bytes(), before[row['path']])
        self.assertIn(b'/ORIGINAL/NEVER/OPEN/a.json', Path(mapping[spec['files'][0]['path']]['physical_path']).read_bytes())

    def test_default_oversized_single_file_exact_chunk_roundtrip(self):
        p = self.src / 'large.bin'; size = 65 * 1024 * 1024 + 19
        with p.open('wb') as f:
            f.seek(size - 1); f.write(b'Z'); f.seek(a.MAX_LOGICAL - tarfile.RECORDSIZE - 520); f.write(b'HOST boundary marker')
        spec, out, packed = self.pack(self.inventory([p]), 64)
        index = json.loads((out / 'INDEX.json').read_text()); chunks = index['files'][0]['chunks']
        self.assertGreaterEqual(len(chunks), 2); self.assertGreaterEqual(packed['shards'], 2)
        self.assertEqual([c['offset'] for c in chunks], [0, chunks[0]['bytes']])
        self.assertTrue(all(s['tar_bytes'] <= a.MAX_LOGICAL and s['bytes'] < a.MAX_COMPRESSED for s in index['shards']))
        restored = a.restore(out, self.root / 'restored')
        mapping = json.loads(Path(restored['mapping']).read_text())['mappings'][str(p)]
        self.assertEqual(a.file_hash(mapping['physical_path']), spec['files'][0]['sha256'])
        self.assertEqual(Path(mapping['physical_path']).stat().st_size, size)

    def test_small_multishard_incompressible_and_readonly_restore(self):
        files = [put(self.src / ('random-%d.bin' % i), os.urandom(700000)) for i in range(3)]
        spec, out, result = self.pack(self.inventory(files), 1)
        self.assertEqual(result['shards'], 3)
        restored = a.restore(out, self.root / 'restored', readonly=True)
        for value in json.loads(Path(restored['mapping']).read_text())['mappings'].values():
            self.assertFalse(Path(value['physical_path']).stat().st_mode & 0o222)
            self.assertEqual(a.file_hash(value['physical_path']), value['sha256'])

    def test_index_tamper_and_external_pin_reject_resealed_metadata(self):
        _, out, result = self.pack(); original = (out / 'INDEX.json').read_bytes()
        index = json.loads(original); index['counts']['files'] += 1; put(out / 'INDEX.json', index)
        with self.assertRaisesRegex(ValueError, 'Index SHA'): a.verify(out)
        (out / 'INDEX.json').write_bytes(original)
        self.reseal(out, lambda i: i.update(created_at_unix=0))
        with self.assertRaisesRegex(ValueError, 'Index SHA'): a.verify(out, result['index_sha256'])

    def test_extra_and_missing_archive_files_rejected(self):
        _, out, _ = self.pack(); extra = put(out / 'extra.bin', b'HOST extra')
        with self.assertRaisesRegex(ValueError, 'Extra/missing'): a.verify(out)
        extra.rename(self.root / 'preserved-extra.bin')
        shard = next(out.glob('shard-*.tar.gz')); shard.rename(self.root / 'preserved-missing-shard.tar.gz')
        with self.assertRaisesRegex(ValueError, 'Extra/missing'): a.verify(out)

    def test_extra_duplicate_and_traversal_tar_members_rejected(self):
        p = put(self.src / 'one.bin', b'HOST')
        for label in ['extra', 'duplicate', 'escape']:
            sub = self.root / label; sub.mkdir(); spec = self.inventory([p]); sp = put(sub / 'spec.json', spec); out = sub / 'archive'; a.pack(sp, out, 1)
            def mutate(raw):
                first = raw[:1024]
                if label == 'escape':
                    h = tarfile.TarInfo('../escape'); h.size = 4; h.mode = 0o600
                    return h.tobuf(format=tarfile.USTAR_FORMAT) + raw[512:]
                addition = first if label == 'duplicate' else tarfile.TarInfo('unlisted/member').tobuf(format=tarfile.USTAR_FORMAT)
                return first + addition + b'\0' * (len(raw) - len(first) - len(addition))
            self.replace_tar(out, mutate)
            with self.assertRaises((ValueError, tarfile.HeaderError)): a.verify(out)
        self.assertFalse((self.root / 'escape').is_file())

    def test_corrupt_and_truncated_gzip_rejected_even_with_updated_outer_sha(self):
        _, out, _ = self.pack(); index = json.loads((out / 'INDEX.json').read_text()); path = out / index['shards'][0]['file']; original = path.read_bytes()
        for label, raw in [('corrupt', original[:15] + bytes([original[15] ^ 255]) + original[16:]), ('truncated', original[:-7])]:
            put(self.root / ('preserved-' + label + '.tar.gz'), raw); path.write_bytes(raw)
            self.reseal(out, lambda i: i['shards'][0].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
            with self.assertRaises(Exception): a.verify(out)
        put(self.root / 'original-compressed-shard.tar.gz', original)

    def test_symlink_source_parent_and_archive_member_rejected(self):
        target = put(self.root / 'external.bin', b'HOST outside prefix')
        link = self.src / 'link.bin'; link.symlink_to(target)
        spec = {'version': 1, 'roots': [{'id': 'owned', 'kind': 'evidence', 'path': str(self.src)}],
                'files': [{'root': 'owned', 'path': str(link), 'logical_path': 'virtual/link.bin', 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': target.stat().st_size, 'mode': '0644'}]}
        sp = put(self.root / 'symlink-spec.json', spec)
        with self.assertRaises(OSError): a.pack(sp, self.root / 'symlink-archive', 1)
        self.assertTrue((self.root / 'symlink-archive/FAILED.json').is_file())
        p = put(self.src / 'normal.bin', b'HOST normal'); _, out, _ = self.pack(self.inventory([p]))
        shard = next(out.glob('shard-*.tar.gz')); original = self.root / 'saved-shard.tar.gz'; shard.rename(original); shard.symlink_to(original)
        with self.assertRaises(OSError): a.verify(out)

    def test_outside_prefix_git_and_path_escape_specs_rejected(self):
        p = put(self.src / 'normal.bin', b'HOST'); good = self.inventory([p])
        for change in [('outside', lambda s: s['files'][0].update(path=str(self.root / 'normal.bin'))),
                       ('escape', lambda s: s['files'][0].update(logical_path='../normal.bin')),
                       ('git', lambda s: s['files'][0].update(logical_path='.git/normal.bin')),
                       ('rename', lambda s: s['files'][0].update(logical_path='other.bin'))]:
            value = copy.deepcopy(good); change[1](value); sp = put(self.root / (change[0] + '.json'), value)
            with self.assertRaises(ValueError): a.pack(sp, self.root / (change[0] + '-out'), 1)

    def test_source_changed_during_pack_failure_preserves_raw_attempt(self):
        p = put(self.src / 'mutable.bin', b'A' * 2000000); inventory = self.inventory([p]); sp = put(self.root / 'spec.json', inventory)
        original = a.Shards.add; calls = []
        def mutate(writer, member, data):
            result = original(writer, member, data)
            if not calls:
                calls.append(True)
                with p.open('r+b') as f: f.seek(1500000); f.write(b'changed-source')
            return result
        out = self.root / 'failed-archive'
        with patch.object(a.Shards, 'add', mutate):
            with self.assertRaisesRegex(ValueError, 'Source'): a.pack(sp, out, 1)
        self.assertTrue((out / 'FAILED.json').is_file()); self.assertTrue(list(out.glob('shard-*.tar.gz')))
        self.assertNotEqual(a.file_hash(p), inventory['files'][0]['sha256'])
        with self.assertRaises(Exception): a.verify(out)

    def test_chunk_offset_full_hash_and_duplicate_spec_rejected(self):
        _, out, _ = self.pack()
        self.reseal(out, lambda i: i['files'][0]['chunks'][0].update(offset=1))
        with self.assertRaisesRegex(ValueError, 'offset'): a.verify(out)
        value = self.inventory(); value['files'].append(copy.deepcopy(value['files'][0])); sp = put(self.root / 'duplicate.json', value)
        with self.assertRaisesRegex(ValueError, 'Duplicate'): a.pack(sp, self.root / 'duplicate-out')

    def test_verify_restore_never_need_original_sources_and_fresh_dest_required(self):
        spec, out, _ = self.pack(); self.src.rename(self.root / 'source-preserved-away')
        self.assertEqual(a.verify(out)['files'], len(spec['files']))
        dest = self.root / 'virtual'; a.restore(out, dest)
        with self.assertRaisesRegex(ValueError, 'Fresh'): a.restore(out, dest)
        with self.assertRaisesRegex(ValueError, 'Fresh'): a.pack(self.root / 'inventory.json', out)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArchiveTests))
    summary = {'kind': 'HOST', 'native_execution': False, 'sdk_forwarding': False, 'actual_dataset_access': False,
               'scope': 'Synthetic explicit-file archive validation only; all attempt directories and failures retained',
               'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful()}
    path = HOST / ('RESULT-%d.json' % time.time_ns()); put(path, summary)
    print(json.dumps({'result': str(path), **summary}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
