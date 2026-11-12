import copy
import unittest
from coverage_registry import registry


def fixture():
    tasks = ['task%d' % i for i in range(5)]
    cells = []
    for t in tasks:
        for p in ['ios', 'android']:
            for f in ['public', 'private']:
                for kind, rule, disposition in [('control', 'enabled', 'required'), ('text_layout', 'computed-font', 'N/A'),
                                                ('source', 'api', 'required-source-review')]:
                    cells.append(dict(task=t, platform=p, family=f, state='ready', rule_id=rule,
                                      kind=kind, disposition=disposition))
    return tasks, cells


class RegistryTests(unittest.TestCase):
    def test_exact_all_cells_and_no_invented_pass(self):
        tasks, cells = fixture(); before = copy.deepcopy(cells)
        result = registry(cells, tasks, ['frozen'])
        self.assertEqual(cells, before)
        for case in result.values():
            self.assertEqual(case['X'], case['Y'])
            self.assertEqual(sum(len(r['applicable_ids']) for r in case['X']), 8)
            self.assertEqual(sum(len(r['not_applicable_ids']) for r in case['X']), 4)
            self.assertFalse(any('passed_ids' in r for r in case['X']))

    def test_duplicate_or_missing_platform_rejected(self):
        tasks, cells = fixture()
        with self.assertRaises(ValueError): registry(cells + [cells[0]], tasks, ['frozen'])
        with self.assertRaises(ValueError): registry([c for c in cells if c['platform'] != 'ios'], tasks, ['frozen'])

    def test_source_cannot_be_native_or_na(self):
        tasks, cells = fixture()
        for wrong in ['required', 'N/A']:
            changed = copy.deepcopy(cells)
            next(c for c in changed if c['kind'] == 'source')['disposition'] = wrong
            with self.assertRaises(ValueError): registry(changed, tasks, ['frozen'])

    def test_wrong_identity_or_unknown_task_rejected(self):
        tasks, cells = fixture(); cells[0]['assertion_id'] = 'different/thing'
        with self.assertRaises(ValueError): registry(cells, tasks, ['frozen'])
        tasks, cells = fixture(); cells[0]['task'] = 'unsealed-task'
        with self.assertRaises(ValueError): registry(cells, tasks, ['frozen'])


if __name__ == '__main__': unittest.main()
