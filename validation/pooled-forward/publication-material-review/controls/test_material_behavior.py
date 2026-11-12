#!/usr/bin/env python3
"""Independent bounded synthetic material-helper controls; no product inputs."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import unittest


ROOT = Path(__file__).resolve().parent.parent
RUN = MODULE = material = None


def sha(raw): return hashlib.sha256(raw).hexdigest()


def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n').encode()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


class Behavior(unittest.TestCase):
    def setUp(self):
        self.case = RUN / 'cases' / self._testMethodName; self.case.mkdir(parents=True); self.observations = []

    def tearDown(self): (self.case / 'OBSERVATIONS.json').write_bytes(encoded(self.observations))

    def source(self, value):
        (self.case / ('INPUT-' + str(len(list(self.case.glob('INPUT-*')))) + '.json')).write_bytes(encoded(value))
        return value

    def observe(self, label, value): self.observations.append({'label': label, 'value': value})

    def reject(self, callback, label):
        try: result = callback()
        except (ValueError, TypeError, KeyError) as error:
            self.observe(label, {'rejected': True, 'type': type(error).__name__, 'message': str(error)}); return
        self.observe(label, {'rejected': False, 'result': result}); self.fail('Expected fail-closed rejection: ' + label)

    def preserve_or_reject(self, value):
        try: result, proof = material.neutralize(value)
        except ValueError as error:
            self.observe('conservative rejection', str(error)); return
        self.observe('projected', result); self.observe('proof', proof); self.assertEqual(result, value)

    def test_01_whole_reports_precise_values_text_and_orders_are_conserved(self):
        raw = b'{"assertions":[{"status":"F","expected":9007199254740993.0,"actual":1e-999},{"status":"P","actual":true},{"status":"U","actual":null}],"issues":[{"message":"Synthetic incomplete evidence","status":"U"}],"work":[{"admission":false}],"claims":[{"statement":"Synthetic complete claim"}],"new_extension":[{"status":"F","expected":"  x","actual":" x"}]}'
        (self.case / 'INPUT.json').write_bytes(raw)
        value = material.projection.strict_json(raw); before = copy.deepcopy(value); result, proof = material.neutralize(value)
        self.observe('result', result); self.assertEqual(result, before); self.assertEqual(value, before)
        self.assertEqual(material.projection.json_text(result), material.projection.json_text(before))
        self.assertEqual([r['status'] for r in result['assertions']], ['F', 'P', 'U']); self.assertFalse(proof['identity_metadata_changes'])

    def test_02_protected_fact_ancestors_fail_closed(self):
        for ancestor in ('actual', 'expected', 'measuredValues', 'rendered_text', 'observed'):
            value = self.source({'native': {ancestor: {'path': '/Users/rex/synthetic/visible-value'}}})
            self.reject(lambda value=value: material.neutralize(value), ancestor)

    def test_03_known_execution_metrics_can_be_omitted(self):
        value = self.source({'tool': 'candidate-v13.9', 'arm': 'B', 'operations': {'seconds': 9, 'count': 3},
                             'timing': {'wall_seconds': 9}, 'assertions': [{'status': 'F', 'actual': False}]})
        result, proof = material.neutralize(value); self.observe('result', result)
        self.assertEqual(result, {'assertions': value['assertions']})
        self.assertEqual(set(proof['omitted_top_level']), {'tool', 'arm', 'operations', 'timing'})

    def test_04_structured_factual_operations_remain_whole(self):
        value = self.source({'operations': [{'name': 'submit', 'status': 'F', 'expected': True, 'actual': False}],
                             'issues': [{'status': 'U', 'message': 'Synthetic issue'}]})
        result, _ = material.neutralize(value); self.assertEqual(result, value)

    def test_05_scalar_operation_claim_cannot_disappear(self):
        value = self.source({'operations': 'Synthetic alarm: expected 48, observed 44; F', 'assertions': []})
        self.preserve_or_reject(value)

    def test_06_opaque_output_claim_cannot_disappear_under_execution_keys(self):
        value = self.source({'operations': {'output': 'Synthetic F claim: expected 48, actual 44'}, 'assertions': []})
        self.preserve_or_reject(value)

    def test_07_outcome_facts_and_legitimate_scalar_metadata_are_supported(self):
        value = self.source({'profile': 'ios', 'action': 'final', 'exit_code': 1, 'service_status': 'failed',
                             'accepted': False, 'error': {'type': 'ValueError', 'message': 'Synthetic missing evidence'},
                             'integrity': {'passed': False, 'issues': [{'status': 'U'}]},
                             'task': 'T1', 'arm': 'B', 'wall_seconds': 9,
                             'service_output': '/Users/rex/synthetic/service', 'capture': None})
        result = material.outcome_view(value); self.observe('view', result)
        self.assertEqual(result, {k: v for k, v in value.items() if k in material.OUTCOME_FIELDS})

    def test_08_unrecognized_outcome_fields_fail_closed(self):
        value = self.source({'exit_code': 1, 'new_assertions': [{'status': 'F', 'actual': False}]})
        self.reject(lambda: material.outcome_view(value), 'unknown outcome field')

    def test_09_structured_report_hidden_in_provenance_is_rejected(self):
        value = self.source({'exit_code': 1, 'config': {'assertions': [{'status': 'F', 'actual': False}]}})
        self.reject(lambda: material.outcome_view(value), 'hidden structured factual data')

    def test_10_unfamiliar_timing_prose_is_not_silently_omitted(self):
        value = self.source({'exit_code': 1, 'wall_seconds': 'Synthetic F alarm: a field is missing'})
        self.reject(lambda: material.outcome_view(value), 'non-numeric timing metadata')

    def test_11_reference_path_cannot_be_arbitrary_factual_prose(self):
        value = self.source({'exit_code': 1, 'capture': {'path': 'Synthetic F alarm: expected 48 actual 44', 'sha256': '0' * 64}})
        self.reject(lambda: material.outcome_view(value), 'non-path reference payload')

    def test_12_reference_aliases_and_controls_fail_closed(self):
        for path in ('/Users/rex/synthetic/../other/report.json', '/Users/rex/synthetic/report\nF: new claim'):
            value = self.source({'exit_code': 1, 'capture': {'path': path, 'sha256': '0' * 64}})
            self.reject(lambda value=value: material.outcome_view(value), 'unsafe provenance path')

    def test_13_whole_acquisition_scope_claim_is_retained_by_value(self):
        value = self.source({'exit_code': 1, 'acquisition_evidence': {
            'capture_receipt': None, 'execution': None, 'native_log': None, 'observation': None,
            'scope': 'Synthetic F alarm: missing native value; expected 48 actual 44'}})
        before = copy.deepcopy(value); result = material.outcome_view(value)
        self.observe('view', result); self.assertEqual(result, before)
        result['acquisition_evidence']['scope'] = 'Changed derived object'
        self.assertEqual(value, before)

    def test_14_bounded_acquisition_references_with_empty_scope_are_supported(self):
        ref = {'path': '/Users/rex/synthetic/original.json', 'sha256': '0' * 64}
        value = self.source({'exit_code': 1, 'acquisition_evidence': {
            'capture_receipt': ref, 'execution': None, 'native_log': ref, 'observation': ref, 'scope': ''}})
        result = material.outcome_view(value); self.assertEqual(result['exit_code'], 1)
        if 'acquisition_evidence' in result:
            self.assertEqual(result['acquisition_evidence'], value['acquisition_evidence'])

    def test_15_outcome_view_owns_its_copied_fact_subtrees(self):
        value = self.source({'error': {'type': 'ValueError', 'message': 'Synthetic original'},
                             'integrity': {'passed': False, 'issues': [{'status': 'F'}]}})
        before = copy.deepcopy(value); result = material.outcome_view(value)
        result['error']['message'] = 'Changed derived output'; result['integrity']['issues'].reverse()
        result['integrity']['issues'][0]['status'] = 'P'
        self.observe('original_after_output_mutation', value); self.assertEqual(value, before)

    def test_16_whole_metadata_paths_use_exact_declared_aliases(self):
        original = '/Users/rex/Project With Spaces/한국/Main.swift'
        value = self.source({'source': {'path': original}, 'assertions': [{'status': 'F', 'actual': 44}]})
        result, proof = material.neutralize(value, {original: 'sources/v0/Main.swift'})
        self.observe('result', result); self.assertEqual(result['source']['path'], 'sources/v0/Main.swift')
        self.assertEqual(result['assertions'], value['assertions']); self.assertEqual(proof['identity_metadata_changes'][0]['original'], original)

    def test_17_narrative_paths_use_full_declared_aliases_including_spaces(self):
        original = '/Users/rex/Project With Spaces/한국/Main.swift'
        value = self.source({'reason': 'See ' + original + ':42; preserve this synthetic F claim.'})
        result, proof = material.neutralize(value, {original: 'sources/v0/Main.swift'})
        self.observe('result', result); self.observe('proof', proof)
        self.assertEqual(result['reason'], 'See sources/v0/Main.swift:42; preserve this synthetic F claim.')

    def test_18_ambiguous_unaliased_narrative_path_fails_closed(self):
        value = self.source({'reason': 'See /Users/rex/Project With Spaces/Main.swift:42; synthetic F claim.'})
        self.reject(lambda: material.neutralize(value), 'unreviewed narrative path boundary')

    def test_19_tool_tokens_are_bounded_and_protected_text_is_not_changed(self):
        value = self.source({'reason': 'candidate-v13.9; synthetic F claim.', 'assertions': [{'status': 'U', 'actual': None}]})
        result, _ = material.neutralize(value); self.assertEqual(result['reason'], 'recorded-engine; synthetic F claim.')
        self.assertEqual(result['assertions'], value['assertions'])
        self.reject(lambda: material.neutralize({'reason': 'candidate-v13.90 has a different identity'}), 'tool token prefix')
        self.reject(lambda: material.neutralize({'expected': {'text': 'candidate-v13.9'}}), 'protected rendered identity')

    def child(self, mode):
        script = self.case / 'PROBE.py'
        script.write_text('''import importlib.util,json,pathlib,sys
module_path=pathlib.Path(sys.argv[1]); revision=module_path.parent.parent/'publication-alarm-review/revision-v2'
spec=importlib.util.spec_from_file_location('anonymous_projection',revision/'anonymous_projection.py')
engine=importlib.util.module_from_spec(spec);sys.modules['anonymous_projection']=engine;spec.loader.exec_module(engine)
engine.project=lambda original,**kwargs: ({}, {'synthetic_unreviewed_cached_function':True})
if sys.argv[2]=='foreign':engine.__file__=str(module_path.parent/'unreviewed.py')
try:
 spec=importlib.util.spec_from_file_location('material_probe',module_path); helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 value={'assertions':[{'status':'F','expected':48,'actual':44}]};result,proof=helper.neutralize(value)
 print(json.dumps({'accepted':True,'result':result,'original':value,'proof':proof}))
except ValueError as error:print(json.dumps({'accepted':False,'error':str(error)}))
''')
        completed = subprocess.run([sys.executable, '-B', str(script), str(MODULE), mode], capture_output=True, text=True)
        (self.case / 'STDOUT.txt').write_text(completed.stdout); (self.case / 'STDERR.txt').write_text(completed.stderr)
        self.assertEqual(completed.returncode, 0); result = json.loads(completed.stdout); self.observe(mode, result)
        self.assertTrue(not result['accepted'] or result['result'] == result['original'], 'Unreviewed cached module altered factual rows')

    def test_20_foreign_named_module_is_rejected_or_isolated(self): self.child('foreign')

    def test_21_same_path_cache_is_not_proof_of_pinned_code(self): self.child('same-path')

    def test_22_changed_library_bytes_are_rejected_before_execution(self):
        base = self.case / 'changed-library'; here = base / 'alarm-material-tools'; here.mkdir(parents=True)
        (here / 'material.py').write_bytes(MODULE.read_bytes())
        revision = base / 'publication-alarm-review/revision-v2'; revision.mkdir(parents=True)
        source = MODULE.parent.parent / 'publication-alarm-review/revision-v2'
        for name in material.PINS:
            raw = (source / name).read_bytes()
            if name == 'anonymous_projection.py': raw += b'\nraise RuntimeError("Synthetic changed code must never execute")\n'
            (revision / name).write_bytes(raw)
        self.reject(lambda: load(here / 'material.py', 'changed_library_probe'), 'mismatched library pin')

    def test_23_extended_acquisition_claims_are_retained_or_fail_closed(self):
        path = '/Users/rex/Project With Spaces/frame.json'
        ref = {'path': path, 'sha256': '0' * 64}
        value = self.source({'exit_code': 1, 'acquisition_evidence': {
            'capture_receipt': ref, 'execution': None, 'native_log': None, 'observation': ref,
            'scope': 'Synthetic F claim: see ' + path + ':1; expected 48, actual 44.',
            'additional_assertions': [{'status': 'F', 'expected': 48, 'actual': 44}, {'status': 'U', 'actual': None}]}})
        try:
            view = material.outcome_view(value)
        except ValueError as error:
            self.assertNotIn('acquisition_evidence', material.OUTCOME_FIELDS)
            self.observe('safe rejection of unfamiliar omitted metadata schema', str(error)); return
        self.assertEqual(view, value)
        result, proof = material.neutralize(view, {path: 'provenance/frame.json'})
        self.observe('projected retained claim', result); self.observe('proof', proof)
        expected = copy.deepcopy(value)
        expected['acquisition_evidence']['scope'] = value['acquisition_evidence']['scope'].replace(path, 'provenance/frame.json')
        expected['acquisition_evidence']['capture_receipt']['path'] = 'provenance/frame.json'
        expected['acquisition_evidence']['observation']['path'] = 'provenance/frame.json'
        self.assertEqual(result, expected)


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.rows = []
    def addSuccess(self, test): super().addSuccess(test); self.rows.append({'test': test.id(), 'status': 'pass'})
    def addFailure(self, test, error):
        super().addFailure(test, error); self.rows.append({'test': test.id(), 'status': 'fail', 'traceback': ''.join(traceback.format_exception(*error))})
    def addError(self, test, error):
        super().addError(test, error); self.rows.append({'test': test.id(), 'status': 'error', 'traceback': ''.join(traceback.format_exception(*error))})


def main():
    global RUN, MODULE, material
    parser = argparse.ArgumentParser(); parser.add_argument('--module', type=Path, required=True); parser.add_argument('--run', type=Path, required=True); args = parser.parse_args()
    MODULE, RUN = args.module, args.run
    assert all(path.is_absolute() and path.is_relative_to(ROOT) for path in (MODULE, RUN))
    RUN.mkdir(parents=True, exist_ok=False); material = load(MODULE, 'reviewed_material')
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(Behavior))
    report = {'version': 1, 'synthetic_only': True, 'tests_run': result.testsRun,
              'passed': result.testsRun - len(result.failures) - len(result.errors), 'failures': len(result.failures), 'errors': len(result.errors),
              'module_sha256': sha(MODULE.read_bytes()), 'control_sha256': sha(Path(__file__).read_bytes()),
              'presentation_pins': material.PINS, 'controls': result.rows}
    (RUN / 'RESULT.json').write_bytes(encoded(report)); print(json.dumps({key: report[key] for key in ('tests_run', 'passed', 'failures', 'errors', 'module_sha256', 'control_sha256')}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
