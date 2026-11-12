#!/usr/bin/env python3
"""Bounded v5 format controls with read-only reuse of the sealed v3 corpus."""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT.parent / 'publication-batch-review'
PRIOR = ROOT.parent / 'publication-batch-v4-review'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


batch = load(ROOT / 'revision-v5/alarm-material-tools-v5/batch.py', 'reviewed_batch_v5')
sys.path.insert(0, str(OLD / 'controls'))
legacy = load(OLD / 'controls/test_batch_behavior.py', 'retained_batch_controls')
from fixture import Store, Study


class Reader:
    def __init__(self, *unused): self.reads = []; self.overlay = {}; self.directories = {}
    def checked(self, value):
        path = Path(value)
        if not path.is_absolute() or not (path.is_relative_to(ROOT) or path.is_relative_to(OLD) or path.is_relative_to(PRIOR)) or '..' in path.parts:
            raise ValueError('Read-only synthetic corpus/new review scope required')
        if any(p.is_symlink() for p in (path, *path.parents)): raise ValueError('Physical synthetic path required')
        return path
    def read_bytes(self, value):
        self.reads.append(str(value)); path = self.checked(value)
        return self.overlay[str(path)].read_bytes() if str(path) in self.overlay else path.read_bytes()
    def read_json(self, value): return batch.strict_json(self.read_bytes(value))
    def hash(self, value): return sha(self.read_bytes(value))
    def directory(self, value):
        path = self.directories.get(str(value), self.checked(value)); self.checked(path)
        if not path.is_dir(): raise FileNotFoundError(str(path))
        return path


reader = Reader()
compat = Study.existing(OLD / 'fixtures/compatible', batch, OLD); compat.reader = reader
rich = Study.existing(OLD / 'fixtures/rich', batch, OLD); rich.reader = reader
cause = {'path': str(OLD / 'fixtures/cause/INDEX.json'), 'sha256': reader.hash(str(OLD / 'fixtures/cause/INDEX.json'))}
legacy.Reader = Reader
legacy.ROOT = ROOT; legacy.ACTIVE = batch; legacy.RUN = ROOT / 'results/final-v2'; legacy.COMPAT = compat; legacy.RICH = rich; legacy.CAUSE = cause
legacy.MINI = None


def compiled():
    source = {'source': 'independent-contract', 'pointer': '/responsibilities'}
    paths = {'/Users/rex/candidate-v13.9/Synthetic source/unit.swift': 'a' * 64,
             '/Users/rex/baseline-v12.6-common-6/Synthetic source/unit.swift': 'a' * 64,
             '/opt/synthetic/external.swift': 'b' * 64}
    claims = []
    for index, supported in enumerate([True, False, True]):
        claims.append({'id': 'synthetic-source-' + str(index), 'clause': '  Exact synthetic source clause  ',
            'priority': 'must', 'owner': 'component', 'method': 'source', 'subject': 'synthetic-subject',
            'rule_ids': [], 'assertion_ids': [], 'files': dict(paths), 'expected': True, 'unit': 'bool',
            'provenance': dict(source, design_lock_sha256='c' * 64), 'supported': supported,
            'unsupported_reason': None if supported else 'Synthetic unsupported boundary remains'})
    return {'version': 1, 'explicit': True, 'design_lock_sha256': 'c' * 64, 'plan_sha256': 'd' * 64,
            'source_ref': source, 'claims': claims, 'issues': [{'priority': 'must', 'reason': 'Synthetic original issue'}],
            'scope': 'Arbitrary factual scope text remains complete'}


def bound_source():
    files = dict(compiled()['claims'][0]['files'])
    return {'format': 'native-ui-source-review-v1', 'design_lock_sha256': 'c' * 64,
            'observations': [{'id': 'synthetic-source-' + str(i), 'observed': observed,
                'reason': '  Exact original source observation  ', 'citations': [], 'files': dict(files),
                'claim_sha256': 'e' * 64} for i, observed in enumerate([True, False, None])],
            'scope': 'Arbitrary original bound-source factual prose remains'}


