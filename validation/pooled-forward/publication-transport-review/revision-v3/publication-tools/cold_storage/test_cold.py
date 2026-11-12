import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import cold


class ColdStorage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        rows = []
        for i, raw in enumerate([b'{"actual":9007199254740993.0,"unknown":null}\n', b'\x00\xff\x80native\n', b'']):
            p = self.source / f'{i}.json'; p.write_bytes(raw)
            rows.append({'root': 'source', 'path': str(p), 'logical_path': f'source/{p.name}',
                         'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'mode': '0644'})
        spec = self.root / 'spec.json'; spec.write_text(json.dumps({'version': 1,
            'roots': [{'id': 'source', 'kind': 'evidence', 'path': str(self.source)}], 'files': rows}))
        self.archive = self.root / 'archive'; self.module = cold.archive_module()
        self.module.pack(spec, self.archive, 1)
        self.index_sha = cold.hash_file(self.archive / 'INDEX.json')
        self.cold = self.root / 'cold'
        self.result = cold.pack(self.archive, self.index_sha, self.cold)

    def tearDown(self): self.temp.cleanup()

    def rewrite(self, value):
        p = self.cold / 'TRANSPORT.json'; p.chmod(0o644); p.write_text(json.dumps(value))
        return cold.hash_file(p)

    def test_lossless_decode_and_restore_with_originals_absent(self):
        before = {p.name: p.read_bytes() for p in self.archive.iterdir()}
        self.archive.rename(self.root / 'retired-archive'); self.source.rename(self.root / 'retired-source')
        decoded = self.root / 'decoded'
        result = cold.decode(self.cold, self.result['transport_sha256'], decoded)
        self.assertEqual(result['inner_verified']['status'], 'verified')
        self.assertEqual(before, {p.name: p.read_bytes() for p in decoded.iterdir()})
        restore = self.root / 'restored'; self.module.restore(decoded, restore, self.index_sha, True)
        self.assertEqual((restore / 'files/source/0.json').read_bytes(), b'{"actual":9007199254740993.0,"unknown":null}\n')

    def test_stored_corruption_fails(self):
        p = self.cold / 'INDEX.json.gz'; p.chmod(0o644); p.write_bytes(p.read_bytes()[:-3])
        with self.assertRaises(ValueError): cold.decode(self.cold, self.result['transport_sha256'], self.root / 'bad')

    def test_external_pin_required(self):
        with self.assertRaises(ValueError): cold.decode(self.cold, '0' * 64, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_symlink_seal_never_read(self):
        p = self.cold / 'TRANSPORT.json'; raw = p.read_bytes(); p.unlink()
        outside = self.root / 'outside.json'; outside.write_bytes(raw); p.symlink_to(outside)
        with self.assertRaises(ValueError): cold.decode(self.cold, self.result['transport_sha256'], self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_nested_output_and_existing_output_rejected(self):
        with self.assertRaises(ValueError): cold.decode(self.cold, self.result['transport_sha256'], self.cold / 'inside')
        with self.assertRaises(ValueError): cold.decode(self.cold, self.result['transport_sha256'], self.source)

    def test_path_traversal_rejected_even_with_new_transport_pin(self):
        value = json.loads((self.cold / 'TRANSPORT.json').read_text())
        value['files']['INDEX.json']['stored'] = '../outside.json'
        with self.assertRaises(ValueError): cold.decode(self.cold, self.rewrite(value), self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_declared_expansion_is_exact(self):
        value = json.loads((self.cold / 'TRANSPORT.json').read_text()); value['files']['INDEX.json']['bytes'] -= 1
        with self.assertRaises(ValueError): cold.decode(self.cold, self.rewrite(value), self.root / 'bad')

    def test_extra_transport_member_rejected(self):
        (self.cold / 'extra').write_bytes(b'not an archive member')
        with self.assertRaises(ValueError): cold.decode(self.cold, self.result['transport_sha256'], self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
