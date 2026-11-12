#!/usr/bin/env python3
"""One shared bounded synthetic all15 fixture plus focused batch controls."""
import contextlib
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import traceback
import unittest
from unittest import mock

from fixture import Reader, Store, Study, cause, sha, PNG


ROOT = Path(__file__).resolve().parent.parent
ACTIVE = RUN = RICH = COMPAT = CAUSE = MINI = None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class Cases(unittest.TestCase):
    def setUp(self):
        self.case = RUN / 'cases' / self._testMethodName; self.case.mkdir(parents=True); self.log = []

    def tearDown(self):
        (self.case / 'OBSERVATIONS.json').write_bytes(ACTIVE.encoded(self.log))
        count = sum(1 for p in ROOT.rglob('*') if p.is_file())
        if count >= 2000: self.fail('Bounded review exceeded 2000 files: ' + str(count))

    def observe(self, label, value): self.log.append({'label': label, 'value': value})

    def rejected(self, callback, label):
        try: result = callback()
        except Exception as error:
            self.observe(label, {'rejected': True, 'type': type(error).__name__, 'message': str(error)}); return
        self.observe(label, {'rejected': False, 'result': result}); self.fail('Expected rejection: ' + label)

    def prepare(self, fixture, name='selection'):
        ACTIVE.MAP_SEAL_SHA = fixture.mapping_seal['sha256']
        return ACTIVE.prepare(fixture.root, fixture.reader, CAUSE, fixture.snapshot, fixture.native_result,
                              self.case / name, self.case / (name + '-intermediates'))

    def group(self, fixture, group='Case01-X', arm='A'):
        work = self.case / 'work'; work.mkdir()
        snap = fixture.reader.read_json(fixture.snapshot['path']); proof = fixture.reader.read_json(fixture.native_result['path'])
        events = [fixture.reader.read_json(ref['path']) for ref in fixture.events]
        return ACTIVE.Group(fixture.root, fixture.reader, group, 'T1', arm, {}, events, snap, proof['files_read'], work)

    @contextlib.contextmanager
    def altered(self, path, raw):
        before = path.read_bytes(); (self.case / 'BEFORE.bin').write_bytes(before); (self.case / 'AFTER.bin').write_bytes(raw)
        path.write_bytes(raw)
        try: yield
        finally: path.write_bytes(before)

    def test_01_complete_unmocked_all15_selection_and_packaging(self):
        selected = self.prepare(RICH)
        body = RICH.reader.read_json(selected['path']); self.assertEqual(len(body['groups']), 15)
        if not hasattr(ACTIVE, 'package_selected'):
            self.fail('Prototype does not expose a checked all15 packaging API')
        result = ACTIVE.package_selected(RICH.root, RICH.reader, selected, self.case / 'packets', self.case / 'packaging', self.case / 'ALL-PACKETS.json')
        self.observe('result', {'groups': len(result['groups']), 'selection_seal': selected, 'phase2_dispatched': result['phase2_dispatched']})
        self.assertEqual(len(result['groups']), 15); self.assertFalse(result['phase2_dispatched'])
        for row in result['groups']:
            seal = RICH.reader.read_json(row['packet_seal']['path']); self.assertEqual(seal['anonymous_group'], row['group'])
            directory = Path(row['packet_seal']['path']).parent
            for name, pin in seal['files'].items():
                raw = (directory / name).read_bytes(); self.assertEqual(sha(raw), pin)
                self.assertNotIn(b'synthetic_control_cost_marker', raw)
                self.assertFalse(ACTIVE.m.projection.LEAK.search(raw.decode('latin-1')))
                self.assertEqual((directory / name).stat().st_mode & 0o222, 0)
                if name.endswith('automatic.json'):
                    report = ACTIVE.strict_json(raw)
                    self.assertEqual([item['status'] for item in report['rows']], ['F', 'P', 'U'])
                    self.assertEqual(str(report['rows'][0]['expected']), '9007199254740993.0')
                    self.assertEqual(str(report['rows'][0]['actual']), '1E-999')
                if name.endswith('/observation.json'):
                    report = ACTIVE.strict_json(raw); self.assertNotIn('operations', report)
                    self.assertEqual(report['issues'], ['Synthetic measurement limitation'])
                    for snapshot in report['snapshots']:
                        self.assertTrue((directory / Path(name).parent / snapshot['screenshot']).is_file())
                if name.endswith('cycle.json'):
                    self.assertNotIn('trace', ACTIVE.strict_json(raw))
        x = RICH.reader.read_json(self.case / 'selection/Case01-X/SPEC.json')
        self.assertEqual(len(x['anonymous_description']['versions']), 2)
        submissions = [d for d in x['documents'] if d['anonymous_relative'].endswith('/original-submission.json')]
        self.assertEqual(len(submissions), 1)
        submitted = RICH.reader.read_json(submissions[0]['original']['path'])
        self.assertEqual(submitted['rows'][0]['actual'], '  Synthetic  ')
        self.assertTrue((self.case / 'packets/Case01-X' / submitted['rows'][0]['image_ref']).is_file())
        self.assertTrue((self.case / 'packets/Case01-X' / submitted['rows'][0]['source_ref']).is_file())
        self.assertTrue(any(d['anonymous_relative'].endswith('/environment-check.json') for d in x['documents']))
        self.assertTrue(any(d['anonymous_relative'].endswith('/execution-coverage.json') for d in x['documents']))
        initial = RICH.reader.read_json(self.case / 'selection/Case01-I/SPEC.json')
        self.assertFalse(any(d['anonymous_relative'] == 'worker/self-claim.json' for d in initial['documents']))
        origins = [e.get('attempt_origins', []) for e in x['anonymous_description']['episodes']]
        self.assertTrue(any('original' in item for item in origins)); self.assertTrue(any('effective' in item for item in origins))
        y = RICH.reader.read_json(self.case / 'selection/Case01-Y/SPEC.json')
        self.assertTrue(any('licensed-entry-failure' in e.get('attempt_origins', []) for e in y['anonymous_description']['episodes']))
        for row in body['groups']:
            derivations = RICH.reader.read_json(row['derivations']['path'])
            self.assertTrue(derivations)
            self.assertTrue(all('original' in d and 'emitter_admission' in d for d in derivations))

    def test_02_partial_cause_stops_before_native_or_mapping_reads(self):
        reader = Reader(ROOT, ACTIVE); bad = self.case / 'CAUSE.json'
        bad.write_bytes(ACTIVE.encoded({'version': 1, 'kind': 'global-independent-cause-grade-barrier', 'groups': []}))
        ref = {'path': str(bad), 'sha256': sha(bad.read_bytes())}
        self.rejected(lambda: ACTIVE.prepare(COMPAT.root, reader, ref, COMPAT.snapshot, COMPAT.native_result,
            self.case / 'out', self.case / 'work'), 'partial cause')
        self.assertEqual(reader.reads, [str(bad)]); self.assertFalse((self.case / 'out').exists())

    def test_03_changed_last_cause_seal_stops_before_native_reads(self):
        reader = Reader(ROOT, ACTIVE); value = reader.read_json(CAUSE['path'])
        value['groups'][-1]['seals']['J2']['sha256'] = '0' * 64
        store = Store(self.case, ACTIVE); ref = store.put(self.case / 'CAUSE.json', value); reader.reads.clear()
        self.rejected(lambda: ACTIVE.prepare(COMPAT.root, reader, ref, COMPAT.snapshot, COMPAT.native_result,
            self.case / 'out', self.case / 'work'), 'bad thirtieth seal')
        self.assertNotIn(COMPAT.snapshot['path'], reader.reads); self.assertFalse((self.case / 'out').exists())

    def test_04_wrong_native_snapshot_pin_stops_before_mapping(self):
        reader = Reader(ROOT, ACTIVE); bad = dict(COMPAT.snapshot, sha256='0' * 64)
        self.rejected(lambda: ACTIVE.prepare(COMPAT.root, reader, CAUSE, bad, COMPAT.native_result,
            self.case / 'out', self.case / 'work'), 'bad native proof pin')
        self.assertFalse(any('MAPPING.json' in p for p in reader.reads))

    def test_05_missing_pinned_public_event_cannot_silently_drop_a_request(self):
        target = next(ref for ref in COMPAT.events if (lambda e: e['kind']=='request_enqueued' and e['task']=='T1' and e['arm']=='A' and e['action']=='final')(COMPAT.reader.read_json(ref['path'])))
        path = Path(target['path']); removed = self.case / 'REMOVED-EVENT.json'; path.rename(removed)
        try: self.rejected(lambda: self.prepare(COMPAT), 'deleted pinned final enqueue')
        finally: removed.rename(path)

    def test_06_changed_private_claim_pin_cannot_hide_original_failure(self):
        claim_ref = COMPAT.private_claims[('T1', 'A', 'ios')]; path = Path(claim_ref['path'])
        value = COMPAT.reader.read_json(str(path)); value['record'] = str(Path(COMPAT.terminal['T1/A/ios']['outcome']['path']).parent)
        with self.altered(path, ACTIVE.encoded(value)):
            group = self.group(COMPAT)
            self.rejected(group.prepare, 'changed original private claim')

    def test_07_source_recovery_never_substitutes_current_bytes_for_missing_version(self):
        group = self.group(COMPAT); raw = b'Synthetic unavailable intermediate source.\n'
        files = {'0/unit.txt': {'sha256': sha(raw), 'bytes': len(raw)}}
        required = {'files': files, 'content_sha256': sha(ACTIVE.json_text(files, sort_keys=True).encode())}
        current = Path(COMPAT.capsules[('T1', 'A', 'final-source')][1]['path']).parent / 'files/0/unit.txt'
        actual = current.read_bytes(); candidates = {('0/unit.txt', sha(actual), len(actual)): current}
        group.sources(required, [str(COMPAT.root / 'source-spaces/T1/A')], candidates)
        self.assertEqual(group.documents, []); missing = group.description['versions'][0]['missing_original_members']
        self.assertEqual(missing, [{'relative': '0/unit.txt', 'sha256': sha(raw), 'bytes': len(raw)}])

    def test_08_identical_source_bytes_keep_separate_original_workspace_aliases(self):
        group = self.group(COMPAT); cap = COMPAT.capsules[('T1', 'A', 'initial')][0]
        source = Path(COMPAT.capsules[('T1', 'A', 'initial')][1]['path']).parent / 'files/0/unit.txt'
        row = cap['files']['0/unit.txt']; candidates = {('0/unit.txt', row['sha256'], row['bytes']): source}
        roots = [str(COMPAT.root / 'source-spaces/T1/' / arm) for arm in ('A', 'B')]
        for root in roots: group.sources(cap, [root], candidates)
        for root in roots: self.assertEqual(group.aliases[cap['content_sha256']][root + '/unit.txt'], 'sources/v0/0/unit.txt')
        self.assertEqual(len(group.documents), 1)

    def test_09_known_emitter_trace_and_counters_are_admitted_with_proof(self):
        group = self.group(COMPAT); store = Store(self.case, ACTIVE)
        value = {'trace': ['route_findings', 'admission'], 'operations': {'counts': {'capture': 1},
            'seconds': {'capture': 0.5}, 'scope': 'Nested inclusive operation walls, not additive elapsed time'},
            'rows': [{'status': 'F', 'actual': 44, 'expected': 48}]}
        ref = store.put(self.case / 'original.json', value)
        group.json_document(ref, 'reports/synthetic.json', {'kind': 'original-report'})
        result = group.reader.read_json(group.documents[0]['original']['path'])
        self.assertEqual(result, {'rows': value['rows']})
        admission = group.derivations[0].get('emitter_admission')
        self.assertIsNotNone(admission); self.assertEqual(set(admission['omitted_top_level']), {'trace', 'operations'})

    def test_10_unknown_emitter_trace_does_not_disappear(self):
        group = self.group(COMPAT); store = Store(self.case, ACTIVE)
        ref = store.put(self.case / 'original.json', {'trace': ['Synthetic F alarm: missing value'], 'rows': []})
        self.rejected(lambda: group.json_document(ref, 'reports/test.json', {'kind': 'original-report'}), 'unknown trace fact')

    def test_11_unknown_native_counter_member_does_not_disappear(self):
        group = self.group(COMPAT); store = Store(self.case, ACTIVE)
        ref = store.put(self.case / 'original.json', {'operations': {'counts': {'synthetic_unknown': 1},
            'seconds': {'synthetic_unknown': 0.5}, 'scope': 'Nested inclusive operation walls, not additive elapsed time'}})
        self.rejected(lambda: group.json_document(ref, 'reports/test.json', {'kind': 'original-report'}), 'unknown operation schema')

    def test_12_protected_factual_path_stays_unprojectable(self):
        group = self.group(COMPAT); store = Store(self.case, ACTIVE)
        ref = store.put(self.case / 'original.json', {'actual': {'path': '/Users/rex/synthetic-rendered-value'}})
        self.rejected(lambda: group.json_document(ref, 'reports/test.json', {'kind': 'original-report'}), 'protected actual path')

    def native_case(self, missing=False, partial=False):
        store = Store(self.case, ACTIVE); native = self.case / 'capture/native'
        image = store.put(native / 'attachments/frame.png', raw=PNG)
        value = {'snapshots': [{'index': 0, 'screenshot': 'attachments/missing.png' if missing else 'attachments/frame.png'}],
                 'issues': ['Synthetic original issue'], 'status': 'U'}
        obs = None if partial else store.put(native / 'observation.json', value)
        receipt = store.put(native.parent / 'result.json', {'image_hashes': {'attachments/frame.png': image['sha256']},
            **({'observation_sha256': obs['sha256']} if obs else {})})
        outcome = {'profile': 'ios', 'action': 'diagnostic', 'exit_code': 1, 'accepted': False, 'capture': receipt}
        outcome_ref = store.put(self.case / 'outcome.json', outcome)
        cap = COMPAT.capsules[('T1', 'A', 'initial')][0]; source = Path(COMPAT.capsules[('T1', 'A', 'initial')][1]['path']).parent / 'files/0/unit.txt'
        row = cap['files']['0/unit.txt']; candidates = {('0/unit.txt', row['sha256'], row['bytes']): source}
        group = self.group(COMPAT)
        return group, lambda: group.operation(outcome_ref, 'synthetic', cap, COMPAT.configs[('T1', 'A', 'ios')], candidates, 'worker_public')

    def test_13_native_screenshot_binding_requires_a_declared_png(self):
        group, invoke = self.native_case(missing=True); self.rejected(invoke, 'unbound original screenshot path')

    def test_14_pinned_partial_png_is_kept_without_inventing_observation(self):
        group, invoke = self.native_case(partial=True); invoke()
        images = [d for d in group.documents if d['anonymous_relative'].endswith('.png')]
        self.assertEqual(len(images), 1)
        self.assertIsNone(group.description['episodes'][0]['capture']['observation'])

    def test_15_unknown_json_report_is_not_silently_filtered(self):
        store = Store(self.case, ACTIVE); service = self.case / 'service'
        report = store.put(service / 'new-alarm-kind.json', {'rows': [{'status': 'F', 'actual': False}]})
        inv = store.put(self.case / 'inventory.json', {report['path']: report['sha256']})
        outcome = store.put(self.case / 'outcome.json', {'profile': 'ios', 'action': 'diagnostic', 'inventory': inv, 'service_output': str(service)})
        group = self.group(COMPAT); cap = COMPAT.capsules[('T1', 'A', 'initial')][0]
        source = Path(COMPAT.capsules[('T1', 'A', 'initial')][1]['path']).parent / 'files/0/unit.txt'; row = cap['files']['0/unit.txt']
        self.rejected(lambda: group.operation(outcome, 'synthetic', cap, COMPAT.configs[('T1', 'A', 'ios')],
            {('0/unit.txt', row['sha256'], row['bytes']): source}, 'worker_public'), 'unknown report filename')

    def mini_selection(self, mismatch=False, changed_last=False):
        global MINI
        store = Store(self.case, ACTIVE)
        if MINI is None:
            base = ROOT / 'fixtures/miniselection'
            if base.exists():
                shared = {'path': str(base / 'DERIVATIONS.json'), 'sha256': COMPAT.reader.hash(str(base / 'DERIVATIONS.json'))}
                MINI = [{'group': 'Case0%d-%s' % (i, v), 'spec': {'path': str(base / ('Case0%d-%s.json' % (i, v))),
                         'sha256': COMPAT.reader.hash(str(base / ('Case0%d-%s.json' % (i, v))))}, 'derivations': shared}
                        for i in range(1, 6) for v in ('I', 'X', 'Y')]
        if MINI is None:
            base = ROOT / 'fixtures/miniselection'; base.mkdir()
            raw = store.put(base / 'raw.json', {'rows': [{'status': 'F', 'actual': False}]})
            derivations = store.put(base / 'DERIVATIONS.json', [])
            MINI = []
            for i in range(1, 6):
              for version in ('I', 'X', 'Y'):
                group = 'Case0%d-%s' % (i, version)
                doc = {'original': raw, 'anonymous_relative': 'reports/raw.json', 'method': 'copy'}
                spec = {'version': 1, 'kind': 'explicit-anonymous-alarm-material-spec', 'anonymous_group': group,
                    'first_cause_barrier': CAUSE, 'documents': [doc],
                    'anonymous_description': {'anonymous_group': group, 'documents': [{'path': 'reports/raw.json', 'kind': 'original-synthetic-report'}]},
                    'instructions': {'path': str(COMPAT.root / 'business-quality-tools/ALARM-INSTRUCTIONS-v1.md'), 'sha256': COMPAT.reader.hash(str(COMPAT.root / 'business-quality-tools/ALARM-INSTRUCTIONS-v1.md'))},
                    'grade_template': {'path': str(COMPAT.root / 'business-quality-tools/ALARM-GRADE-TEMPLATE-v1.json'), 'sha256': COMPAT.reader.hash(str(COMPAT.root / 'business-quality-tools/ALARM-GRADE-TEMPLATE-v1.json'))}}
                MINI.append({'group': group, 'spec': store.put(base / (group + '.json'), spec), 'derivations': derivations})
        rows = copy.deepcopy(MINI)
        index = 0 if mismatch else len(rows) - 1
        spec = ACTIVE.pinned(COMPAT.reader, rows[index]['spec'])
        if mismatch:
            spec['anonymous_group'] = 'Case02-I'; spec['anonymous_description']['anonymous_group'] = 'Case02-I'
        if changed_last: spec['documents'][0]['original']['sha256'] = '0' * 64
        rows[index]['spec'] = store.put(self.case / 'MUTATED-SPEC.json', spec)
        pins = ACTIVE.code_pins() if hasattr(ACTIVE, 'code_pins') else {}
        return store.put(self.case / 'SELECTION.json', {'version': 1, 'kind': 'all15-uniform-original-alarm-selection-seal',
            'groups': rows, 'first_cause_barrier': CAUSE, 'closed_cause_contexts': 30, 'original_root': str(COMPAT.root),
            'code_pins': pins, 'mapping_revealed_to_judges_or_model': False, 'quality_adjudicated': False})

    def package_gate(self, selected):
        calls = []
        def marker(reader, spec, output, record):
            calls.append({'group': spec['anonymous_group'], 'output': str(output)})
            raise RuntimeError('Synthetic packaging-reach marker; no packet written')
        with mock.patch.object(ACTIVE, 'build', side_effect=marker):
            if hasattr(ACTIVE, 'package_selected'):
                self.rejected(lambda: ACTIVE.package_selected(COMPAT.root, COMPAT.reader, selected, self.case / 'packets', self.case / 'packaging'), 'selection preflight')
            else:
                argv = [ACTIVE.__file__, 'build', '--root', str(COMPAT.root), '--id', self._testMethodName.replace('_', '-'),
                        '--selection-seal', selected['path'], '--selection-seal-sha256', selected['sha256']]
                with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                    self.rejected(ACTIVE.main, 'legacy selection build')
        self.observe('packaging reached', calls); self.assertEqual(calls, [], 'Packaging began before every selection was valid')

    def test_16_selection_row_and_packet_group_must_match(self): self.package_gate(self.mini_selection(mismatch=True))

    def test_17_last_selected_byte_pin_must_verify_before_first_packet(self): self.package_gate(self.mini_selection(changed_last=True))