def cached_positive(self):
    """Replay all15 selection proofs against the unchanged cached packet bytes.

    The existing packet-root freshness guard is the deliberate no-write stop
    after every preflight check. The prior unmocked full build stays sealed.
    """
    base = OLD / 'results/v3/cases/test_01_complete_unmocked_all15_selection_and_packaging'
    selected = reader.read_json(str(base / 'selection/ALL-SPECS-SEAL.json'))
    for row in selected['groups']:
        derivations = reader.read_json(row['derivations']['path'])
        for item in derivations:
            item['emitter_admission'] = batch.present_value(reader.read_json(item['original']['path']), outcome=item['outer_fact_selection'] is not None)[1]
        path = self.case / (row['group'] + '-DERIVATIONS.json'); path.write_bytes(batch.encoded(derivations))
        row['derivations'] = {'path': str(path), 'sha256': reader.hash(str(path))}
    selected['code_pins'] = batch.code_pins()
    path = self.case / 'ALL-SPECS-SEAL.json'; path.write_bytes(batch.encoded(selected))
    selected_ref = {'path': str(path), 'sha256': reader.hash(str(path))}
    packets = reader.read_json(str(base / 'ALL-PACKETS.json'))
    for row in packets['groups']:
        seal = reader.read_json(row['packet_seal']['path']); folder = Path(row['packet_seal']['path']).parent
        self.assertEqual(seal['anonymous_group'], row['group'])
        for name, wanted in seal['files'].items(): self.assertEqual(reader.hash(str(folder / name)), wanted)
    before = len(reader.reads)
    with self.assertRaisesRegex(ValueError, 'Fresh physical output directory'):
        batch.package_selected(rich.root, reader, selected_ref, base / 'packets', self.case / 'no-write-operator')
    reread = set(reader.reads[before:])
    self.assertTrue(all(row['spec']['path'] in reread and row['derivations']['path'] in reread for row in selected['groups']))
    self.assertFalse((self.case / 'no-write-operator').exists())
    self.observe('readonly all15 replay', {'groups': 15, 'cached_packet_bytes_verified': True,
        'all_raw_derived_spec_document_proofs_replayed': True, 'new_packets_written': False,
        'prior_unmocked_full_build_freeze': '704d360588ae6b22f36ff3852bb1f5fec516bd82375e51b16beba933ea940d84'})


def missing_event(self):
    events = compat.run / 'events'; target = next(ref for ref in compat.events if
        (lambda e: e['kind']=='request_enqueued' and e['task']=='T1' and e['arm']=='A' and e['action']=='final')(reader.read_json(ref['path'])))
    physical = PRIOR / 'results/cases/test_05_missing_pinned_public_event_cannot_silently_drop_a_request/missing-event-tree'
    # Reuse the retained small negative namespace read-only. This saves 49
    # duplicate files while preserving a genuine filesystem directory reader.
    self.assertEqual({p.name for p in physical.iterdir()}, {p.name for p in events.iterdir() if str(p) != target['path']})
    for path in physical.iterdir(): self.assertEqual(path.read_bytes(), (events / path.name).read_bytes())
    reader.directories[str(events)] = physical
    try: self.rejected(lambda: self.prepare(compat), 'missing immutable event via separate physical overlay')
    finally: del reader.directories[str(events)]


def changed_claim(self):
    original = compat.private_claims[('T1', 'A', 'ios')]['path']; value = reader.read_json(original)
    value['record'] = str(Path(compat.terminal['T1/A/ios']['outcome']['path']).parent)
    path = self.case / 'CHANGED-CLAIM.json'; path.write_bytes(batch.encoded(value)); reader.overlay[original] = path
    try: self.rejected(self.group(compat).prepare, 'changed immutable claim via separate byte overlay')
    finally: del reader.overlay[original]


