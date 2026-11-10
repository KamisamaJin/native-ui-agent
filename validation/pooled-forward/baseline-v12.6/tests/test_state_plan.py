import copy
import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import native_checks as checks
import state_plan
from observation_contract import validate_actions


class StateMatrix(unittest.TestCase):
    def matrix(self):
        return {'version': 1, 'required_state_ids': ['one', 'two', 'three'],
                'required_requirement_ids': ['name'],
                'states': [{'id': name, 'input_index': 0, 'after_action': i, 'coverage': 'targets'}
                           for i, name in enumerate(['one', 'two', 'three'])],
                'requirements': [{'id': 'name', 'source': 'Independent public interface contract',
                                  'check': {'kind': 'control', 'target': {'identifier': 'choice'},
                                            'property': 'label', 'expected': 'Required name'}}]}

    def test_each_selected_state_is_a_required_atomic_check(self):
        matrix = self.matrix()
        plan, actions = state_plan.compile_matrix(matrix, [{'type': 'checkpoint'}] * 3)
        self.assertEqual([a['id'] for a in plan['assertions']], ['one/name', 'two/name', 'three/name'])
        self.assertEqual([a['state_id'] for a in actions], ['one', 'two', 'three'])
        self.assertTrue(all(a['after_targets'] == [{'identifier': 'choice'}] for a in actions))
        self.assertNotIn('expected', str(actions))
        self.assertEqual(matrix, self.matrix())

    def test_missing_declared_state_or_requirement_cannot_silently_shrink_denominator(self):
        for key in ['required_state_ids', 'required_requirement_ids']:
            matrix = self.matrix(); matrix[key] = matrix[key][:-1]
            with self.assertRaises(ValueError): state_plan.compile_matrix(matrix)

    def test_missing_state_expectation_rejected_before_native_cost(self):
        matrix = self.matrix(); matrix['requirements'][0]['check'].pop('expected')
        matrix['requirements'][0]['by_state'] = {'one': {'expected': 'First'}}
        with self.assertRaises(ValueError): state_plan.compile_matrix(matrix)

    def test_explicit_not_applicable_is_retained_with_reason(self):
        matrix = self.matrix(); matrix['requirements'][0]['not_applicable'] = {'three': 'Control not part of this selected state'}
        plan, _ = state_plan.compile_matrix(matrix)
        self.assertEqual(len(plan['assertions']), 2)
        self.assertEqual(len(plan['matrix_contract']['cells']), 3)
        self.assertEqual(plan['matrix_contract']['cells'][-1]['disposition'], 'not_applicable')
        matrix['requirements'][0]['not_applicable']['three'] = ''
        with self.assertRaises(ValueError): state_plan.compile_matrix(matrix)

    def test_observation_plan_preserves_original_actions_and_callback_requests(self):
        matrix = self.matrix(); original = [{'type': 'tap', 'target': {'identifier': 'choice'}, 'expect_callback': 'requested'}] * 3
        _, enriched = state_plan.compile_matrix(matrix, original)
        self.assertEqual(original[0], {'type': 'tap', 'target': {'identifier': 'choice'}, 'expect_callback': 'requested'})
        self.assertEqual(enriched[0]['expect_callback'], 'requested')
        conflicting = copy.deepcopy(original); conflicting[1]['state_id'] = 'wrong'
        with self.assertRaises(ValueError): state_plan.compile_matrix(matrix, conflicting)

    def test_selected_state_failures_all_become_exact_machine_findings(self):
        plan, _ = state_plan.compile_matrix(self.matrix())
        snapshots, steps = [], []
        for name in ['one', 'two', 'three']:
            binding = {'fixture_index': 0, 'input_sha256': 'input', 'event_revision': 0, 'instance': 'native'}
            snapshots.append({'state_id': name, 'binding': binding, 'nodes': [
                {'identifier': 'choice', 'label': 'Contradicting name', 'intersects_viewport': True}]})
            steps.append({'state_id': name, 'after': len(snapshots) - 1, 'binding_after': binding})
        result = checks.evaluate(plan, {'snapshots': snapshots, 'steps': steps}, 'ios')
        self.assertEqual(result['counts'], {'passed': 0, 'failed': 3, 'unassessed': 0})
        self.assertEqual([f['id'] for f in result['machine_findings']], ['one/name', 'two/name', 'three/name'])


