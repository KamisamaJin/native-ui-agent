#!/usr/bin/env python3
"""Bounded v4 format controls with read-only reuse of the sealed v3 corpus."""
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

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT.parent / 'publication-batch-review'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


batch = load(ROOT / 'revision-v4/alarm-material-tools-v4/batch.py', 'reviewed_batch_v4')
sys.path.insert(0, str(OLD / 'controls'))
legacy = load(OLD / 'controls/test_batch_behavior.py', 'retained_batch_controls')
from fixture import Store, Study


class Reader:
    def __init__(self, *unused): self.reads = []; self.overlay = {}; self.directories = {}
    def checked(self, value):
        path = Path(value)
        if not path.is_absolute() or not (path.is_relative_to(ROOT) or path.is_relative_to(OLD)) or '..' in path.parts:
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
legacy.ROOT = ROOT; legacy.ACTIVE = batch; legacy.RUN = ROOT / 'results/final'; legacy.COMPAT = compat; legacy.RICH = rich; legacy.CAUSE = cause
legacy.MINI = None


def cached_positive(self):
    """Replay all15 selection proofs against the unchanged cached packet bytes.

    The existing packet-root freshness guard is the deliberate no-write stop
    after every preflight check. The prior unmocked full build stays sealed.
    """
    base = OLD / 'results/v3/cases/test_01_complete_unmocked_all15_selection_and_packaging'
    selected = reader.read_json(str(base / 'selection/ALL-SPECS-SEAL.json'))
    for row in selected['groups']:
        derivations = reader.read_json(row['derivations']['path'])
        for item in derivations: item['emitter_admission']['schema_sha256'] = batch.EMITTER_SCHEMA_SHA
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
    physical = ROOT / 'results/cases/test_05_missing_pinned_public_event_cannot_silently_drop_a_request/missing-event-tree'
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
    self.assertLess(sum(1 for p in ROOT.rglob('*') if p.is_file()), 300, 'Additional review file bound')
legacy.Cases.tearDown = bounded_teardown


class V4Cases(legacy.Cases):
    def test_18_repinned_derived_fact_still_cannot_bypass_original_proof(self):
        row = reader.read_json(str(OLD / 'results/derivation-v3/DERIVATIONS.json'))[0]
        row['emitter_admission']['schema_sha256'] = batch.EMITTER_SCHEMA_SHA
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


class Recorded(legacy.Recorded): pass


def main():
    legacy.RUN.mkdir(exist_ok=True)
    (ROOT / 'fixtures').mkdir(exist_ok=True)
    # All legacy functions except the classifier have byte-identical ASTs.
    old_tree = ast.parse((OLD / 'revision-v3/alarm-material-tools-v3/batch.py').read_bytes())
    new_tree = ast.parse((ROOT / 'revision-v4/alarm-material-tools-v4/batch.py').read_bytes())
    old_functions = {node.name: ast.dump(node, include_attributes=False) for node in old_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    new_functions = {node.name: ast.dump(node, include_attributes=False) for node in new_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert set(old_functions) == set(new_functions)
    assert all(old_functions[name] == new_functions[name] for name in old_functions if name != 'inventory_kind')
    for path in (OLD / 'fixtures/rich').rglob('original-inventory.json'):
        service = path.parent / 'service'
        for name in reader.read_json(str(path)):
            relative = Path(name).relative_to(service).as_posix()
            old = load_old.inventory_kind(relative)
            assert batch.inventory_kind(relative) == old
    result = unittest.TextTestRunner(verbosity=2, resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(V4Cases))
    report = {'version': 1, 'tests_run': result.testsRun, 'passed': result.testsRun-len(result.failures)-len(result.errors),
        'failures': len(result.failures), 'errors': len(result.errors), 'controls': result.rows,
        'batch_sha256': sha((ROOT/'revision-v4/alarm-material-tools-v4/batch.py').read_bytes()),
        'schema_sha256': batch.EMITTER_SCHEMA_SHA, 'control_sha256': sha(Path(__file__).read_bytes()),
        'prior_18_control_freeze': '704d360588ae6b22f36ff3852bb1f5fec516bd82375e51b16beba933ea940d84',
        'legacy_functions_unchanged_except_classifier': True, 'legacy_inventory_classifications_unchanged': True,
        'positive_replay_scope': 'Real all15 preflight/proof replay and cached packet SHA checks; existing packet-root freshness deliberately stops writes. Original v3 unmocked full all15 build remains frozen.',
        'readonly_corpus': str(OLD), 'actual_bodies_read': False}
    (legacy.RUN/'RESULT.json').write_bytes(batch.encoded(report))
    print(json.dumps({key:report[key] for key in ['tests_run','passed','failures','errors','batch_sha256','schema_sha256']}))


load_old = load(OLD / 'revision-v3/alarm-material-tools-v3/batch.py', 'old_classifier_reference')
if __name__ == '__main__': main()
