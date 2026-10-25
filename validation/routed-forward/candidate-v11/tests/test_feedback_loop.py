import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_delivery_plan as fixtures
import design_contract as d
import feedback_loop as loop
import locator_diagnostics as diag
import retest_plan


class DefaultLoopTests(unittest.TestCase):
    setUp = fixtures.DeliveryPlanTests.setUp
    audit = fixtures.DeliveryPlanTests.audit

    def test_unknown_is_planned_without_fabricating_failure(self):
        report = copy.deepcopy(self.report)
        report['assertions'][0]['status'] = 'unassessed'
        result = retest_plan.unresolved(self.coverage, self.plan, report, changed_files=[], source_before='a'*64, source_after='a'*64)
        self.assertEqual(result['states'], ['ready'])
        self.assertEqual(result['original_failed_ids'], [])
        self.assertEqual(result['original_unknown_ids'], ['ready/caption'])
        self.assertTrue(result['full_final_required'])

    def test_final_is_full_even_when_only_one_state_has_an_issue(self):
        self.report['assertions'][0]['status'] = 'failed'
        result = retest_plan.unresolved(self.coverage, self.plan, self.report, changed_files=['A.swift'], source_before='a'*64, source_after='b'*64, final=True)
        self.assertEqual(result['states'], ['ready', 'chosen', 'updated'])

    def test_diagnosis_does_not_guess_or_close_missing_state(self):
        report = copy.deepcopy(self.report); report['assertions'][0]['status'] = 'unassessed'
        source = Path(self.temp.name) / 'View.swift'; source.write_text('Text("Caption").accessibilityIdentifier("caption")')
        result = diag.diagnose(self.plan, report, {}, [source])
        self.assertEqual(len(result['items']), 1)
        row = result['items'][0]
        self.assertFalse(row['state_evidence_present'])
        self.assertEqual(row['targets'][0]['source_occurrences'][0]['line'], 1)
        self.assertEqual(row['targets'][0]['frames'], [])
        self.assertIn('open', row['closure'])

    def test_default_entry_always_routes_diagnoses_and_plans_before_native(self):
        root = Path(self.temp.name); roots = [root / 'Component.swift']; roots[0].write_text('let x = 1')
        paths = {}
        for name, obj in [('plan', self.plan), ('design_lock', self.lock), ('fixtures', {'initial': {}, 'updates': [{}]}), ('routes', self.routes), ('environment', {})]:
            paths[name] = str(root / (name + '.json')); Path(paths[name]).write_text(json.dumps(obj))
        bridge = root / 'Bridge.swift'; bridge.write_text('bridge')
        config = dict(paths, design_sha256=self.lock_sha, routes_sha256=d.digest(self.routes), bridge=str(bridge), source_roots=list(map(str, roots)),
                      launch_ref={'source': 'reference', 'pointer': '/launch'}, native_options={}, environment_sha256=d.digest({}))
        native_result = {'status': 'invalid_or_incomplete_capture'}
        def native(*args, **kwargs):
            out = args[6]; out.mkdir(); (out / 'result.json').write_text(json.dumps(native_result))
            self.assertTrue((out.parent / 'retest-plan.json').exists())
            self.assertTrue((out.parent / 'before-diagnostics.json').exists())
            self.assertTrue((out.parent / 'before-routes.json').exists())
            return native_result
        # Launch approval already has dedicated native preflight tests. Here the
        # spy verifies actual default sequencing and no hand-selected states.
        with patch.object(loop.xp, 'compile_execution', return_value={'parent_plan_sha256': d.digest(self.plan), 'design_lock_sha256': self.lock_sha, 'selected_states': ['ready', 'chosen', 'updated'], 'scope': 'full'}) as compile_spy, patch.object(loop.xp, 'run_execution', side_effect=native):
            result = loop.run_cycle(config, root / 'cycle')
        self.assertEqual(compile_spy.call_args.kwargs['states'], ['ready', 'chosen', 'updated'])
        self.assertEqual(result['trace'][:3], ['route_findings', 'locator_diagnostics', 'retest_plan.dispatch'])
        self.assertTrue(result['native_executed'])
        with self.assertRaises(TypeError): loop.run_cycle(config, root / 'other', states=['ready'])

    def test_approved_absence_acquires_full_content_without_demanding_presence(self):
        root = Path(self.temp.name)
        reference = json.loads((root / 'reference.json').read_text())
        reference['enabled']['value'] = False
        (root / 'reference.json').write_text(json.dumps(reference))
        contract = json.loads((root / 'contract.json').read_text())
        contract['rules'][1]['property'] = 'present'
        contract['sources'][0]['sha256'] = loop.sha(root / 'reference.json')
        (root / 'contract.json').write_text(json.dumps(contract))
        lock = d.seal(root / 'contract.json', root); lock_sha = d.digest(lock)
        plan, _ = d.compile_contract(lock, lock_sha, 'public', 'ios', self.plan['design_contract']['bindings'], self.plan['design_contract']['base_actions'])
        value = loop.xp.compile_execution(plan, lock, lock_sha, {'initial': {}, 'updates': [{}]}, 'a'*64,
                                         launch_ref={'source': 'reference', 'pointer': '/launch'})
        for entry in value['required_coverage']:
            self.assertEqual(entry['coverage'], 'full_content')
            self.assertNotIn({'identifier': 'activate', 'role': 'button'}, entry['targets'])
        self.assertEqual(value['actions'][1]['capture_scope'], 'full_content')

    def test_failed_locator_has_diagnostic_evidence_without_changing_verdict(self):
        self.report['assertions'][0]['status'] = 'failed'
        result = diag.diagnose(self.plan, self.report, {}, [])
        self.assertEqual(result['items'][0]['issue_status'], 'failed')
        self.assertEqual(self.report['assertions'][0]['status'], 'failed')

    def test_pinned_previous_cannot_be_replaced_before_sdk(self):
        p = Path(self.temp.name) / 'result.json'; p.write_text('{}')
        with self.assertRaises(ValueError):
            loop.load_previous(p, '0'*64, self.plan, self.lock, self.lock_sha, {}, p, [])

if __name__ == '__main__': unittest.main()
