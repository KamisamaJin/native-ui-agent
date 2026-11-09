import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import design_contract as d
import requirement_routes as routes
import execution_plan as execution
import retest_plan as retest


class DeliveryPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        source = {'title': {'value': 'Approved caption', 'unit': 'string'}, 'enabled': {'value': True, 'unit': 'bool'},
                  'launch': {'fixtures_sha256': d.digest({'initial': {}, 'updates': [{}]}), 'bridge_sha256': 'a' * 64, 'scenario': 'public', 'platform': 'ios'},
                  'obligations': [
                      {'id': 'caption', 'clause': 'The initial caption is present.', 'priority': 'must', 'states': ['ready'], 'risk': 'content'},
                      {'id': 'activation', 'clause': 'The action stays enabled after interaction and caller replacement.', 'priority': 'must', 'states': ['chosen', 'updated'], 'risk': 'behavior'},
                      {'id': 'optional', 'clause': 'Optional native font inspection.', 'priority': 'advisory', 'states': ['ready'], 'risk': 'style'}]}
        (root / 'reference.json').write_text(json.dumps(source))
        import hashlib
        contract = {'version': 1, 'design_owner': 'independent-owner', 'approval_reference': 'external',
                    'sources': [{'id': 'reference', 'path': 'reference.json', 'sha256': hashlib.sha256((root / 'reference.json').read_bytes()).hexdigest()}],
                    'rules': [{'id': 'caption', 'kind': 'control', 'target': 'title', 'property': 'label'},
                              {'id': 'enabled', 'kind': 'control', 'target': 'action', 'property': 'enabled'}],
                    'required_rule_ids': ['caption', 'enabled'], 'scenarios': {}}
        states = [{'id': v, 'input_index': 1 if v == 'updated' else 0, 'after_action': i,
                   'coverage': 'targets' if v == 'chosen' else 'full_content'} for i, v in enumerate(['ready', 'chosen', 'updated'])]
        actions = [{'type': 'checkpoint'}, {'type': 'tap', 'target': 'action'}, {'type': 'apply_next_fixture'}]
        contract['scenarios']['public'] = {'states': states, 'actions': actions, 'values': {rule: {s['id']: {
            pl: {'source': 'reference', 'pointer': '/' + ('title' if rule == 'caption' else 'enabled')} for pl in ['ios', 'android']}
            for s in states} for rule in ['caption', 'enabled']}}
        (root / 'contract.json').write_text(json.dumps(contract)); self.lock = d.seal(root / 'contract.json', root); self.lock_sha = d.digest(self.lock)
        bindings = {'title': {'identifier': 'caption', 'role': 'text'}, 'action': {'identifier': 'activate', 'role': 'button'}}
        bound = copy.deepcopy(actions); bound[1]['target'] = bindings['action']
        self.plan, self.actions = d.compile_contract(self.lock, self.lock_sha, 'public', 'ios', bindings, bound)
        self.routes = {'version': 1, 'index': {'source': 'reference', 'pointer': '/obligations'}, 'routes': {
            'caption': {'rule_ids': ['caption'], 'reason': 'Bound native caption.', 'regression_obligations': []},
            'activation': {'rule_ids': ['enabled'], 'reason': 'Bound native action.', 'regression_obligations': ['caption']},
            'optional': {'rule_ids': [], 'reason': 'Unavailable advisory native property.', 'regression_obligations': []}}}
        self.coverage = self.audit()
        self.report = {'assertions': [{'id': a['id'], 'state': a['state'], 'status': 'passed'} for a in self.plan['assertions']]}
        self.capture = {'status': 'verified_capture', 'scope': 'full', 'parent_plan_sha256': d.digest(self.plan),
                        'native_exit_code': 0, 'source_unchanged': True, 'inputs_unchanged': True, 'coverage_satisfied': True}

    def audit(self, value=None):
        value = value or self.routes
        return routes.audit(self.lock, self.lock_sha, self.plan, value, d.digest(value))

    def test_all_approved_obligations_need_dispositions(self):
        changed = copy.deepcopy(self.routes); del changed['routes']['optional']
        with self.assertRaises(ValueError): self.audit(changed)
        self.assertFalse(self.coverage['must_route_gaps'])

    def test_missing_must_route_blocks_even_all_other_checks_pass(self):
        changed = copy.deepcopy(self.routes); changed['routes']['activation']['rule_ids'] = []
        coverage = self.audit(changed)
        self.assertEqual(coverage['must_route_gaps'], ['activation'])
        self.assertEqual(routes.admission(coverage, self.plan, self.report)['status'], 'not_accepted')

    def test_unknown_is_not_success_and_partial_is_never_complete_acceptance(self):
        self.assertEqual(routes.admission(self.coverage, self.plan, self.report)['status'], 'not_accepted')
        self.assertEqual(routes.admission(self.coverage, self.plan, self.report, capture=self.capture, environment={'status': 'P'})['status'], 'accepted')
        self.assertEqual(routes.admission(self.coverage, self.plan, self.report, capture=self.capture, environment={'status': 'U'})['status'], 'not_accepted')
        self.assertEqual(routes.admission(self.coverage, self.plan, self.report, execution_scope='targeted')['status'], 'not_accepted')
        self.report['assertions'][0]['status'] = 'unassessed'
        self.assertIn('caption', routes.admission(self.coverage, self.plan, self.report)['blocking_obligations'])

    def test_routes_cannot_be_repinned_or_invent_checks(self):
        with self.assertRaises(ValueError): routes.audit(self.lock, self.lock_sha, self.plan, self.routes, '0' * 64)
        changed = copy.deepcopy(self.routes); changed['routes']['caption']['rule_ids'] = ['invented']
        with self.assertRaises(ValueError): self.audit(changed)

    def test_single_execution_reconstructs_after_targets(self):
        config = {'initial': {}, 'updates': [{}]}
        value = execution.compile_execution(self.plan, self.lock, self.lock_sha, config, 'a' * 64, launch_ref={'source': 'reference', 'pointer': '/launch'})
        self.assertEqual(value['actions'][1]['after_targets'], self.actions[1]['after_targets'])
        execution.verify_execution(value, self.plan, self.lock, self.lock_sha, config, 'a' * 64)
        changed = copy.deepcopy(value); del changed['actions'][1]['after_targets']
        with self.assertRaises(ValueError): execution.verify_execution(changed, self.plan, self.lock, self.lock_sha, config, 'a' * 64)

    def test_targeted_feedback_retains_business_actions_and_parent_expectations(self):
        before = d.digest(self.plan)
        value = execution.compile_execution(self.plan, self.lock, self.lock_sha, {'initial': {}, 'updates': [{}]}, 'a' * 64, launch_ref={'source': 'reference', 'pointer': '/launch'}, states=['updated'])
        self.assertEqual(value['scope'], 'targeted')
        self.assertEqual([a['type'] for a in value['actions']], [a['type'] for a in self.actions])
        self.assertEqual(value['actions'][1]['target'], self.actions[1]['target'])
        self.assertEqual(value['actions'][1]['capture_scope'], 'none')
        self.assertEqual(d.digest(self.plan), before)
        self.assertEqual([s['id'] for s in value['config']['execution_state_definitions']], ['ready', 'chosen', 'updated'])

    def test_feedback_selects_original_failures_and_dependency_closure(self):
        self.report['assertions'][0]['status'] = 'failed'
        selected = retest.propose(self.coverage, self.plan, self.report, [self.report['assertions'][0]['id']], changed_files=['Component.swift'], source_before='a' * 64, source_after='b' * 64)
        self.assertEqual(selected['states'], ['ready']); self.assertTrue(selected['full_final_required'])
        failed = next(v for v in self.report['assertions'] if v['id'] == 'chosen/enabled'); failed['status'] = 'failed'
        selected = retest.propose(self.coverage, self.plan, self.report, [failed['id']], changed_files=['Component.swift'], source_before='a' * 64, source_after='b' * 64)
        self.assertEqual(selected['obligations'], ['activation', 'caption'])
        self.assertEqual(selected['states'], ['ready', 'chosen', 'updated'])

    def test_retest_rejects_invented_failure_unchanged_source_and_unsafe_paths(self):
        for kwargs in [dict(source_before='a', source_after='a', changed_files=['A.swift']),
                       dict(source_before='a', source_after='b', changed_files=['../A.swift']),
                       dict(source_before='a', source_after='b', changed_files=['A.swift'])]:
            with self.assertRaises(ValueError): retest.propose(self.coverage, self.plan, self.report, ['ready/caption'], **kwargs)

    def test_outside_route_discovery_is_not_automatically_a_product_false_alarm(self):
        changed = copy.deepcopy(self.routes); changed['routes']['activation']['rule_ids'] = []
        tasks = routes.route_findings(self.audit(changed), self.plan, self.report, {}, discoveries=[
            {'obligation_id': 'activation', 'reason': 'Original observed contradiction', 'evidence': [{'path': 'original.png', 'sha256': 'a' * 64}]}])['tasks']
        self.assertTrue(any(v['action'] == 'repair_contract_route' for v in tasks))
        self.assertFalse(any('FP' in v for v in tasks))

    def test_visual_disagreement_routes_to_oracle_not_code_churn(self):
        self.report['assertions'][0].update(status='unassessed', panel_disagreement=True)
        tasks = routes.route_findings(self.coverage, self.plan, self.report, {})['tasks']
        self.assertEqual(tasks[0]['action'], 'clarify_oracle')

    def test_deliberately_unrequested_states_do_not_trigger_locator_investigation(self):
        value = execution.compile_execution(self.plan, self.lock, self.lock_sha, {'initial': {}, 'updates': [{}]}, 'a' * 64,
                                            launch_ref={'source': 'reference', 'pointer': '/launch'}, states=['updated'])
        report = copy.deepcopy(self.report)
        for row in report['assertions']: row['status'] = 'unassessed'
        result = routes.route_findings(self.coverage, self.plan, report, {'execution_scope': 'targeted'}, execution=value)
        self.assertIn('ready/caption', result['deferred_assertions'])
        self.assertTrue(all(t['action'] == 'defer_to_full_verification' for t in result['tasks'] if t.get('state') == 'ready'))
        self.assertTrue(all(t['action'] == 'acquire_evidence' for t in result['tasks'] if t.get('state') == 'updated'))
        unknown = routes.route_findings(self.coverage, self.plan, report, {'execution_scope': 'targeted'})
        self.assertTrue(all(t['action'] == 'validate_execution_scope' for t in unknown['tasks'] if t.get('state')))
        # A real supported failure is retained even outside a requested state.
        report['assertions'][0]['status'] = 'failed'
        result = routes.route_findings(self.coverage, self.plan, report, {'execution_scope': 'targeted'}, execution=value)
        self.assertNotIn('ready/caption', result['deferred_assertions'])

    def test_launch_inputs_cannot_be_self_approved_or_cross_bound(self):
        for config, bridge in [({'initial': {'changed': True}, 'updates': [{}]}, 'a' * 64),
                               ({'initial': {}, 'updates': [{}]}, 'b' * 64)]:
            with self.assertRaises(ValueError):
                execution.compile_execution(self.plan, self.lock, self.lock_sha, config, bridge,
                                            launch_ref={'source': 'reference', 'pointer': '/launch'})

    def test_targeted_prefix_never_skips_its_preceding_business_stimuli(self):
        value = execution.compile_execution(self.plan, self.lock, self.lock_sha, {'initial': {}, 'updates': [{}]}, 'a' * 64,
                                            launch_ref={'source': 'reference', 'pointer': '/launch'}, states=['chosen'])
        self.assertEqual(value['executed_action_count'], 2)
        self.assertEqual(value['parent_action_count'], 3)
        self.assertEqual(value['actions'][1]['type'], 'tap')
        self.assertEqual(value['config']['updates'], [{}])

    def test_invalid_execution_or_policy_is_rejected_before_sdk(self):
        root = Path(self.temp.name); bridge = root / 'Bridge.swift'; bridge.write_text('neutral source')
        import hashlib
        bridge_sha = hashlib.sha256(bridge.read_bytes()).hexdigest()
        # Reseal independent neutral approval, not a caller's execution override.
        self.lock['sources']['reference']['document']['launch']['bridge_sha256'] = bridge_sha
        source = root / 'reference.json'; doc = json.loads(source.read_text()); doc['launch']['bridge_sha256'] = bridge_sha
        source.write_text(json.dumps(doc))
        contract = json.loads((root / 'contract.json').read_text()); contract['sources'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        (root / 'contract.json').write_text(json.dumps(contract)); lock = d.seal(root / 'contract.json', root); lock_sha = d.digest(lock)
        bindings = self.plan['design_contract']['bindings']
        plan, _ = d.compile_contract(lock, lock_sha, 'public', 'ios', bindings, self.plan['design_contract']['base_actions'])
        config = {'initial': {}, 'updates': [{}]}
        value = execution.compile_execution(plan, lock, lock_sha, config, bridge_sha, launch_ref={'source': 'reference', 'pointer': '/launch'})
        with patch.object(execution.subprocess, 'run') as sdk:
            for invalid, policy in [(dict(value, selected_states=['invented']), None), (value, {})]:
                with self.assertRaises((ValueError, KeyError)):
                    execution.run_execution(invalid, plan, lock, lock_sha, config, bridge, root / 'run', [bridge], {}, policy=policy, policy_sha='0' * 64 if policy is not None else None)
            with self.assertRaises(ValueError):
                execution.run_execution(value, plan, lock, lock_sha, config, bridge, root / 'run', [bridge], {},
                                        expected_environment={'width': 400}, environment_sha='0' * 64)
            sdk.assert_not_called()
        self.assertFalse((root / 'run').exists())
        with patch.object(execution.subprocess, 'run') as sdk:
            sdk.return_value.returncode = 65
            result = execution.run_execution(value, plan, lock, lock_sha, config, bridge, root / 'native-failure', [bridge], {})
        self.assertEqual(result['native_exit_code'], 65)
        self.assertEqual(result['status'], 'invalid_or_incomplete_capture')
        self.assertTrue((root / 'native-failure/result.json').is_file())
        def remove_source(*args, **kwargs):
            bridge.unlink()
            return type('NativeResult', (), {'returncode': 0})()
        with patch.object(execution.subprocess, 'run', side_effect=remove_source):
            result = execution.run_execution(value, plan, lock, lock_sha, config, bridge, root / 'source-drift', [bridge], {})
        self.assertFalse(result['source_unchanged'])
        self.assertEqual(result['status'], 'invalid_or_incomplete_capture')
        self.assertTrue((root / 'source-drift/result.json').is_file())

    def test_missing_capture_never_claims_required_state_coverage(self):
        value = execution.compile_execution(self.plan, self.lock, self.lock_sha, {'initial': {}, 'updates': [{}]}, 'a' * 64,
                                            launch_ref={'source': 'reference', 'pointer': '/launch'})
        receipt = execution.coverage_receipt(value, {})
        self.assertFalse(receipt['satisfied'])
        self.assertEqual(receipt['missing_states'], ['ready', 'chosen', 'updated'])

    def test_retest_derives_actual_changes_and_rejects_report_or_root_substitution(self):
        import hashlib
        root = Path(self.temp.name); production = root / 'Component.swift'; production.write_text('original source')
        captured = root / 'captured'; captured.mkdir()
        before = execution.source_fingerprint([production])
        report = copy.deepcopy(self.report); report['assertions'][0]['status'] = 'failed'
        for name, value in [('source-before.json', before), ('source-after.json', before), ('automatic.json', report)]:
            (captured / name).write_text(json.dumps(value))
        receipt = {'status': 'verified_capture', 'parent_plan_sha256': d.digest(self.plan), 'source_sha256': d.digest(before),
                   'source_roots': [str(production.resolve())], 'automatic_sha256': hashlib.sha256((captured / 'automatic.json').read_bytes()).hexdigest()}
        path = captured / 'result.json'; path.write_text(json.dumps(receipt)); pinned = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaises(ValueError): retest.from_capture(self.coverage, self.plan, ['ready/caption'], path, pinned, [production])
        production.write_text('actual changed source')
        value = retest.from_capture(self.coverage, self.plan, ['ready/caption'], path, pinned, [production])
        self.assertEqual(value['changed_files'], ['0/Component.swift']); self.assertEqual(value['states'], ['ready'])
        with self.assertRaises(ValueError): retest.from_capture(self.coverage, self.plan, ['ready/caption'], path, pinned, [root])
        (captured / 'automatic.json').write_text(json.dumps(self.report))
        with self.assertRaises(ValueError): retest.from_capture(self.coverage, self.plan, ['ready/caption'], path, pinned, [production])


if __name__ == '__main__': unittest.main()
