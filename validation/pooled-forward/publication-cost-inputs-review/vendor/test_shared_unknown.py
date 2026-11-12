import ast
import copy
import importlib.util
from pathlib import Path
import unittest

import metric_rules_v3 as new


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('original_cost_v2', HERE / 'upstream/metric_rules_v2.py')
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)


def fixture():
    # Reuse only the original generic fixture function, without executing its
    # test module's import-time HOST writer or invoking a study reader.
    text = (HERE / 'upstream/test_metrics_v2.py').read_text()
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == 'fixture')
    environment = {'copy': copy, 'v2': old}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<original-fixture-only>', 'exec'), environment)
    return environment['fixture']()


def run(module, f):
    cases, assignment, registry, shared = f
    return module.summarize(cases, 'A', assignment, shared_costs=shared, coverage_denominators=registry)


class Costs(unittest.TestCase):
    def test_all_measured_preserves_v2_arithmetic(self):
        f = fixture()
        f[3].update(initial_oracle_seconds=13, design_preparation_seconds=7,
                    common_infrastructure_seconds=19, independent_grading_matcher_seconds=11)
        a, b = run(old, f), run(new, f)
        for key in a:
            if key not in {'version', 'scope', 'cost'}: self.assertEqual(a[key], b[key])
        self.assertEqual(a['cost'], {k: v for k, v in b['cost'].items()
                                    if k not in {'known_shared_cost_subtotal_seconds', 'unknown_shared_cost_categories'}})

    def test_one_unknown_retains_null_and_known_subtotal(self):
        f = fixture(); f[3].update(design_preparation_seconds=None, initial_oracle_seconds=12)
        value = run(new, f)['cost']
        self.assertIsNone(value['shared_cost_total_seconds'])
        self.assertIsNone(value['shared_costs_reported_separately']['design_preparation_seconds'])
        self.assertEqual(value['unknown_shared_cost_categories'], ['design_preparation_seconds'])
        self.assertEqual(value['known_shared_cost_subtotal_seconds'], 12)
        self.assertEqual(value['all_attempt_public_seconds'], 150)
        self.assertEqual(value['hidden_validation_seconds'], 15)

    def test_all_unknown_is_not_zero_total(self):
        f = fixture()
        for k in f[3]: f[3][k] = None
        value = run(new, f)
        self.assertEqual(value['counts']['delivered'], 5)
        self.assertIsNone(value['cost']['shared_cost_total_seconds'])
        self.assertEqual(len(value['cost']['unknown_shared_cost_categories']), 4)

    def test_unknown_cannot_replace_own_or_hidden_cost(self):
        for field in ['public_wall_seconds', 'hidden_validation_wall_seconds']:
            f = fixture(); f[0][0]['versions']['X'][field] = None
            with self.assertRaises(ValueError): run(new, f)

    def test_invalid_known_values_or_missing_categories_reject(self):
        for invalid in [-1, True, 'unknown', float('inf'), float('nan')]:
            f = fixture(); f[3]['design_preparation_seconds'] = invalid
            with self.assertRaises(ValueError): run(new, f)
        f = fixture(); del f[3]['design_preparation_seconds']
        with self.assertRaises(ValueError): run(new, f)

    def test_overflow_rejects_even_with_an_unknown_category(self):
        f = fixture(); keys = list(f[3]); f[3][keys[0]] = None
        f[3][keys[1]] = f[3][keys[2]] = 1e308
        with self.assertRaises(ValueError): run(new, f)

    def test_quality_u_and_na_rules_stay_strict(self):
        f = fixture(); f[3]['design_preparation_seconds'] = None
        row = f[0][0]['versions']['X']['mandatory_coverage'][0]
        row['unassessed_ids'] = row['passed_ids']; row['passed_ids'] = []
        with self.assertRaises(ValueError): run(new, f)
        f[0][0]['versions']['X']['delivery_obligations']['public_current_all_must_passed'] = False
        value = run(new, f)
        self.assertEqual(value['counts']['delivered'], 4)
        self.assertEqual(value['mandatory_coverage']['counts']['unassessed'], 1)

    def test_input_is_unchanged(self):
        f = fixture(); f[3]['design_preparation_seconds'] = None; before = copy.deepcopy(f)
        run(new, f); self.assertEqual(f, before)


if __name__ == '__main__': unittest.main()