class TargetSetEvidence(unittest.TestCase):
    def observation(self):
        binding = {'fixture_index': 0, 'input_sha256': 'input', 'event_revision': 1, 'instance': 'native', 'pid': 123}
        nodes = [[{'identifier': 'heading', 'label': 'Bound heading', 'intersects_viewport': True}],
                 [{'identifier': 'footer', 'label': 'Bound footer', 'intersects_viewport': True}]]
        snapshots = [{'state_id': 'ready', 'binding': dict(binding), 'binding_after_capture': dict(binding),
                      'capture_consistent': True, 'nodes': n} for n in nodes]
        before = dict(binding, event_revision=0)
        step = {'state_id': 'ready', 'after': 1, 'immediate_after': 0, 'binding_after': binding,
                'outcome': 'tapped', 'callback_delta': ['requested'],
                'dispatch': {'attempted': True, 'succeeded': True, 'method': 'xcui_tap', 'stimulus': 'activation',
                             'binding_before': before, 'event_start': 0, 'event_end': 1, 'matches': 1, 'native_controls': 1, 'enabled': True},
                'observation_set': {'state_id': 'ready', 'after_action': 0, 'binding': binding,
                                    'binding_after_observation': dict(binding), 'binding_stable': True,
                                    'snapshot_indices': [0, 1], 'all_targets_observed': True}}
        return {'snapshots': snapshots, 'steps': [step]}

    def plan(self):
        return {'version': 1, 'states': [{'id': 'ready', 'input_index': 0, 'after_action': 0, 'coverage': 'targets'}],
                'assertions': [{'id': key, 'state': 'ready', 'kind': 'control', 'target': {'identifier': key},
                                'property': 'label', 'expected': 'Bound ' + key} for key in ['heading', 'footer']]}

    def test_joint_frames_cover_targets_without_claiming_full_content(self):
        result = checks.evaluate(self.plan(), self.observation(), 'ios')
        self.assertEqual(result['counts']['passed'], 2)
        self.assertFalse(result['states']['ready']['complete'])
        self.assertEqual([r['snapshot_indices'] for r in result['assertions']], [[0], [1]])

    def test_old_last_frame_still_gets_actual_credit_only(self):
        observation = self.observation(); observation['steps'][0].pop('observation_set')
        result = checks.evaluate(self.plan(), observation, 'ios')
        self.assertEqual(result['counts'], {'passed': 1, 'failed': 0, 'unassessed': 1})

    def test_input_event_process_or_image_drift_cannot_borrow_frames(self):
        for field, value in [('event_revision', 2), ('instance', 'other'), ('input_sha256', 'other'), ('fixture_index', 1)]:
            observation = self.observation(); observation['snapshots'][1]['binding'][field] = value
            self.assertEqual(checks.evaluate(self.plan(), observation, 'ios')['counts']['unassessed'], 2)
        observation = self.observation(); observation['snapshots'][1]['capture_consistent'] = False
        self.assertEqual(checks.evaluate(self.plan(), observation, 'ios')['counts']['unassessed'], 2)

    def test_target_summary_boolean_is_not_native_proof(self):
        observation = self.observation(); observation['steps'][0]['observation_set']['snapshot_indices'] = [1]
        self.assertEqual(checks.evaluate(self.plan(), observation, 'ios')['counts']['unassessed'], 2)
        observation = self.observation(); observation['steps'][0]['observation_set']['after_action'] = 1
        self.assertEqual(checks.evaluate(self.plan(), observation, 'ios')['counts']['unassessed'], 2)

    def test_callback_interval_remains_immediate_not_target_navigation(self):
        observation = self.observation(); plan = self.plan()
        plan['assertions'] = [{'id': 'event', 'state': 'ready', 'kind': 'event', 'action_index': 0, 'expected': ['requested']}]
        self.assertEqual(checks.evaluate(plan, observation, 'ios')['counts']['passed'], 1)
        observation['steps'][0]['dispatch']['event_end'] = 2
        self.assertEqual(checks.evaluate(plan, observation, 'ios')['counts']['unassessed'], 1)

    def test_conflicting_values_inside_one_native_epoch_stay_unknown(self):
        observation = self.observation(); observation['snapshots'][1]['nodes'].append(
            {'identifier': 'heading', 'label': 'Unexpected heading', 'intersects_viewport': True})
        result = checks.evaluate(self.plan(), observation, 'ios')
        self.assertEqual(result['counts'], {'passed': 1, 'failed': 0, 'unassessed': 1})

    def test_missing_target_does_not_prove_absence_without_full_sweep(self):
        plan = self.plan(); plan['assertions'] = [{'id': 'absent', 'state': 'ready', 'kind': 'control',
            'target': {'identifier': 'unseen'}, 'property': 'present', 'expected': False}]
        self.assertEqual(checks.evaluate(plan, self.observation(), 'ios')['counts']['unassessed'], 1)


class ObservationBounds(unittest.TestCase):
    def test_duplicate_or_unbounded_target_requests_rejected(self):
        for targets in [[], [{'identifier': 'a'}] * 2, [{'identifier': str(i)} for i in range(33)]]:
            with self.assertRaises(ValueError): validate_actions([{'type': 'checkpoint', 'after_targets': targets}])
        validate_actions([{'type': 'checkpoint', 'after_targets': [{'label': 'Exact', 'role': 'text'}], 'observation_max_scrolls': 0}])
        with self.assertRaises(ValueError): validate_actions([{'type': 'checkpoint', 'observation_max_scrolls': True}])


if __name__ == '__main__':
    unittest.main()
