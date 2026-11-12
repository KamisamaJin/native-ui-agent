import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'native-ui-agent/tests'))
sys.path.insert(0, str(HERE))
import source_only_binding as subject
import test_managed_execution as original_fixtures


class SourceOnlyControls(unittest.TestCase):
    def fixture(self):
        fixture = original_fixtures.ResponsibilityTests('runTest'); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config, plan, lock = fixture.config()
        root = Path(fixture.temp.name).resolve()
        actual = {'version': 1, 'observations': [{'id': 'binding', 'observed': True,
            'reason': 'Actual approved bridge implementation.', 'citations': [{'path': config['bridge'], 'line': 1}]}]}
        return root, config, actual, original_fixtures.er

    def test_conflicting_original_store_is_preserved_and_does_not_override_independent_actual(self):
        root, config, actual, backend = self.fixture()
        old = copy.deepcopy(actual); old['observations'][0]['observed'] = False
        backend.bind(config, old, root/'original-receipt.json')
        original_bytes = {str(p): p.read_bytes() for p in Path(config['source_review_store']).glob('*')}
        before = copy.deepcopy(config)
        result = subject.bind_source(config, actual, root/'independent', backend)
        value = json.loads(Path(result['evaluation']).read_bytes())
        self.assertEqual(value['rows'][0]['status'], 'passed')
        self.assertFalse(value['original_public_gate_promoted']); self.assertFalse(value['current_delivery_verified'])
        self.assertEqual(config, before)
        self.assertEqual({str(p): p.read_bytes() for p in Path(config['source_review_store']).glob('*')}, original_bytes)
        self.assertEqual(backend.evaluate(config, backend.compile_contract(config, backend.d.load(Path(config['plan'])), backend.d.load(Path(config['design_lock']))))['rows'][0]['status'], 'failed')

    def test_false_and_unknown_actuals_remain_false_and_unknown(self):
        for index, actual_value in enumerate([False, None]):
            root, config, actual, backend = self.fixture(); actual['observations'][0]['observed'] = actual_value
            result = subject.bind_source(config, actual, root/('separate-' + str(index)), backend)
            row = json.loads(Path(result['evaluation']).read_bytes())['rows'][0]
            self.assertEqual(row['status'], 'failed' if actual_value is False else 'unassessed')
            self.assertIs(row['actual'], actual_value)

    def test_source_store_is_only_config_change_and_cannot_enter_old_store_or_production(self):
        root, config, actual, backend = self.fixture()
        derived = subject.isolated_config(config, root/'view')
        self.assertEqual({k for k in set(config)|set(derived) if config.get(k) != derived.get(k)}, {'source_review_store'})
        for bad in [Path(config['source_review_store'])/'nested', Path(config['source_roots'][0])/'nested']:
            with self.assertRaises(ValueError): subject.isolated_config(config, bad)

    def test_expectation_override_wrong_subject_and_reused_output_are_rejected(self):
        for index, change in enumerate(['expectation', 'foreign', 'reuse']):
            root, config, actual, backend = self.fixture(); output = root/('case-' + str(index))
            if change == 'expectation': actual['observations'][0]['expected'] = False
            elif change == 'foreign': actual['observations'][0]['citations'][0]['path'] = config['source_roots'][0]
            else: output.mkdir()
            with self.assertRaises(ValueError): subject.bind_source(config, actual, output, backend)

    def test_subject_drift_after_bind_aborts_before_evaluation(self):
        root, config, actual, backend = self.fixture()
        class DriftingBackend:
            d = backend.d
            compile_contract = staticmethod(backend.compile_contract)
            evaluate = staticmethod(backend.evaluate)
            @staticmethod
            def bind(config, submission, output):
                value = backend.bind(config, submission, output)
                Path(config['bridge']).write_text('changed actual source')
                return value
        with self.assertRaisesRegex(ValueError, 'subject bytes changed'):
            subject.bind_source(config, actual, root/'drift', DriftingBackend)


if __name__ == '__main__': unittest.main(verbosity=2)