class Recorded(unittest.TextTestResult):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.rows = []
    def addSuccess(self, test): super().addSuccess(test); self.rows.append({'test': test.id(), 'status': 'pass'})
    def addFailure(self, test, error):
        super().addFailure(test, error); self.rows.append({'test': test.id(), 'status': 'fail', 'traceback': ''.join(traceback.format_exception(*error))})
    def addError(self, test, error):
        super().addError(test, error); self.rows.append({'test': test.id(), 'status': 'error', 'traceback': ''.join(traceback.format_exception(*error))})


def main():
    global ACTIVE, RUN, RICH, COMPAT, CAUSE
    parser = argparse.ArgumentParser(); parser.add_argument('--candidate-only', action='store_true'); args = parser.parse_args()
    candidate = load(ROOT / 'revision-v3/alarm-material-tools-v3/batch.py', 'review_candidate_batch')
    sys.path.insert(0, str(ROOT / 'snapshots/driver-v1'))
    original = load(ROOT / 'snapshots/driver-v1/batch.py', 'review_original_batch')
    fixture_root = ROOT / 'fixtures'; fixture_root.mkdir(exist_ok=True)
    CAUSE = {'path': str(fixture_root / 'cause/INDEX.json'), 'sha256': sha((fixture_root / 'cause/INDEX.json').read_bytes())} if (fixture_root / 'cause/INDEX.json').exists() else cause(fixture_root / 'cause', candidate)
    RICH = Study.existing(fixture_root / 'rich', candidate, ROOT, True) if (fixture_root / 'rich').exists() else Study(fixture_root / 'rich', candidate, ROOT, True)
    COMPAT = Study.existing(fixture_root / 'compatible', candidate, ROOT, False) if (fixture_root / 'compatible').exists() else Study(fixture_root / 'compatible', candidate, ROOT, False)
    all_results = {}
    for name, module in ([('v3', candidate)] if args.candidate_only else [('v1', original), ('v3', candidate)]):
        ACTIVE = module; RUN = ROOT / 'results' / name; RUN.mkdir()
        result = unittest.TextTestRunner(verbosity=2, resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
        report = {'version': 1, 'synthetic_only': True, 'tests_run': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors), 'failures': len(result.failures), 'errors': len(result.errors),
            'module_sha256': sha(Path(module.__file__).read_bytes()), 'control_sha256': sha(Path(__file__).read_bytes()),
            'fixture_generator_sha256': sha((ROOT / 'controls/fixture.py').read_bytes()), 'controls': result.rows,
            'fixture_mapping_pin_substitution': True, 'native_result_is_synthetic_unit_input': True,
            'full_positive_uses_real_presentation_and_packet_verifiers': True}
        (RUN / 'RESULT.json').write_bytes(candidate.encoded(report)); all_results[name] = {key: report[key] for key in ('tests_run','passed','failures','errors')}
    count = sum(1 for p in ROOT.rglob('*') if p.is_file()); assert count < 2000
    print(json.dumps({'results': all_results, 'retained_file_count': count}))


if __name__ == '__main__': main()