legacy.Cases.test_01_complete_unmocked_all15_selection_and_packaging = cached_positive
legacy.Cases.test_05_missing_pinned_public_event_cannot_silently_drop_a_request = missing_event
legacy.Cases.test_06_changed_private_claim_pin_cannot_hide_original_failure = changed_claim
old_teardown = legacy.Cases.tearDown
def bounded_teardown(self):
    old_teardown(self)
    self.assertLessEqual(sum(1 for p in ROOT.rglob('*') if p.is_file()), 400, 'Additional review file bound')
legacy.Cases.tearDown = bounded_teardown


class V5Cases(legacy.Cases):
    def test_18_repinned_derived_fact_still_cannot_bypass_original_proof(self):
        row = reader.read_json(str(OLD / 'results/derivation-v3/DERIVATIONS.json'))[0]
        row['emitter_admission'] = batch.present_value(reader.read_json(row['original']['path']), outcome=row['outer_fact_selection'] is not None)[1]
        (self.case / 'DERIVATION.json').write_bytes(batch.encoded(row))
        with self.assertRaisesRegex(ValueError, 'Exact raw-to-derived presentation proof differs'):
            batch.verify_derivation(reader, row)

    def test_19_uuid_attachment_and_workflow_queue_are_selected_whole(self):
        store = Store(self.case, batch); service = self.case / 'service'
        uuid_name = '11111111-2222-4333-8444-555555555555.json'
        original = batch.strict_json(b'{"schema_version":2,"rows":[{"status":"F","expected":9007199254740993.0,"actual":1e-999},{"status":"P","actual":true},{"status":"U","actual":null}],"snapshots":[{"index":0,"screenshot_attachment":"synthetic-shot","nodes":[{"text":"  exact  ","frame":{"height":44}}]}],"issues":["Synthetic original attachment issue"]}')
        attachment = store.put(service / 'capture/native/attachments' / uuid_name, original)
        queue = {'version': 1, 'generation': 2, 'repair_jobs': [{'status': 'F', 'expected': 48, 'actual': 44}, {'status': 'U', 'actual': None}], 'completion': None}
        state = store.put(service / 'workflow-state.json', queue)
        for name in ['workflow-context.json', 'capture/native/coverage-domain-input.json', 'capture/native/coverage-domain-binding.json']:
            store.put(service / name, {'synthetic_provenance_only': True, 'path': '/Users/rex/candidate-v13.9/private-control'})
        responsibility = compiled(); bound = bound_source()
        store.put(service / 'evidence-responsibility.json', responsibility)
        store.put(service / 'report.json', bound)
        inventory = store.put(self.case / 'INVENTORY.json', {str(p): sha(p.read_bytes()) for p in service.rglob('*') if p.is_file()})
        outcome = store.put(self.case / 'OUTCOME.json', {'profile': 'ios', 'action': 'diagnostic', 'exit_code': 1, 'accepted': False,
            'inventory': inventory, 'service_output': str(service)})
        group = self.group(compat); cap = compat.capsules[('T1', 'A', 'initial')][0]
        source = Path(compat.capsules[('T1', 'A', 'initial')][1]['path']).parent / 'files/0/unit.txt'; expected = cap['files']['0/unit.txt']
        group.operation(outcome, 'attachment', cap, compat.configs[('T1', 'A', 'ios')],
            {('0/unit.txt', expected['sha256'], expected['bytes']): source}, 'worker_public')
        by_name = {d['anonymous_relative']: d for d in group.documents}
        selected = 'episodes/attachment/ios/reports/capture/native/attachments/' + uuid_name
        self.assertIn(selected, by_name); self.assertEqual(reader.read_json(by_name[selected]['original']['path']), original)
        selected_state = 'episodes/attachment/ios/reports/workflow-state.json'
        self.assertEqual(reader.read_json(by_name[selected_state]['original']['path']), queue)
        self.assertFalse(any('workflow-context' in name or 'coverage-domain-input' in name or 'coverage-domain-binding' in name for name in by_name))
        spec = {'version': 1, 'kind': 'explicit-anonymous-alarm-material-spec', 'anonymous_group': 'Case01-X',
            'first_cause_barrier': cause, 'documents': group.documents, 'anonymous_description': group.description,
            'instructions': batch.ref(reader, rich.root / 'business-quality-tools/ALARM-INSTRUCTIONS-v1.md'),
            'grade_template': batch.ref(reader, rich.root / 'business-quality-tools/ALARM-GRADE-TEMPLATE-v1.json')}
        built = batch.build(reader, spec, self.case / 'packet', self.case / 'operator')
        self.observe('new factual attachment packet', built)
        self.assertEqual(batch.strict_json((self.case / 'packet' / selected).read_bytes()), original)
        for filename, raw_value, member in [('evidence-responsibility.json', responsibility, 'claims'), ('report.json', bound, 'observations')]:
            supplied = batch.strict_json((self.case / 'packet/episodes/attachment/ios/reports' / filename).read_bytes())
            expected_value, _proof = batch.admit_metadata_keys(raw_value)
            self.assertEqual(supplied, expected_value)
            self.assertEqual(len(supplied[member]), 3)
            self.assertTrue(all(len(row['files']) == 3 for row in supplied[member]))
            self.assertTrue(all(all(key.startswith('record-ref-') for key in row['files']) for row in supplied[member]))
        self.assertEqual([r['observed'] for r in batch.strict_json((self.case / 'packet/episodes/attachment/ios/reports/report.json').read_bytes())['observations']], [True, False, None])
        self.assertTrue(any(d['anonymous_relative'].startswith('sources/v0/0/') for d in group.documents))
        for path in (self.case / 'packet').rglob('*'):
            if path.is_file(): self.assertNotIn(b'candidate-v13.9', path.read_bytes())

    def test_20_attachment_scope_and_workflow_source_contract_are_bounded(self):
        for path in ['native/attachments/observer-result.json', 'capture/native/attachments/11111111-2222-4333-8444-555555555555.json']:
            self.assertEqual(batch.inventory_kind(path), 'report')
        for path in ['other/11111111-2222-4333-8444-555555555555.json', 'capture/native/attachments/nested/file.json',
                     'capture/native/attachments/../file.json', '/native/attachments/file.json', 'native\\attachments\\file.json']:
            with self.assertRaises(ValueError): batch.inventory_kind(path)
        self.assertEqual(batch.inventory_kind('capture/native/attachments/manifest.json'), 'control')
        value = {'repair_jobs': [{'status': 'F', 'expected': 48, 'actual': 44}, {'status': 'P', 'actual': True}, {'status': 'U', 'actual': None}],
                 'scope': 'Synthetic queue claim remains complete'}
        for name in ['cycle-payload.json','handoff.json','workflow-state.json','repair-task.json','patch-retest.json','workflow-final-state.json','capture-validity.json']:
            self.assertEqual(batch.inventory_kind(name), 'report')
            presented, admission = batch.present_value(value)
            neutral, _ = batch.m.neutralize(presented)
            self.assertEqual(neutral, value); self.assertEqual(admission['omitted_top_level'], {})

    def test_21_v4_reproductions_and_exact_typed_composition(self):
        for name, value, member in [('compiled', compiled(), 'claims'), ('bound-source', bound_source(), 'observations')]:
            raw = batch.encoded(value); path = ROOT / 'reproductions' / (name + '.json'); path.write_bytes(raw)
            with self.assertRaises(ValueError): load_old.m.neutralize(value)
            before = copy.deepcopy(value); admitted, proof = batch.admit_metadata_keys(value)
            self.assertEqual(value, before)
            expected = copy.deepcopy(value)
            for row in expected[member]: row['files'] = {'record-ref-' + sha(k.encode()): v for k, v in row['files'].items()}
            self.assertEqual(admitted, expected)
            self.assertEqual(len(proof), 3)
            self.assertEqual([p['pointer'] for p in proof], ['/' + member + '/' + str(i) + '/files' for i in range(3)])
            self.assertTrue(all(len(p['entries']) == 3 for p in proof))
            projected, _ = batch.m.neutralize(admitted)
            self.assertEqual(projected, expected); self.assertEqual(path.read_bytes(), raw)
            arbitrary = {next(iter(value[member][0]['files'])): 'sources/v999/0/unavailable.swift'}
            projected, _ = batch.m.neutralize(admitted, arbitrary)
            self.assertEqual(projected, expected, 'Caller scalar aliases cannot choose metadata map keys')
            self.observe(name, {'v4_rejected': True, 'v5_all_fields_values_preserved_except_exact_keys': True, 'map_proof': proof})

    def test_22_file_map_values_are_exact_sha_strings(self):
        for invalid in [True, None, 4, 'A' * 64, 'a' * 63, {'status': 'F'}, ['a' * 64]]:
            value = compiled(); value['claims'][0]['files'] = {'/Users/rex/synthetic/file.swift': invalid}
            with self.subTest(value=invalid), self.assertRaisesRegex(ValueError, 'file SHA value'): batch.present_value(value)

    def test_23_unsafe_or_already_aliased_map_keys_fail(self):
        for key in ['relative/file.swift', '/', '/Users/rex//file.swift', '/Users/rex/../file.swift', '/Users/rex/file\\name',
                    '/Users/rex/file\nname', 'record-ref-' + 'f' * 64]:
            value = compiled(); value['claims'][0]['files'] = {key: 'a' * 64}
            with self.subTest(key=repr(key)), self.assertRaisesRegex(ValueError, 'Canonical original'): batch.present_value(value)

    def test_24_collision_cannot_merge_entries(self):
        value = compiled(); original = copy.deepcopy(value)
        with mock.patch.object(batch, 'metadata_file_key', return_value='record-ref-' + '0' * 64):
            with self.assertRaisesRegex(ValueError, 'collision; no file-map merge'): batch.present_value(value)
        self.assertEqual(value, original)

    def test_25_unknown_root_or_row_schemas_cannot_borrow_key_permission(self):
        values = []
        x = compiled(); x['extra_facts'] = ['must remain']; values.append(x)
        x = compiled(); x['version'] = 2; values.append(x)
        x = compiled(); x['version'] = True; values.append(x)
        x = compiled(); x['claims'][0]['actual'] = {'status': 'F'}; values.append(x)
        x = bound_source(); x['observations'][0]['status'] = 'F'; values.append(x)
        x = bound_source(); x['format'] = 'unfamiliar-bound-source-v2'; values.append(x)
        x = {'version': 1, 'claims': compiled()['claims']}; values.append(x)
        for index, value in enumerate(values):
            before = copy.deepcopy(value)
            with self.subTest(case=index), self.assertRaises(ValueError): batch.present_value(value)
            self.assertEqual(value, before)

    def test_26_protected_ancestors_are_never_key_aliased(self):
        for key in ['actual', 'expected', 'Meas_ured', 'renderedValue', 'observed', 'payload']:
            value = {key: compiled()}; before = copy.deepcopy(value)
            with self.subTest(ancestor=key), self.assertRaises(ValueError): batch.present_value(value)
            self.assertEqual(value, before)

    def test_27_source_native_and_unknown_key_maps_stay_outside_boundary(self):
        for root in ['source_hashes', 'native', 'files', 'rows', 'claims']:
            value = {root: {'/opt/synthetic/source.swift': 'a' * 64}}
            with self.subTest(root=root), self.assertRaisesRegex(ValueError, 'Unreviewed path-keyed'): batch.present_value(value)
        ordinary = {'files': {'0/source.swift': 'a' * 64}, 'rows': [{'status': 'F', 'actual': 44, 'expected': 48}]}
        presented, admission = batch.present_value(ordinary)
        self.assertEqual(presented, ordinary); self.assertEqual(admission['metadata_key_maps'], [])

    def test_28_forged_key_proof_or_derived_alias_cannot_replay(self):
        store = Store(self.case, batch); raw = store.put(self.case / 'RAW.json', compiled())
        presented, admission = batch.present_value(reader.read_json(raw['path']))
        neutral, projection = batch.m.neutralize(presented)
        row = {'original': raw, 'derived': store.put(self.case / 'DERIVED.json', neutral), 'anonymous_relative': 'reports/compiled.json',
               'projection': projection, 'emitter_admission': admission, 'outer_fact_selection': None}
        batch.verify_derivation(reader, row)
        for field, replacement in [('anonymous_key', 'sources/v0/0/forged.swift'), ('original_key', '/opt/synthetic/other.swift'), ('file_sha256', 'f' * 64)]:
            changed = copy.deepcopy(row); changed['emitter_admission']['metadata_key_maps'][0]['entries'][0][field] = replacement
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Source-schema admission proof differs'): batch.verify_derivation(reader, changed)
        changed = copy.deepcopy(row); changed['emitter_admission']['metadata_key_maps'][0]['pointer'] = '/expected/files'
        with self.assertRaisesRegex(ValueError, 'Source-schema admission proof differs'): batch.verify_derivation(reader, changed)
        forged = copy.deepcopy(neutral); files = forged['claims'][0]['files']; files['sources/v0/0/forged.swift'] = files.pop(next(iter(files)))
        changed = copy.deepcopy(row); changed['derived'] = store.put(self.case / 'FORGED-DERIVED.json', forged)
        with self.assertRaisesRegex(ValueError, 'Exact raw-to-derived presentation proof differs'): batch.verify_derivation(reader, changed)
        # Repin every downstream digest/projection and the claimed key proof.
        # The immutable raw input still determines the only admissible result.
        changed['projection'] = batch.m.neutralize(forged)[1]
        changed['emitter_admission']['admitted_value_sha256'] = batch.m.projection.digest(forged)
        changed['emitter_admission']['selected_value_sha256'] = batch.m.projection.digest(forged)
        claimed = changed['emitter_admission']['metadata_key_maps'][0]
        claimed['entries'][0]['anonymous_key'] = 'sources/v0/0/forged.swift'
        claimed['admitted_map_sha256'] = batch.m.projection.digest(files)
        with self.assertRaisesRegex(ValueError, 'Source-schema admission proof differs'): batch.verify_derivation(reader, changed)
        (self.case / 'FULLY-REPINNED-FORGED-PROOF.json').write_bytes(batch.encoded(changed))
        self.observe('valid deterministic proof and all repinned forgeries rejected', row)

    def test_29_file_sha_changes_remain_visible(self):
        value = compiled(); changed = copy.deepcopy(value); key = next(iter(changed['claims'][0]['files']))
        changed['claims'][0]['files'][key] = 'f' * 64
        first, proof_a = batch.admit_metadata_keys(value); second, proof_b = batch.admit_metadata_keys(changed)
        alias = 'record-ref-' + sha(key.encode())
        self.assertEqual(first['claims'][0]['files'][alias], 'a' * 64); self.assertEqual(second['claims'][0]['files'][alias], 'f' * 64)
        self.assertNotEqual(proof_a[0]['original_map_sha256'], proof_b[0]['original_map_sha256'])
        self.assertNotEqual(proof_a[0]['admitted_map_sha256'], proof_b[0]['admitted_map_sha256'])

    def test_30_duplicate_original_json_keys_fail_before_admission(self):
        raw = b'{"files":{"/Users/rex/synthetic/file.swift":"' + b'a' * 64 + b'","/Users/rex/synthetic/file.swift":"' + b'b' * 64 + b'"}}'
        (self.case / 'DUPLICATE.json').write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON member'): batch.strict_json(raw)

    def test_31_utf8_and_full_path_identity_are_exact(self):
        files = {'/Users/rex/synthetic/e\u0301.swift': 'a' * 64, '/Users/rex/synthetic/\u00e9.swift': 'a' * 64,
                 '/Users/rex/synthetic/other/\u00e9.swift': 'a' * 64}
        value = compiled(); value['claims'][0]['files'] = files
        admitted, proof = batch.admit_metadata_keys(value)
        self.assertEqual(set(admitted['claims'][0]['files']), {'record-ref-' + sha(key.encode('utf-8')) for key in files})
        self.assertEqual(len(admitted['claims'][0]['files']), 3); self.assertEqual(len(proof[0]['entries']), 3)

    def test_32_bound_observed_values_and_unknown_metadata_are_not_dropped(self):
        value = bound_source(); before = copy.deepcopy(value)
        presented, admission = batch.present_value(value)
        self.assertEqual([row['observed'] for row in presented['observations']], [True, False, None])
        self.assertEqual([row['reason'] for row in presented['observations']], [row['reason'] for row in before['observations']])
        self.assertEqual(admission['omitted_top_level'], {}); self.assertEqual(value, before)
        bad = copy.deepcopy(value); bad['observations'][0]['observed'] = 1
        with self.assertRaisesRegex(ValueError, 'Unreviewed bound source'): batch.present_value(bad)


