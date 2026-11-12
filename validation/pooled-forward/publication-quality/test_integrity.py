"""Synthetic positive/hostile evidence packets; no native run or quality claims."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from integrity import digest, sha, verify_packet
from verify import LiveReader, reader_module


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


class Fixture:
    def __init__(self, root):
        self.root = root
        self.packet = root / 'packet'
        self.capture = root / 'original/capture'
        self.ledger_path = root / 'operator/LEDGER.json'
        self.packet.mkdir(parents=True)
        self.ledger_path.parent.mkdir()
        self.originals = {}
        self.members = {}
        self.copies = []
        self.projections = []
        source = b'// SYNTHETIC TEST ONLY\nstruct Widget {}\n'
        self.add_copy('source/0/Widget.swift', root / 'original/source/Widget.swift', source)
        self.add_copy('source/placement/ios/Package.swift', root / 'original/stock/Package.swift', b'// synthetic placement\n')
        self.add_copy('contracts/public/ios/API.md', root / 'original/API.md', b'Synthetic API contract.\n')
        files = {'0/Widget.swift': {'sha256': sha(source), 'bytes': len(source)}}
        manifest = {'files': files, 'content_sha256': digest(files)}
        self.manifest = self.put(root / 'original/source.json', manifest)
        original = {'0/Widget.swift': sha(source)}
        self.put(self.capture / 'source-before.json', original)
        self.put(self.capture / 'source-after.json', original)
        self.put(self.capture / 'request.json', {'source_sha256': digest(original), 'source_roots': ['/synthetic/production']})
        self.projections.append({'anonymous_observation': 'public-ios', 'original': self.ref(self.capture / 'source-before.json'),
                                 'source_model': None, 'controller_content_sha256': digest(files), 'sut_source_sha256': digest(original)})
        native = {'version': 1, 'snapshots': [{'index': 0, 'state': 'initial', 'actual_text': 'Observed'}],
                  'actions': [{'success': True}], 'issues': [], 'operations': {'seconds': {'native': 0}}}
        self.put(self.capture / 'native/observation.json', native)
        self.project('observations/public-ios/native/observation.json', self.capture / 'native/observation.json',
                     {key: value for key, value in native.items() if key not in {'issues', 'operations'}},
                     {'all_original_top_level_members_except': ['operations', 'issues'], 'retained_values_unchanged': True})
        image = b'SYNTHETIC IMAGE BYTES; NOT A PNG OR NATIVE CAPTURE'
        self.add_copy('observations/public-ios/native/frame.png', self.capture / 'native/frame.png', image)
        automatic = {'assertions': [{'id': 'one', 'actual': 3, 'snapshot_indices': [0], 'status': 'P'},
                                    {'id': 'two', 'actual': False, 'snapshot_indices': [0], 'status': 'F'}]}
        self.put(self.capture / 'automatic.json', automatic)
        self.project('observations/public-ios/automatic-actuals.json', self.capture / 'automatic.json',
                     {'assertions': [{key: row[key] for key in ['id', 'actual', 'snapshot_indices']} for row in automatic['assertions']]},
                     {'all_assertions': True, 'member_allowlist': ['id', 'actual', 'snapshot_indices'], 'retained_values_unchanged': True})
        self.receipt = {'source_sha256': digest(original), 'observation_sha256': self.ref(self.capture / 'native/observation.json')['sha256'],
                        'automatic_sha256': self.ref(self.capture / 'automatic.json')['sha256'], 'image_hashes': {'frame.png': sha(image)}}
        self.put(self.capture / 'result.json', self.receipt)
        self.put(self.capture / 'execution.json', {'selected_states': ['initial']})
        catalog = {'version': 1, 'rows': [{'id': 'visual-one', 'state': 'initial', 'method': 'visual', 'proposition': 'Synthetic question', 'review_id': 'review-one'}]}
        catalog_sha = digest(catalog)
        catalog_original = dict(catalog, catalog_sha256=catalog_sha)
        catalog_path = root / 'operator/public-ios-catalog-original.json'
        self.put(catalog_path, catalog_original)
        self.members['observations/public-ios/catalog.json'] = encoded(catalog)
        template = {'version': 1, 'catalog_sha256': catalog_sha, 'observation_sha256': self.receipt['observation_sha256'],
                    'decisions': [{'review_id': 'review-one', 'actual': None, 'reason': '', 'snapshot_indices': []}]}
        self.members['observations/public-ios/visual-requirements.json'] = encoded({'rows': [{'id': 'visual-one', 'state': 'initial', 'proposition': 'Synthetic question', 'review_id': 'review-one'}], 'submission_template': template})
        self.description = {'anonymous_group': 'Case01-I', 'fixed_source_file_count': 1, 'source_files': files,
                            'production_placement': {'ios': 'source/placement/ios/Package.swift'},
                            'contracts': {'public': {'ios': {'API': 'contracts/public/ios/API.md'}}},
                            'observations': [{'id': 'public-ios', 'family': 'public', 'platform': 'ios', 'facts_available': True,
                                              'native_observation': 'observations/public-ios/native/observation.json',
                                              'automatic_actuals': 'observations/public-ios/automatic-actuals.json',
                                              'catalog': 'observations/public-ios/catalog.json',
                                              'visual_requirements': 'observations/public-ios/visual-requirements.json',
                                              'original_observation_sha256': self.receipt['observation_sha256'], 'original_image_count': 1}]}
        self.members['PACKET.json'] = encoded(self.description)
        self.ledger = {'version': 1, 'kind': 'operator-only-anonymous-packet-byte-and-projection-ledger', 'group': 'Case01-I',
                       'copies': self.copies, 'projections': self.projections, 'original_source_manifest': self.ref(self.manifest),
                       'catalog_commands': [{'native_or_sdk_execution': False, 'output': self.ref(catalog_path)}]}
        self.reseal()

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else encoded(value))
        return path

    def ref(self, path):
        return {'path': str(path), 'sha256': sha(path.read_bytes())}

    def add_copy(self, relative, original, raw):
        self.put(original, raw)
        self.members[relative] = raw
        self.copies.append({'anonymous_relative': relative, 'original': self.ref(original), 'bytes': len(raw)})

    def project(self, relative, original, value, selection):
        self.members[relative] = encoded(value)
        self.projections.append({'anonymous_relative': relative, 'original': self.ref(original),
                                 'projection_sha256': sha(self.members[relative]), 'selection': selection})

    def reseal(self):
        self.ledger['anonymous_inventory'] = {name: {'sha256': sha(raw), 'bytes': len(raw)} for name, raw in self.members.items()}
        for name, raw in self.members.items():
            self.put(self.packet / name, raw)
        self.put(self.ledger_path, self.ledger)
        self.put(self.packet / 'SEAL.json', {'version': 1, 'kind': 'anonymous-fixed-version-input-seal', 'anonymous_group': 'Case01-I',
                                           'files': {name: sha(raw) for name, raw in self.members.items()}})
        self.seal_sha = sha((self.packet / 'SEAL.json').read_bytes())
        self.ledger_sha = sha(self.ledger_path.read_bytes())

    def verify(self):
        return verify_packet(LiveReader(reader_module()), str(self.packet), str(self.ledger_path),
                             packet_seal_sha256=self.seal_sha, ledger_sha256=self.ledger_sha)


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='quality-synthetic-')
        self.fixture = Fixture(Path(self.temp.name).resolve())

    def tearDown(self):
        self.temp.cleanup()

    def reject(self, phrase=None):
        with self.assertRaises((ValueError, KeyError, FileNotFoundError, OSError)) as context:
            self.fixture.verify()
        if phrase:
            self.assertIn(phrase, str(context.exception))

    def test_complete(self):
        self.assertEqual(self.fixture.verify()['native_images'], 1)

    def test_external_seal_pin(self):
        self.fixture.seal_sha = '0' * 64
        self.reject('Original reference bytes differ')

    def test_external_ledger_pin(self):
        self.fixture.ledger_sha = '0' * 64
        self.reject('Original reference bytes differ')

    def test_extra_member(self):
        (self.fixture.packet / 'rogue').write_text('unexpected')
        self.reject('namespace differs')

    def test_extra_empty_directory(self):
        (self.fixture.packet / 'rogue').mkdir()
        self.reject('empty packet directory')

    def test_symlink(self):
        p = self.fixture.packet / 'source/0/Widget.swift'
        p.unlink()
        p.symlink_to(self.fixture.root / 'original/source/Widget.swift')
        self.reject('symlink')

    def test_original_corruption(self):
        (self.fixture.capture / 'native/frame.png').write_bytes(b'bad')
        self.reject('Original reference bytes differ')

    def test_resealed_native_fact_changed(self):
        f = self.fixture
        name = 'observations/public-ios/native/observation.json'
        value = json.loads(f.members[name]); value['actions'][0]['success'] = False
        f.members[name] = encoded(value)
        next(row for row in f.projections if row.get('anonymous_relative') == name)['projection_sha256'] = sha(f.members[name])
        f.reseal()
        self.reject('changes or drops original facts')

    def test_resealed_actual_row_dropped(self):
        f = self.fixture
        name = 'observations/public-ios/automatic-actuals.json'
        value = json.loads(f.members[name]); value['assertions'].pop()
        f.members[name] = encoded(value)
        next(row for row in f.projections if row.get('anonymous_relative') == name)['projection_sha256'] = sha(f.members[name])
        f.reseal()
        self.reject('changes or drops original facts')

    def test_resealed_omitted_cost_added(self):
        f = self.fixture
        name = 'observations/public-ios/native/observation.json'
        value = json.loads(f.members[name]); value['operations'] = {'seconds': 123}
        f.members[name] = encoded(value)
        next(row for row in f.projections if row.get('anonymous_relative') == name)['projection_sha256'] = sha(f.members[name])
        f.reseal()
        self.reject('changes or drops original facts')

    def test_source_after_differs(self):
        self.fixture.put(self.fixture.capture / 'source-after.json', {'0/Widget.swift': '0' * 64})
        self.reject('source changed')

    def test_resealed_visual_question_dropped(self):
        f = self.fixture
        name = 'observations/public-ios/visual-requirements.json'
        value = json.loads(f.members[name]); value['rows'] = []
        f.members[name] = encoded(value); f.reseal()
        self.reject('Visual requirements incomplete')

    def test_resealed_image_dropped(self):
        f = self.fixture
        name = 'observations/public-ios/native/frame.png'
        del f.members[name]
        f.copies[:] = [row for row in f.copies if row['anonymous_relative'] != name]
        (f.packet / name).unlink()
        f.reseal()
        self.reject('image namespace differs')

    def test_resealed_identity_leak(self):
        f = self.fixture
        f.members['INSTRUCTIONS.md'] = b'candidate-v13'
        f.reseal()
        self.reject('Identity disclosure')

    def test_unregistered_projection(self):
        f = self.fixture
        next(row for row in f.projections if 'anonymous_relative' in row)['selection'] = {'arbitrary': True}
        f.reseal()
        self.reject('Unregistered projection')

    def test_capture_absence_is_not_inferred(self):
        f = self.fixture
        f.projections.append({'anonymous_observation': 'public-ios', 'original': f.ref(f.capture / 'result.json'),
                              'selection': 'Capture absence only; no arm/tool/cost/failure verdict text.'})
        f.put(f.capture / 'result.json', dict(f.receipt, capture={'path': 'exists'}))
        f.projections[-1]['original'] = f.ref(f.capture / 'result.json')
        f.reseal()
        self.reject('absence conflicts')

    def test_duplicate_source_binding(self):
        f = self.fixture
        f.projections.append(copy.deepcopy(f.projections[0])); f.reseal()
        self.reject('Duplicate or unknown source binding')

    def test_existing_native_facts_cannot_be_unknown(self):
        f = self.fixture
        f.description['observations'][0]['facts_available'] = False
        f.members['PACKET.json'] = encoded(f.description)
        f.reseal()
        self.reject('must not be marked missing')

    def restored(self, remove_mapping=None):
        f = self.fixture
        destination = f.root / 'virtual'
        namespace = destination / 'files'
        mappings = {}
        for folder in ['original', 'packet', 'operator']:
            for path in (f.root / folder).rglob('*'):
                if not path.is_file():
                    continue
                relative = path.relative_to(f.root)
                target = namespace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                target.chmod(0o444)
                mappings[str(path)] = {'physical_path': str(target), 'logical_path': relative.as_posix(),
                                       'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
                                       'original_mode': '0' + format(path.stat().st_mode & 0o777, '03o'), 'restored_mode': '0444'}
        if remove_mapping:
            del mappings[str(remove_mapping)]
        mapping = destination / 'RESTORED-MAP.json'
        index_sha = 'b' * 64
        f.put(mapping, {'format': 'explicit-file-lossless-v1', 'version': 1, 'index_sha256': index_sha,
                        'namespace': str(namespace), 'mappings': mappings, 'scope': 'Synthetic HOST only.'})
        return reader_module().Resolver(str(mapping), map_sha256=sha(mapping.read_bytes()), index_sha256=index_sha)

    def test_virtual_restore_without_original_paths(self):
        f = self.fixture
        reader = self.restored()
        for folder in ['original', 'packet', 'operator']:
            (f.root / folder).rename(f.root / ('retired-' + folder))
        result = verify_packet(reader, str(f.packet), str(f.ledger_path),
                               packet_seal_sha256=f.seal_sha, ledger_sha256=f.ledger_sha)
        self.assertEqual(result['status'], 'passed')

    def test_restore_never_falls_back_to_original(self):
        f = self.fixture
        reader = self.restored(remove_mapping=f.manifest)
        self.assertTrue(f.manifest.is_file())
        with self.assertRaises(KeyError):
            verify_packet(reader, str(f.packet), str(f.ledger_path),
                          packet_seal_sha256=f.seal_sha, ledger_sha256=f.ledger_sha)


if __name__ == '__main__':
    unittest.main(verbosity=2)
