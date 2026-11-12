import copy
import unittest

from anonymous_projection import project, strict_json


class Projection(unittest.TestCase):
    def test_exact_identity_path_and_all_verdict_actual_rows_preserved(self):
        original = {'arm': 'B', 'operations': {'seconds': 50}, 'assertions': [
            {'id': 'x', 'status': 'F', 'expected': '#123456', 'actual': '#654321',
             'reason': 'Original /Users/rex/work/capture/frame.png'}]}
        before = copy.deepcopy(original)
        value, ledger = project(original, omit_top_level=['arm', 'operations'],
            replacements=[{'original': '/Users/rex/work/capture', 'anonymous': 'observations/native'}],
            rewrite_pointers=['/assertions/0/reason'])
        self.assertEqual(value['assertions'][0], dict(original['assertions'][0], reason='Original observations/native/frame.png'))
        self.assertEqual(original, before)
        self.assertEqual(len(ledger['identity_metadata_changes']), 1)

    def test_arbitrary_color_substitution_forbidden(self):
        with self.assertRaises(ValueError):
            project({'actual': '#123456'}, replacements=[{'original': '#123456', 'anonymous': '#000000'}])

    def test_measurement_and_expected_omission_forbidden(self):
        for key in ['actual', 'expected', 'assertions', 'status', 'reason', 'issues', 'source_observations']:
            with self.assertRaises(ValueError):
                project({key: None}, omit_top_level=[key])

    def test_identity_token_in_actual_text_is_not_rewritten(self):
        with self.assertRaises(ValueError):
            project({'actual': 'candidate-v13.9'}, replacements=[{'original': 'candidate-v13.9', 'anonymous': 'frozen-tool'}], rewrite_pointers=['/actual'])

    def test_unlisted_or_incomplete_identity_rewrite_fails_closed(self):
        with self.assertRaises(ValueError):
            project({'reason': '/Users/rex/other/file'}, replacements=[{'original': '/Users/rex/work', 'anonymous': 'own'}])

    def test_absent_pointer_not_ignored(self):
        with self.assertRaises(ValueError):
            project({'reason': 'ok'}, rewrite_pointers=['/missing/path'])

    def test_native_numbers_booleans_null_and_order_are_exact(self):
        original = {'assertions': [{'actual': False}, {'actual': None}, {'actual': 1.0000000000000002}],
                    'issues': [{'reason': 'Native limitation, not a product verdict'}]}
        value, ledger = project(original)
        self.assertEqual(value, original)
        self.assertEqual(ledger['identity_metadata_changes'], [])

    def test_json_duplicate_and_nonfinite_rejected(self):
        for raw in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with self.assertRaises(ValueError):
                strict_json(raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