class Recorded(legacy.Recorded): pass


def main():
    legacy.RUN.mkdir(exist_ok=True)
    (ROOT / 'fixtures').mkdir(exist_ok=True)
    # All legacy functions/classes except present_value have byte-identical ASTs.
    old_tree = ast.parse((PRIOR / 'revision-v4/alarm-material-tools-v4/batch.py').read_bytes())
    new_tree = ast.parse((ROOT / 'revision-v5/alarm-material-tools-v5/batch.py').read_bytes())
    old_functions = {node.name: ast.dump(node, include_attributes=False) for node in old_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    new_functions = {node.name: ast.dump(node, include_attributes=False) for node in new_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert set(new_functions) == set(old_functions) | {'metadata_file_key', 'admit_metadata_keys'}
    assert all(old_functions[name] == new_functions[name] for name in old_functions if name != 'present_value')
    for path in (OLD / 'fixtures/rich').rglob('original-inventory.json'):
        service = path.parent / 'service'
        for name in reader.read_json(str(path)):
            relative = Path(name).relative_to(service).as_posix()
            old = load_old.inventory_kind(relative)
            assert batch.inventory_kind(relative) == old
    result = unittest.TextTestRunner(verbosity=2, resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(V5Cases))
    report = {'version': 1, 'tests_run': result.testsRun, 'passed': result.testsRun-len(result.failures)-len(result.errors),
        'failures': len(result.failures), 'errors': len(result.errors), 'controls': result.rows,
        'batch_sha256': sha((ROOT/'revision-v5/alarm-material-tools-v5/batch.py').read_bytes()),
        'schema_sha256': batch.EMITTER_SCHEMA_SHA, 'control_sha256': sha(Path(__file__).read_bytes()),
        'prior_18_control_freeze': '704d360588ae6b22f36ff3852bb1f5fec516bd82375e51b16beba933ea940d84',
        'legacy_functions_unchanged_except_present_value': True, 'legacy_inventory_classifications_unchanged': True,
        'positive_replay_scope': 'Real all15 preflight/proof replay and cached packet SHA checks; existing packet-root freshness deliberately stops writes. Original v3 unmocked full all15 build remains frozen.',
        'readonly_corpus': str(OLD), 'prior_v4_freeze': '9c44f2a1ab8329514407528d5f77f77d769fffec9db186234ac509b90454ed33',
        'actual_bodies_read': False}
    (legacy.RUN/'RESULT.json').write_bytes(batch.encoded(report))
    print(json.dumps({key:report[key] for key in ['tests_run','passed','failures','errors','batch_sha256','schema_sha256']}))


load_old = load(PRIOR / 'revision-v4/alarm-material-tools-v4/batch.py', 'old_v4_reference')
if __name__ == '__main__': main()
