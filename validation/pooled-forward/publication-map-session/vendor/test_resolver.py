"""Small synthetic HOST controls; no cohort data, SDK or subprocesses."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

from resolver import Resolver


HERE = Path(__file__).resolve().parent
HOST = HERE / 'HOST'
INDEX = 'ab' * 32


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Controls(unittest.TestCase):
    def setUp(self):
        HOST.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='synthetic-', dir=str(HOST)))
        self.namespace = self.root / 'virtual/files'
        self.namespace.mkdir(parents=True)
        self.map = self.root / 'virtual/RESTORED-MAP.json'
        self.original = str(self.root / 'original')
        self.payload = b'{"original_path":"/ORIGINAL/NEVER/OPEN/a.json","value":17}\n'
        self.rows = {}
        self.add('packet/result.json', 'evidence/packet/result.json', self.payload)
        self.add('packet/native/frame.png', 'evidence/packet/native/frame.png', b'PNG synthetic bytes')
        self.add('packet/native/frames/second.png', 'evidence/packet/native/frames/second.png', b'second synthetic bytes')
        self.write_map()
        (self.root / 'ATTEMPT.json').write_text(json.dumps({'test': self.id(), 'at_unix': time.time(), 'scope': 'Synthetic HOST only; retained fixture, no actual cohort or SDK'})+'\n')

    def add(self, relative, logical, raw):
        p = self.namespace / logical
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw); p.chmod(0o444)
        self.rows[self.original+'/'+relative] = {'physical_path': str(p), 'logical_path': logical,
            'sha256': sha(raw), 'bytes': len(raw), 'original_mode': '0644', 'restored_mode': '0444'}

    def write_map(self, value=None):
        if value is None:
            value = {'format': 'explicit-file-lossless-v1', 'version': 1, 'index_sha256': INDEX,
                'namespace': str(self.namespace), 'mappings': self.rows, 'scope': 'Synthetic fixture, not an archive verification claim'}
        self.map.write_text(json.dumps(value, indent=2)+'\n')
        self.pin = sha(self.map.read_bytes())

    def resolver(self, **kwargs):
        return Resolver(str(self.map), map_sha256=kwargs.get('map_sha256', self.pin), index_sha256=kwargs.get('index_sha256', INDEX))

    def test_roundtrip_and_embedded_original_path_remain_exact(self):
        before = self.map.read_bytes(); r = self.resolver(); original = self.original+'/packet/result.json'
        self.assertEqual(r.read_bytes(original), self.payload)
        self.assertEqual(r.read_json(original)['original_path'], '/ORIGINAL/NEVER/OPEN/a.json')
        self.assertEqual(r.hash(original), sha(self.payload))
        self.assertEqual(r.file(original), self.namespace/'evidence/packet/result.json')
        self.assertEqual(self.map.read_bytes(), before)
        self.assertEqual(r.file(original).stat().st_mode & 0o777, 0o444)

    def test_complete_directory_keeps_nested_relative_layout(self):
        r = self.resolver()
        self.assertEqual(r.directory(self.original+'/packet/native'), self.namespace/'evidence/packet/native')
        self.assertEqual(r.directory(self.original+'/packet'), self.namespace/'evidence/packet')

    def test_wrong_external_map_and_index_pins_rejected(self):
        with self.assertRaises(ValueError): self.resolver(map_sha256='00'*32)
        with self.assertRaises(ValueError): self.resolver(index_sha256='cd'*32)
        with self.assertRaises(ValueError): self.resolver(map_sha256=None)

    def test_missing_original_never_falls_back_even_when_original_exists(self):
        original = Path(self.original)/'not-in-map.json'; original.parent.mkdir(); original.write_bytes(b'exists only in original')
        r = self.resolver()
        with self.assertRaises(KeyError): r.read_bytes(str(original))
        with self.assertRaises(KeyError): r.directory(str(original.parent/'unmapped-dir'))
        self.assertEqual(original.read_bytes(), b'exists only in original')

    def test_missing_restored_file_never_falls_back_to_original(self):
        original = Path(self.original)/'packet/result.json'; original.parent.mkdir(parents=True); original.write_bytes(self.payload)
        Path(self.rows[str(original)]['physical_path']).unlink()
        with self.assertRaises((ValueError, OSError)): self.resolver().file(str(original))

    def test_changed_payload_hash_rejected_even_at_same_size(self):
        r = self.resolver(); original = self.original+'/packet/result.json'; p=r.file(original)
        p.chmod(0o644); p.write_bytes(b'X'*len(self.payload)); p.chmod(0o444)
        with self.assertRaises(ValueError): r.read_bytes(original)

    def test_byte_count_and_mode_drift_rejected(self):
        original = self.original+'/packet/result.json'; row=self.rows[original]
        row['bytes'] += 1; self.write_map()
        with self.assertRaises(ValueError): self.resolver().hash(original)
        row['bytes'] -= 1; self.write_map(); r=self.resolver()
        Path(row['physical_path']).chmod(0o644)
        with self.assertRaises(ValueError): r.file(original)

    def test_map_replacement_or_mutation_rejected(self):
        r=self.resolver(); self.map.write_bytes(self.map.read_bytes()+b' ')
        with self.assertRaises(ValueError): r.file(self.original+'/packet/result.json')

    def test_physical_escape_and_namespace_escape_rejected(self):
        original=self.original+'/packet/result.json'; self.rows[original]['physical_path']=str(self.root/'outside.json'); self.write_map()
        with self.assertRaises(ValueError): self.resolver()
        value=json.loads(self.map.read_bytes()); value['namespace']=str(self.root/'outside'); self.write_map(value)
        with self.assertRaises(ValueError): self.resolver()

    def test_symlink_file_and_ancestor_rejected(self):
        original=self.original+'/packet/result.json'; p=Path(self.rows[original]['physical_path'])
        outside=self.root/'outside.json'; outside.write_bytes(self.payload)
        p.unlink(); p.symlink_to(outside)
        with self.assertRaises((ValueError, OSError)): self.resolver().read_bytes(original)
        p.unlink(); parent=p.parent; moved=parent.with_name('moved-packet'); parent.rename(moved); parent.symlink_to(moved, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)): self.resolver().directory(self.original+'/packet')

    def test_namespace_symlink_rejected(self):
        moved=self.namespace.with_name('moved-files'); self.namespace.rename(moved); self.namespace.symlink_to(moved, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)): self.resolver()

    def test_inconsistent_directory_layout_rejected(self):
        original=self.original+'/packet/native/frames/second.png'; old=Path(self.rows[original]['physical_path'])
        raw=old.read_bytes(); old.unlink()
        self.rows.pop(original); self.add('packet/native/frames/second.png','elsewhere/second.png',raw); self.write_map()
        r=self.resolver()
        self.assertEqual(r.read_bytes(original),raw)
        with self.assertRaises(ValueError): r.directory(self.original+'/packet/native')

    def test_unmapped_extra_file_and_directory_rejected(self):
        r=self.resolver(); root=self.namespace/'evidence/packet/native'; extra=root/'extra.png'; extra.write_bytes(b'extra')
        with self.assertRaises(ValueError): r.directory(self.original+'/packet/native')
        extra.unlink(); (root/'unmapped-empty').mkdir()
        with self.assertRaises(ValueError): r.directory(self.original+'/packet/native')

    def test_conflicting_alias_and_duplicate_json_key_rejected(self):
        self.rows[self.original+'/other/result.json']=copy.deepcopy(self.rows[self.original+'/packet/result.json']); self.write_map()
        with self.assertRaises(ValueError): self.resolver()
        raw=self.map.read_bytes(); raw=raw[:-2]+b',"version":1}\n'; self.map.write_bytes(raw); self.pin=sha(raw)
        with self.assertRaises(ValueError): self.resolver()

    def test_traversal_and_file_as_directory_rejected(self):
        r=self.resolver()
        with self.assertRaises(ValueError): r.file(self.original+'/packet/../packet/result.json')
        with self.assertRaises(ValueError): r.directory(self.original+'/packet/result.json')


if __name__ == '__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    HOST.mkdir(exist_ok=True)
    record={'version':1,'at_unix':time.time(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'scope':'Author synthetic HOST controls only; no business data, SDK or cleanup','retained_attempts':True}
    (HOST/('RESULT-'+str(time.time_ns())+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
