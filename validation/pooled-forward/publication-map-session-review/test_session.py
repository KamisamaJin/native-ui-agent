import importlib.util
import os
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'vendor'))
sys.path.insert(0, str(HERE))
import session
_spec = importlib.util.spec_from_file_location('original_resolver_controls', HERE/'vendor/test_resolver.py')
fixture = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fixture)


class SessionControls(fixture.Controls):
    def resolver(self, **kwargs):
        return session.MapSessionReader(str(self.map), map_sha256=kwargs.get('map_sha256', self.pin),
            index_sha256=kwargs.get('index_sha256', fixture.INDEX))

    def test_same_size_map_write_and_restored_mtime_do_not_restore_ctime(self):
        reader = self.resolver(); original = self.original+'/packet/result.json'
        before = self.map.stat(); raw = self.map.read_bytes()
        self.map.write_bytes(raw.replace(b'Synthetic fixture', b'Synthetic fixturE'))
        os.utime(self.map, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaises(ValueError): reader.hash(original)

    def test_identical_bytes_atomic_replacement_invalidates_session(self):
        reader = self.resolver(); replacement = self.map.with_name('replacement.json')
        replacement.write_bytes(self.map.read_bytes()); os.replace(replacement, self.map)
        with self.assertRaises(ValueError): reader.read_bytes(self.original+'/packet/result.json')

    def test_map_symlink_and_map_parent_symlink_do_not_gain_authority(self):
        reader = self.resolver(); moved = self.map.with_name('moved-map.json')
        self.map.rename(moved); self.map.symlink_to(moved)
        with self.assertRaises((ValueError, OSError)): reader.hash(self.original+'/packet/result.json')

    def test_full_closure_verifies_map_and_every_payload_and_prevents_reuse(self):
        reader = self.resolver(); self.assertEqual(reader.verify_all(), len(self.rows)); reader.close()
        with self.assertRaises(ValueError): reader.hash(self.original+'/packet/result.json')

    def test_missing_payload_fails_full_closure_without_original_fallback(self):
        reader = self.resolver(); key = self.original+'/packet/result.json'
        original = Path(key); original.parent.mkdir(parents=True); original.write_bytes(self.payload)
        Path(self.rows[key]['physical_path']).unlink()
        with self.assertRaises((ValueError, OSError)): reader.verify_all()


if __name__ == '__main__': unittest.main(verbosity=2)
