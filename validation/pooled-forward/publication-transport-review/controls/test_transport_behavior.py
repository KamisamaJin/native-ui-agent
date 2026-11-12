#!/usr/bin/env python3
"""Bounded independent transport controls; only small retained synthetic data."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
import unittest


ROOT = Path(__file__).resolve().parent.parent
RUN = MODULES = cold = None


def sha(raw): return hashlib.sha256(raw).hexdigest()


def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def dump(path, value): path.write_bytes(encoded(value))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class TransportBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = RUN / 'fixture'; cls.master.mkdir()
        source = cls.master / 'original-source'; source.mkdir()
        cls.payloads = {
            'numeric.json': b' \r\n{"synthetic":true,"actual":9007199254740993.0,"tiny":1e-999,"order":["F","P","U"]}\r\n',
            'native.bin': bytes(range(256)) * 3,
            'empty.dat': b'',
            'unicode.txt': 'Synthetic 공백  x\r\n'.encode('utf-16'),
            'do-not-execute.sh': b'#!/bin/sh\n# Synthetic archived bytes; never execute.\n'}
        rows = []
        for name, raw in cls.payloads.items():
            p = source / name; p.write_bytes(raw); mode = 0o755 if name.endswith('.sh') else 0o644; p.chmod(mode)
            rows.append({'root': 'synthetic', 'path': str(p), 'logical_path': 'synthetic/' + name,
                         'sha256': sha(raw), 'bytes': len(raw), 'mode': format(mode, '04o')})
        spec = cls.master / 'original-spec.json'
        spec.write_bytes(encoded({'version': 1, 'roots': [{'id': 'synthetic', 'kind': 'evidence', 'path': str(source)}], 'files': rows}).replace(b'\n', b'\r\n'))
        original_archive = cls.master / 'original-archive'
        cls.archive_module = cold.archive_module()
        cls.archive_module.pack(spec, original_archive, 1)
        cls.archive = cls.master / 'retained-inner'; original_archive.rename(cls.archive)
        source.rename(cls.master / 'retained-source'); spec.rename(cls.master / 'retained-spec.json')
        cls.original_paths = [str(source), str(spec), str(original_archive), *(row['path'] for row in rows)]
        assert not any(Path(path).exists() for path in cls.original_paths)
        cls.index_sha = sha((cls.archive / 'INDEX.json').read_bytes())
        cls.master_cold = cls.master / 'transport'
        cls.packed = cold.pack(cls.archive, cls.index_sha, cls.master_cold)
        dump(cls.master / 'FIXTURE.json', {'synthetic_only': True, 'original_namespaces_absent': cls.original_paths,
                                         'index_sha256': cls.index_sha, 'transport_sha256': cls.packed['transport_sha256'],
                                         'payload_sha256': {name: sha(raw) for name, raw in cls.payloads.items()}})

    def setUp(self):
        self.case = RUN / 'cases' / self._testMethodName; self.case.mkdir(parents=True)
        self.folder = self.case / 'transport'; shutil.copytree(self.master_cold, self.folder)
        self.pin = self.packed['transport_sha256']; self.observations = []

    def tearDown(self): dump(self.case / 'OBSERVATIONS.json', self.observations)

    def observe(self, label, value): self.observations.append({'label': label, 'value': value})

    def reject(self, callback, label):
        try: result = callback()
        except Exception as error:
            self.observe(label, {'rejected': True, 'type': type(error).__name__, 'message': str(error)})
            return error
        self.observe(label, {'rejected': False, 'returned': result})
        self.fail('Expected fail-closed rejection: ' + label)

    def repin(self, folder, value):
        p = folder / 'TRANSPORT.json'
        before = folder.parent / 'BEFORE-TRANSPORT.json'
        if not before.exists(): before.write_bytes(p.read_bytes())
        p.chmod(0o644); p.write_bytes(encoded(value)); p.chmod(0o444)
        return sha(p.read_bytes())

    def seal(self): return json.loads((self.folder / 'TRANSPORT.json').read_bytes())

    def test_01_exact_roundtrip_and_readonly_restore_without_original_paths(self):
        result = cold.decode(self.folder, self.pin, self.case / 'decoded')
        self.observe('decode', result)
        self.assertEqual(result['inner_verified']['status'], 'verified')
        self.assertEqual({p.name: p.read_bytes() for p in self.archive.iterdir()},
                         {p.name: p.read_bytes() for p in (self.case / 'decoded').iterdir()})
        restored = self.case / 'restored'
        self.archive_module.restore(self.case / 'decoded', restored, self.index_sha, True)
        for name, raw in self.payloads.items():
            p = restored / 'files/synthetic' / name
            self.assertEqual(p.read_bytes(), raw)
            self.assertEqual(p.stat().st_mode & 0o777, 0o555 if name.endswith('.sh') else 0o444)
        self.assertFalse(any(Path(path).exists() for path in self.original_paths))

    def test_02_only_index_and_spec_are_compressed_and_pack_is_deterministic(self):
        again = self.case / 'packed-again'
        result = cold.pack(self.archive, self.index_sha, again); self.observe('pack', result)
        self.assertEqual(result['transport_sha256'], self.pin)
        seal = self.seal()
        for name, row in seal['files'].items():
            raw = (self.folder / row['stored']).read_bytes(); original = (self.archive / name).read_bytes()
            if name in {'INDEX.json', 'SPEC.json'}:
                self.assertEqual(row['stored'], name + '.gz'); self.assertEqual(gzip.decompress(raw), original)
            else:
                self.assertEqual(row['stored'], name); self.assertEqual(raw, original)
        self.assertEqual({p.name: p.read_bytes() for p in self.folder.iterdir()},
                         {p.name: p.read_bytes() for p in again.iterdir()})

    def test_03_invalid_external_transport_pin_fails_before_output(self):
        for i, pin in enumerate(['0' * 64, '', None, 'A' * 64]):
            target = self.case / ('bad-' + str(i))
            self.reject(lambda pin=pin, target=target: cold.decode(self.folder, pin, target), 'external transport pin ' + str(i))
            self.assertFalse(target.exists())

    def test_04_pack_requires_nonoptional_exact_original_index_pin(self):
        self.reject(lambda: cold.pack(self.archive, None, self.case / 'bad-pack'), 'None is not an external original index SHA')
        self.assertFalse((self.case / 'bad-pack').exists())

    def test_05_decode_requires_nonoptional_exact_original_index_pin(self):
        seal = self.seal(); seal['index_sha256'] = None; pin = self.repin(self.folder, seal)
        self.reject(lambda: cold.decode(self.folder, pin, self.case / 'bad-decode'), 'repinned transport with null original index SHA')
        self.assertFalse((self.case / 'bad-decode').exists())

    def test_06_stored_corruption_is_not_accepted(self):
        p = self.folder / 'INDEX.json.gz'; p.chmod(0o644); p.write_bytes(p.read_bytes()[:-3])
        self.reject(lambda: cold.decode(self.folder, self.pin, self.case / 'bad'), 'truncated stored index')

    def test_07_outer_seal_change_without_new_external_pin_fails(self):
        seal = self.seal(); seal['scope'] += ' synthetic altered bytes'; self.repin(self.folder, seal)
        self.reject(lambda: cold.decode(self.folder, self.pin, self.case / 'bad'), 'changed outer seal')
        self.assertFalse((self.case / 'bad').exists())

    def test_08_repin_cannot_hide_wrong_expanded_sha(self):
        seal = self.seal(); seal['files']['INDEX.json']['sha256'] = '0' * 64
        pin = self.repin(self.folder, seal)
        self.reject(lambda: cold.decode(self.folder, pin, self.case / 'bad'), 'wrong decoded index SHA')

    def test_09_expansion_is_exact_in_both_directions(self):
        for delta in (-1, 1):
            folder = self.case / ('transport-' + str(delta)); shutil.copytree(self.master_cold, folder)
            seal = json.loads((folder / 'TRANSPORT.json').read_bytes()); seal['files']['INDEX.json']['bytes'] += delta
            pin = self.repin(folder, seal)
            self.reject(lambda folder=folder, pin=pin, delta=delta: cold.decode(folder, pin, self.case / ('bad-' + str(delta))), 'expanded length delta ' + str(delta))

    def test_10_invalid_size_types_and_limits_fail_before_output(self):
        for i, size in enumerate([-1, True, cold.LIMIT + 1]):
            seal = self.seal(); seal['files']['INDEX.json']['bytes'] = size; pin = self.repin(self.folder, seal)
            target = self.case / ('bad-' + str(i))
            self.reject(lambda pin=pin, target=target: cold.decode(self.folder, pin, target), 'invalid declared size ' + str(size))
            self.assertFalse(target.exists())

    def test_11_unsafe_inner_names_stored_paths_and_aliases_fail(self):
        original_seal = self.seal()
        mutations = [
            lambda v: v['files'].update({'../outside': copy.deepcopy(v['files']['SEAL.json'])}),
            lambda v: v['files']['INDEX.json'].update(stored='../INDEX.json.gz'),
            lambda v: v['files']['INDEX.json'].update(stored='/INDEX.json.gz'),
            lambda v: v['files']['SPEC.json'].update(stored='INDEX.json.gz')]
        for i, mutate in enumerate(mutations):
            seal = copy.deepcopy(original_seal); mutate(seal); pin = self.repin(self.folder, seal)
            target = self.case / ('bad-' + str(i))
            self.reject(lambda pin=pin, target=target: cold.decode(self.folder, pin, target), 'unsafe metadata path variant ' + str(i))
            self.assertFalse(target.exists())

    def test_12_symlink_members_are_rejected_before_output(self):
        p = self.folder / 'INDEX.json.gz'; retained = self.case / 'retained-index.gz'; p.rename(retained); p.symlink_to(retained)
        self.reject(lambda: cold.decode(self.folder, self.pin, self.case / 'bad'), 'symlink transport member')
        self.assertFalse((self.case / 'bad').exists())

    def test_13_output_paths_cannot_overlap_or_follow_aliases(self):
        target = self.case / 'physical'; target.mkdir(); alias = self.case / 'alias'; alias.symlink_to(target, target_is_directory=True)
        paths = [self.folder / 'inside', self.folder, alias / 'output', self.case / 'physical' / '..' / 'output']
        for i, path in enumerate(paths):
            self.reject(lambda path=path: cold.decode(self.folder, self.pin, path), 'unsafe output variant ' + str(i))
        self.assertFalse((target / 'output').exists()); self.assertFalse((self.case / 'output').exists())

    def test_14_extra_transport_member_and_unsafe_inner_source_are_rejected(self):
        (self.folder / 'extra.bin').write_bytes(b'Synthetic unexpected transport member')
        self.reject(lambda: cold.decode(self.folder, self.pin, self.case / 'bad'), 'extra transport file')
        inner = self.case / 'inner'; shutil.copytree(self.archive, inner)
        p = inner / 'SEAL.json'; retained = self.case / 'retained-seal.json'; p.rename(retained); p.symlink_to(retained)
        self.reject(lambda: cold.pack(inner, self.index_sha, self.case / 'bad-pack'), 'symlink inner archive member')
        self.assertFalse((self.case / 'bad-pack').exists())

    def test_15_selfconsistent_outer_pins_still_require_genuine_inner_verifier(self):
        index = json.loads((self.archive / 'INDEX.json').read_bytes()); index['counts']['files'] += 1
        index_raw = encoded(index); index_sha = sha(index_raw)
        inner_seal = json.loads((self.archive / 'SEAL.json').read_bytes()); inner_seal['index_sha256'] = index_sha
        inner_seal_raw = encoded(inner_seal)
        seal = self.seal(); seal['index_sha256'] = index_sha
        for name, raw in [('INDEX.json', index_raw), ('SEAL.json', inner_seal_raw)]:
            row = seal['files'][name]; stored = gzip.compress(raw, mtime=0) if name == 'INDEX.json' else raw
            p = self.folder / row['stored']; p.chmod(0o644); p.write_bytes(stored); p.chmod(0o444)
            row.update(sha256=sha(raw), bytes=len(raw), stored_sha256=sha(stored), stored_bytes=len(stored))
        pin = self.repin(self.folder, seal)
        error = self.reject(lambda: cold.decode(self.folder, pin, self.case / 'bad'), 'genuine frozen verifier must reject invalid inner counts')
        self.assertIn('counts differ', str(error))
        self.assertTrue((self.case / 'bad/INDEX.json').is_file(), 'Must reach the real post-decode inner verification')

    def test_16_corrupt_gzip_crc_fails_even_when_outer_stored_pin_matches(self):
        p = self.folder / 'INDEX.json.gz'; raw = bytearray(p.read_bytes()); raw[-8] ^= 1
        p.chmod(0o644); p.write_bytes(raw); p.chmod(0o444)
        seal = self.seal(); seal['files']['INDEX.json']['stored_sha256'] = sha(raw)
        pin = self.repin(self.folder, seal)
        self.reject(lambda: cold.decode(self.folder, pin, self.case / 'bad'), 'gzip CRC failure with valid stored pin')

    def test_17_changed_parent_code_is_rejected_without_importing_it(self):
        parent = self.case / 'altered-parent'; (parent / 'cold_storage').mkdir(parents=True)
        (parent / 'cold_storage/cold.py').write_bytes((MODULES / 'cold.py').read_bytes())
        original = (MODULES.parent / 'archive.py').read_bytes()
        (parent / 'archive.py').write_bytes(original + b'\nraise RuntimeError("Synthetic changed parent must never import")\n')
        module = load_module(parent / 'cold_storage/cold.py', 'synthetic_changed_parent_transport')
        error = self.reject(module.archive_module, 'changed frozen archive code')
        self.assertIn('code differs', str(error))


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.rows = []
    def addSuccess(self, test): super().addSuccess(test); self.rows.append({'test': test.id(), 'status': 'pass'})
    def addFailure(self, test, error):
        super().addFailure(test, error); self.rows.append({'test': test.id(), 'status': 'fail', 'traceback': ''.join(traceback.format_exception(*error))})
    def addError(self, test, error):
        super().addError(test, error); self.rows.append({'test': test.id(), 'status': 'error', 'traceback': ''.join(traceback.format_exception(*error))})


def main():
    global RUN, MODULES, cold
    parser = argparse.ArgumentParser(); parser.add_argument('--modules', type=Path, required=True); parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args(); RUN, MODULES = args.run, args.modules
    assert all(p.is_absolute() and p.is_relative_to(ROOT) for p in (RUN, MODULES))
    RUN.mkdir(parents=True, exist_ok=False)
    cold = load_module(MODULES / 'cold.py', 'reviewed_transport')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TransportBehavior)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    report = {'version': 1, 'synthetic_only': True, 'tests_run': result.testsRun,
              'passed': result.testsRun - len(result.failures) - len(result.errors), 'failures': len(result.failures), 'errors': len(result.errors),
              'code_sha256': sha((MODULES / 'cold.py').read_bytes()), 'parent_archive_sha256': sha((MODULES.parent / 'archive.py').read_bytes()),
              'test_sha256': sha(Path(__file__).read_bytes()), 'controls': result.rows}
    dump(RUN / 'RESULT.json', report)
    print(json.dumps({key: report[key] for key in ('tests_run', 'passed', 'failures', 'errors', 'code_sha256', 'test_sha256')}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
