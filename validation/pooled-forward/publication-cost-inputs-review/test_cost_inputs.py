"""Independent pure synthetic review of nullable shared-cost input only."""
import ast
import copy
import importlib.util
import inspect
import itertools
import math
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
OBSERVATIONS = []
CATEGORIES = ['initial_oracle_seconds', 'design_preparation_seconds',
              'common_infrastructure_seconds', 'independent_grading_matcher_seconds']


def load(name, relative):
    path = HERE/'vendor'/relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


old = load('reviewed_v2_cost_arithmetic', 'upstream/metric_rules_v2.py')
new = load('author_v3_nullable_shared_costs', 'metric_rules_v3.py')
source = (HERE/'vendor/upstream/test_metrics_v2.py').read_bytes()
tree = ast.parse(source)
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'fixture', 'cause', 'provenance'}]
assert {n.name for n in nodes} == {'fixture', 'cause', 'provenance'}
environment = {'copy': copy, 'v2': old}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<only-three-frozen-generic-fixture-functions>', 'exec'), environment)
fixture, cause, provenance = (environment[n] for n in ['fixture', 'cause', 'provenance'])


def run(module, value, arm='A'):
    cases, assignment, registry, shared = value
    return module.summarize(cases, arm, assignment, shared_costs=shared, coverage_denominators=registry)


def common_output(value):
    out = copy.deepcopy(value)
    out.pop('version');out.pop('scope')
    for field in ['known_shared_cost_subtotal_seconds', 'unknown_shared_cost_categories']:
        out['cost'].pop(field, None)
    return out


