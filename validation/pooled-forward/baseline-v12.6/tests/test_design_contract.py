"""Public boundaries: wrong provenance, value overrides, units and state loss."""
import copy
import json
from pathlib import Path
import sys
import unittest

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S / 'scripts'))
import design_contract as d
import native_checks as n


class DesignContractTests(unittest.TestCase):
    def setUp(self):
        root = S / 'assets/design-example'
        self.lock = d.seal(root / 'contract.json', root)
        self.sha = d.digest(self.lock)
        self.bindings = d.load(root / 'bindings.json')
        self.actions = d.load(root / 'actions.json')

    def compile(self, platform='android', lock=None, bindings=None, actions=None):
        return d.compile_contract(lock or self.lock, self.sha, 'neutral', platform,
                                  bindings or self.bindings, actions or self.actions)

    def test_exact_sources_generate_every_cell(self):
        plan, actions = self.compile()
        self.assertEqual(len(plan['matrix_contract']['cells']), 12)
        self.assertEqual(len(plan['assertions']), 10)
        self.assertEqual(len(actions[0]['after_targets']), 4)
        self.assertEqual(plan['assertions'][0]['expected'], 'Panel A')
        self.assertEqual(plan['assertions'][3]['expected'], 0xFF276145)
        self.assertEqual(d.verify_generated(plan, self.lock, self.sha, 'android'), actions)

    def test_reject_plan_expected_precision_source_coverage_overrides(self):
        original, _ = self.compile()
        for field, value in [('expected', 'Panel C'), ('unit', 'dp'), ('source', 'implementation')]:
            plan = copy.deepcopy(original); plan['assertions'][0][field] = value
            with self.assertRaises(ValueError):
                d.verify_generated(plan, self.lock, self.sha, 'android')
        for mutation in ['delete', 'tolerance', 'state']:
            plan = copy.deepcopy(original)
            if mutation == 'delete': plan['assertions'].pop()
            if mutation == 'tolerance': plan['assertions'][1]['tolerance'] = 99
            if mutation == 'state': plan['states'][0]['input_index'] = 1
            with self.assertRaises(ValueError):
                d.verify_generated(plan, self.lock, self.sha, 'android')

    def test_cannot_replace_lock_and_repin_it_inside_plan(self):
        lock = copy.deepcopy(self.lock)
        lock['sources']['reference']['document']['labels']['A']['value'] = 'wrong'
        with self.assertRaises(ValueError): self.compile(lock=lock)
        with self.assertRaises(ValueError): d.validate_lock(lock, d.digest(lock))
        lock = copy.deepcopy(self.lock)
        lock['contract']['rules'].pop()
        with self.assertRaises(ValueError): self.compile(lock=lock)

    def test_source_pointers_inline_values_and_unit_arithmetic(self):
        sources = self.lock['sources']
        for expr in [{'value': 72, 'unit': 'dp'}, {'source': 'reference', 'pointer': ''},
                     {'operation': 'add', 'arguments': [{'source': 'reference', 'pointer': '/geometry/ios/width'}, {'source': 'reference', 'pointer': '/geometry/android/width'}]}]:
            with self.assertRaises((ValueError, KeyError)): d.expression(expr, sources)
        result, proof = d.expression({'operation': 'subtract', 'arguments': [{'source': 'reference', 'pointer': '/geometry/android/width'}, {'source': 'reference', 'pointer': '/geometry/android/gap'}]}, sources)
        self.assertEqual(result, {'value': 62, 'unit': 'dp'})
        self.assertEqual(len(proof), 2)

    def test_bindings_cannot_change_expectations_or_routes(self):
        bindings = dict(self.bindings, expected={'value': 99})
        with self.assertRaises(ValueError): self.compile(bindings=bindings)
        bindings = copy.deepcopy(self.bindings); bindings['header']['expected'] = 'Injected'
        with self.assertRaises(ValueError): self.compile(bindings=bindings)
        actions = copy.deepcopy(self.actions); actions[0]['type'] = 'capture'
        with self.assertRaises(ValueError): self.compile(actions=actions)
        plan, _ = self.compile()
        with self.assertRaises(ValueError): n.evaluate(plan, {}, 'android')
        with self.assertRaises(ValueError): d.verify_generated(plan, self.lock, self.sha, 'ios')

    def test_geometry_shared_frame_and_observation_basis(self):
        snapshot = {'nodes': [dict(node_id=1, parent_id=-1, identifier='a', label='A', intersects_viewport=True, fully_visible=True, unclipped_bounds_dp=[10, 20, 82, 52]), dict(node_id=2, parent_id=-1, identifier='b', label='B', intersects_viewport=True, fully_visible=True, unclipped_bounds_dp=[92, 20, 164, 52])]}
        rule = {'target': {'identifier': 'b'}, 'reference_target': {'identifier': 'a'}, 'property': 'gap_x'}
        self.assertEqual(n.geometry_value(snapshot, rule, 'android'), 10)
        snapshot['nodes'][0]['fully_visible'] = False
        self.assertIsNone(n.geometry_value(snapshot, rule, 'android'))
        snapshot['nodes'].pop(0)
        self.assertIsNone(n.geometry_value(snapshot, rule, 'android'))

    def test_numeric_tolerance_is_explicit(self):
        self.assertTrue(n.compare(72.00001, 72, 'near', 0.1))
        self.assertFalse(n.compare(73, 72, 'near', 0.1))
        self.assertFalse(n.compare(True, 1, 'near', 0.1))

    def test_ambiguous_json_and_unsupported_layout_scope(self):
        for text in ['{"value":1,"value":2}', '{"value":NaN}', '{"value":Infinity}']:
            with self.assertRaises(ValueError): d.strict_json(text)
        self.assertIsNone(n.geometry_value({}, {'measurement': 'layout_box'}, 'ios'))
        self.assertIsNone(n.geometry_value({}, {'measurement': 'layout_box'}, 'android'))

    def test_trusted_mode_cannot_be_downgraded_by_stripping_metadata(self):
        plan, _ = self.compile(); del plan['design_contract']
        with self.assertRaises(ValueError): n.evaluate(plan, {}, 'android', design_lock=self.lock, design_sha256=self.sha)
        with self.assertRaises(ValueError): n.evaluate(plan, {}, 'android', design_sha256=self.sha)


if __name__ == '__main__': unittest.main()
