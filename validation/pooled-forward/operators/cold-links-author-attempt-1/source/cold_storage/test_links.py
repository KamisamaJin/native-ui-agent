import errno
import hashlib
import json
from pathlib import Path
import stat
import unittest
from unittest import mock

import cold
from test_cold import ColdStorage


class ReadonlyTransportLinks(unittest.TestCase):
    def setUp(self):
        ColdStorage.setUp(self)

    def tearDown(self):
        ColdStorage.tearDown(self)

    def raw_names(self):
        return [p.name for p in self.cold.iterdir()
                if p.name == 'SEAL.json' or p.name.startswith('shard-')]

    def test_only_raw_transport_members_share_storage(self):
        output = self.root / 'decoded'
        result = cold.decode(self.cold, self.result['transport_sha256'], output)
        self.assertEqual(result['transport_storage']['readonly_linked_members'], len(self.raw_names()))
        for name in self.raw_names():
            self.assertEqual((self.cold / name).stat().st_ino, (output / name).stat().st_ino)
        for name in ['INDEX.json', 'SPEC.json']:
            self.assertNotEqual((self.cold / (name + '.gz')).stat().st_ino, (output / name).stat().st_ino)

    def test_writable_inputs_keep_original_copy_behavior(self):
        for name in self.raw_names():
            (self.cold / name).chmod(0o644)
        before = {name: (cold.hash_file(self.cold / name), stat.S_IMODE((self.cold / name).stat().st_mode))
                  for name in self.raw_names()}
        output = self.root / 'decoded'
        result = cold.decode(self.cold, self.result['transport_sha256'], output)
        self.assertEqual(result['transport_storage']['readonly_linked_members'], 0)
        for name in self.raw_names():
            self.assertNotEqual((self.cold / name).stat().st_ino, (output / name).stat().st_ino)
            self.assertEqual(before[name], (cold.hash_file(self.cold / name), stat.S_IMODE((self.cold / name).stat().st_mode)))
            self.assertEqual(stat.S_IMODE((output / name).stat().st_mode), 0o444)

    def test_cross_filesystem_failure_falls_back_without_input_changes(self):
        output = self.root / 'decoded'
        before = {name: cold.hash_file(self.cold / name) for name in self.raw_names()}
        with mock.patch.object(cold.os, 'link', side_effect=OSError(errno.EXDEV, 'synthetic cross-device boundary')):
            result = cold.decode(self.cold, self.result['transport_sha256'], output)
        self.assertEqual(result['transport_storage']['readonly_linked_members'], 0)
        self.assertEqual(before, {name: cold.hash_file(self.cold / name) for name in self.raw_names()})
        for name in self.raw_names():
            self.assertNotEqual((self.cold / name).stat().st_ino, (output / name).stat().st_ino)

    def test_raw_symlink_is_rejected_even_if_bytes_match(self):
        name = self.raw_names()[0]
        source = self.cold / name
        outside = self.root / 'same-bytes'
        outside.write_bytes(source.read_bytes())
        source.unlink()
        source.symlink_to(outside)
        with self.assertRaises(ValueError):
            cold.decode(self.cold, self.result['transport_sha256'], self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_mutating_a_shared_alias_fails_both_outer_and_inner_verification(self):
        output = self.root / 'decoded'
        cold.decode(self.cold, self.result['transport_sha256'], output)
        shard = next(output.glob('shard-*.tar.gz'))
        shard.chmod(0o644)
        raw = bytearray(shard.read_bytes())
        raw[-1] ^= 1
        shard.write_bytes(raw)
        with self.assertRaises((ValueError, OSError)):
            self.module.verify(output, self.index_sha)
        with self.assertRaises(ValueError):
            cold.decode(self.cold, self.result['transport_sha256'], self.root / 'bad')

    def test_unlinking_decoded_alias_preserves_cold_member(self):
        output = self.root / 'decoded'
        cold.decode(self.cold, self.result['transport_sha256'], output)
        name = self.raw_names()[0]
        wanted = cold.hash_file(self.cold / name)
        (output / name).unlink()
        self.assertEqual(cold.hash_file(self.cold / name), wanted)
        self.assertEqual(cold.decode(self.cold, self.result['transport_sha256'], self.root / 'another')['status'], 'verified')

    def test_existing_target_is_not_replaced(self):
        source = self.cold / self.raw_names()[0]
        target = self.root / 'existing'
        target.write_bytes(b'keep this original')
        with self.assertRaises(ValueError):
            cold.readonly_link(source, target)
        self.assertEqual(target.read_bytes(), b'keep this original')

    def test_identical_logical_payloads_restore_to_independent_inodes(self):
        rows = []
        for name in ['first.bin', 'second.bin']:
            source = self.source / name
            source.write_bytes(b'same logical bytes')
            rows.append({'root': 'source', 'path': str(source), 'logical_path': 'source/' + name,
                         'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                         'bytes': source.stat().st_size, 'mode': '0644'})
        spec = self.root / 'two-spec.json'
        spec.write_text(json.dumps({'version': 1, 'roots': [{'id': 'source', 'kind': 'evidence',
                                                           'path': str(self.source)}], 'files': rows}))
        archive = self.root / 'two-archive'
        packed = self.module.pack(spec, archive, 1)
        transport = self.root / 'two-cold'
        seal = cold.pack(archive, packed['index_sha256'], transport)
        decoded = self.root / 'two-decoded'
        cold.decode(transport, seal['transport_sha256'], decoded)
        restored = self.root / 'two-restored'
        self.module.restore(decoded, restored, packed['index_sha256'], True)
        first, second = [restored / 'files/source' / name for name in ['first.bin', 'second.bin']]
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertNotEqual(first.stat().st_ino, second.stat().st_ino)
        self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o444)


if __name__ == '__main__':
    unittest.main(verbosity=2)