class CostInputsReview(unittest.TestCase):
    def test_01_only_declared_ast_and_api_changes(self):
        a = ast.parse((HERE/'vendor/upstream/metric_rules_v2.py').read_bytes())
        b = ast.parse((HERE/'vendor/metric_rules_v3.py').read_bytes())
        b.body[0] = copy.deepcopy(a.body[0])  # The declared module description.
        fa = next(n for n in a.body if isinstance(n, ast.FunctionDef) and n.name == 'summarize')
        fb = next(n for n in b.body if isinstance(n, ast.FunctionDef) and n.name == 'summarize')
        old_assignments = {n.targets[0].id: n for n in fa.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
        body = []
        for node in fb.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name in {'unknown_shared', 'known_shared_total'}:
                    continue
                if name in {'shared', 'shared_total'}:
                    node = copy.deepcopy(old_assignments[name])
            body.append(node)
        fb.body = body
        ra, rb = fa.body[-1].value, fb.body[-1].value
        old_values = {k.value: v for k, v in zip(ra.keys, ra.values)}
        for i, key in enumerate(rb.keys):
            if key.value in {'version', 'scope'}:
                rb.values[i] = copy.deepcopy(old_values[key.value])
            if key.value == 'cost':
                d = rb.values[i]
                pairs = [(k, v) for k, v in zip(d.keys, d.values) if k.value not in
                         {'known_shared_cost_subtotal_seconds', 'unknown_shared_cost_categories'}]
                d.keys, d.values = [k for k, v in pairs], [v for k, v in pairs]
        self.assertEqual(ast.dump(a, include_attributes=False), ast.dump(b, include_attributes=False))
        for function in ['summarize', 'coverage', 'provenance', 'seconds', 'total', 'fraction', 'unique']:
            self.assertEqual(inspect.signature(getattr(old, function)), inspect.signature(getattr(new, function)))
        self.assertEqual(old.GATES, new.GATES)
        OBSERVATIONS.append({'control': self.id(), 'result': 'Exact AST equality after reverting only declared nullable-shared block, two cost fields, version/scope/module description; APIs unchanged.'})

    def test_02_measured_finite_v2_equivalence_both_arms(self):
        for measured in [[0, 0, 0, 0], [13.25, 7.5, 0, 19], [1e-300, 2e99, 123.456, .125]]:
            f = fixture();f[3].update(zip(CATEGORIES, measured))
            for i, case in enumerate(f[0], 1):
                case['versions']['Y']['public_wall_seconds'] = i*11.5
                case['versions']['Y']['hidden_validation_wall_seconds'] = i*.25
                if i % 2:f[1][case['case_id']] = {'A': 'Y', 'B': 'X'}
            for arm in ['A', 'B']:
                a, b = run(old, f, arm), run(new, f, arm)
                self.assertEqual(common_output(a), common_output(b))
                self.assertEqual(b['cost']['known_shared_cost_subtotal_seconds'], a['cost']['shared_cost_total_seconds'])
                self.assertEqual(b['cost']['unknown_shared_cost_categories'], [])
        OBSERVATIONS.append({'control': self.id(), 'result': 'Six fixed measured-cost/both-arm comparisons match every prior output field except declared version/scope additions.'})

    def test_03_all_sixteen_unknown_patterns_exact_subtotal_and_sorted_categories(self):
        for unknown_bits in itertools.product([False, True], repeat=4):
            f = fixture();known = [3, 7.25, 0, 11]
            f[3].update({k: None if unknown else value for k, value, unknown in zip(CATEGORIES, known, unknown_bits)})
            result = run(new, f)['cost']
            expected_unknown = sorted(k for k, unknown in zip(CATEGORIES, unknown_bits) if unknown)
            subtotal = math.fsum(v for v, unknown in zip(known, unknown_bits) if not unknown)
            self.assertEqual(result['unknown_shared_cost_categories'], expected_unknown)
            self.assertEqual(result['known_shared_cost_subtotal_seconds'], subtotal)
            self.assertEqual(result['shared_cost_total_seconds'], None if expected_unknown else subtotal)
            self.assertEqual(result['shared_costs_reported_separately'], f[3])

    def test_04_unknown_and_measured_zero_remain_distinct(self):
        f = fixture();zero = run(new, f)['cost']
        f[3].update(dict.fromkeys(CATEGORIES, None));unknown = run(new, f)['cost']
        self.assertEqual(zero['shared_cost_total_seconds'], 0)
        self.assertEqual(zero['unknown_shared_cost_categories'], [])
        self.assertIsNone(unknown['shared_cost_total_seconds'])
        self.assertEqual(unknown['known_shared_cost_subtotal_seconds'], 0)
        self.assertEqual(len(unknown['unknown_shared_cost_categories']), 4)
        OBSERVATIONS.append({'control': self.id(), 'measured_zero_cost': zero, 'all_unknown_cost': unknown,
                             'meaning': 'Zero empty known subtotal is an accounting identity; the full unknown shared total remains null.'})

    def test_05_v2_rejects_unknown_without_coercing_it_to_zero(self):
        f = fixture();f[3]['design_preparation_seconds'] = None
        with self.assertRaises(ValueError):run(old, f)
        result = run(new, f)
        self.assertIsNone(result['cost']['shared_cost_total_seconds'])
        self.assertIsNone(result['cost']['shared_costs_reported_separately']['design_preparation_seconds'])
        OBSERVATIONS.append({'control': self.id(), 'v2': 'expected nonnegative-finite rejection for explicit unknown', 'v3': 'unknown retained; no numeric replacement'})

    def test_06_invalid_known_shared_inputs_rejected(self):
        for bad in [True, False, -1, 'unknown', 'N/A', [], {}, float('nan'), float('inf'), -float('inf')]:
            f = fixture();f[3]['design_preparation_seconds'] = bad
            with self.assertRaises(ValueError):run(new, f)

    def test_07_missing_extra_and_nonmapping_shared_categories_rejected(self):
        for remove in CATEGORIES:
            f = fixture();f[3].pop(remove)
            with self.assertRaisesRegex(ValueError, 'Explicit separately reported'):run(new, f)
        for bad in [{}, {**dict.fromkeys(CATEGORIES, None), 'invented_category': 0}, None, []]:
            f = fixture();f = (*f[:3], bad)
            with self.assertRaisesRegex(ValueError, 'Explicit separately reported'):run(new, f)

    def test_08_known_subtotal_overflow_rejected_even_with_unknowns(self):
        for unknown in [False, True]:
            f = fixture();f[3].update(zip(CATEGORIES, [1e308, 1e308, None if unknown else 0, 0]))
            with self.assertRaisesRegex(ValueError, 'Aggregate cost exceeds'):run(new, f)

    def test_09_own_and_hidden_still_require_finite_values_both_arms(self):
        for arm, selected in [('A', 'X'), ('B', 'Y')]:
            for field in ['public_wall_seconds', 'hidden_validation_wall_seconds']:
                for bad in [None, True, False, -1, 'unknown', float('inf'), float('nan')]:
                    f = fixture();f[3].update(dict.fromkeys(CATEGORIES, None))
                    f[0][0]['versions'][selected][field] = bad
                    with self.assertRaises(ValueError):run(new, f, arm)

    def test_10_per_arm_and_combined_overflows_unchanged(self):
        for field in ['public_wall_seconds', 'hidden_validation_wall_seconds', 'combined']:
            f = fixture();f[3]['design_preparation_seconds'] = None
            for case in f[0]:
                if field == 'combined':
                    case['versions']['X']['public_wall_seconds'] = 2e307
                    case['versions']['X']['hidden_validation_wall_seconds'] = 2e307
                else:case['versions']['X'][field] = 1e308
            with self.assertRaisesRegex(ValueError, 'Aggregate cost exceeds'):run(new, f)

    def test_11_no_shared_cost_allocation_or_new_denominator(self):
        f = fixture();f[3].update(dict.fromkeys(CATEGORIES, None));result = run(new, f)
        self.assertEqual(result['attempts'], 5)
        self.assertEqual(result['cost']['all_attempt_public_seconds'], 150)
        self.assertEqual(result['cost']['hidden_validation_seconds'], 15)
        self.assertEqual(result['cost']['combined_seconds'], 165)
        self.assertEqual(result['cost']['successful_delivery_seconds'], 30)
        self.assertEqual(result['cost']['combined_successful_delivery_seconds'], 33)
        for field in ['model_billing', 'tokens', 'human_monetary_cost']:
            self.assertIsNone(result['cost'][field])

    def test_12_zero_success_delivery_cost_na_unchanged(self):
        f = fixture();f[3].update(dict.fromkeys(CATEGORIES, None))
        for case in f[0]:case['versions']['X']['delivery_obligations']['independent_quality_complete'] = False
        result = run(new, f)
        self.assertEqual(result['counts']['delivered'], 0)
        self.assertIsNone(result['cost']['successful_delivery_seconds'])
        self.assertIsNone(result['cost']['combined_successful_delivery_seconds'])
        self.assertEqual(result['cost']['all_attempt_public_seconds'], 150)

    def test_13_all_platform_family_u_gates_unchanged(self):
        gates = {'public_native_image': 'public_current_all_must_passed', 'private_native_image': 'private_current_all_must_passed', 'source': 'source_all_must_passed'}
        for index in range(6):
            f = fixture();f[3]['design_preparation_seconds'] = None
            final = f[0][0]['versions']['X'];row = final['mandatory_coverage'][index]
            row['unassessed_ids'] = row['passed_ids'];row['passed_ids'] = []
            with self.assertRaisesRegex(ValueError, 'contradicts frozen mandatory F/U'):run(new, f)
            final['delivery_obligations'][gates[row['family']]] = False
            result = run(new, f)
            self.assertEqual(result['counts']['delivered'], 4)
            self.assertEqual(result['mandatory_coverage']['counts']['unassessed'], 1)
            self.assertEqual(result['mandatory_coverage']['counts']['not_applicable'], 30)

    def test_14_na_and_frozen_denominator_cannot_be_changed(self):
        f = fixture();f[3]['design_preparation_seconds'] = None
        row = f[0][0]['versions']['X']['mandatory_coverage'][0];row['passed_ids'].append(row['not_applicable_ids'][0])
        with self.assertRaisesRegex(ValueError, 'N/A cannot become pass'):run(new, f)
        f = fixture();f[3]['design_preparation_seconds'] = None
        f[0][0]['versions']['X']['mandatory_coverage'].pop()
        with self.assertRaises(ValueError):run(new, f)

    def test_15_visibility_alarm_unknown_and_repair_provenance_unchanged(self):
        f = fixture();f[3]['design_preparation_seconds'] = None;final = cause(f[0])
        final['defect_alarms'] = [
            {'id': 'private-true', 'verdict': 'true', 'initial_cause_ids': ['initial-a'], 'worker_visible': False, 'provenance': provenance('independent_private_after_seal')},
            {'id': 'unresolved', 'verdict': 'unresolved', 'initial_cause_ids': [], 'worker_visible': True, 'provenance': provenance('worker_public')}]
        result = run(new, f)
        self.assertEqual(result['initial_detection_fraction']['value'], 0)
        self.assertEqual(result['alarm_unadjudicated_denominator'], 1)
        self.assertEqual(result['alarm_by_phase']['independent_private_after_seal']['adjudicated_denominator'], 1)
        final['attempted_repairs'] = [{'id': 'hidden-repair', 'initial_cause_ids': ['initial-a'], 'evidence': ['synthetic'],
                                     'worker_visible': False, 'provenance': provenance('independent_private_after_seal')}]
        with self.assertRaisesRegex(ValueError, 'worker-public action'):run(new, f)

    def test_16_unresolved_quality_or_null_inventory_not_delivery(self):
        f = fixture();f[3]['design_preparation_seconds'] = None
        final = f[0][0]['versions']['X'];final['unresolved_quality'] = ['synthetic pending quality']
        self.assertEqual(run(new, f)['counts']['delivered'], 4)
        final['unresolved_quality'] = None
        with self.assertRaisesRegex(ValueError, 'null is not complete'):run(new, f)

    def test_17_input_preserved_and_returned_shared_dict_independent(self):
        f = fixture();f[3]['design_preparation_seconds'] = None;before = copy.deepcopy(f)
        result = run(new, f)
        self.assertEqual(f, before)
        result['cost']['shared_costs_reported_separately']['design_preparation_seconds'] = 99
        self.assertEqual(f, before)


if __name__ == '__main__':unittest.main(verbosity=2)
