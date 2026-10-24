import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

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
        self.assertEqual(routes.admission(self.coverage, self.plan, self.report)['status'], 'accepted')
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


if __name__ == '__main__': unittest.main()
