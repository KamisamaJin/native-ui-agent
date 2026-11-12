import copy
import unittest
from metric_rules import summarize


def fixture():
    cases = []
    mapping = {}
    for i in range(1, 6):
        key = f'Case0{i}'; mapping[key] = {'A': 'X', 'B': 'Y'}
        version = {'initial_relations': [], 'defect_alarms': [], 'attempted_repairs': [],
                   'new_regressions': [], 'unresolved_regressions': [], 'positive_validation_claims': [],
                   'unresolved_quality': [], 'public_wall_seconds': i * 10,
                   'hidden_validation_wall_seconds': 3,
                   'delivery_obligations': {k: True for k in ['public_current_all_must_passed',
                       'private_current_all_must_passed', 'source_all_must_passed',
                       'owned_resources_closed', 'independent_quality_complete']}}
        cases.append({'case_id': key, 'confirmed_initial_causes': [],
                      'versions': {'X': copy.deepcopy(version), 'Y': copy.deepcopy(version)}})
    return cases, mapping


class Metrics(unittest.TestCase):
    def test_zero_defects_and_alarms_are_na_not_invented(self):
        c, m = fixture(); r = summarize(c, 'A', m)
        self.assertIsNone(r['repair_fraction']['value'])
        self.assertIsNone(r['false_discovery_fraction']['value'])
        self.assertEqual(r['complete_delivery_fraction']['value'], 1)

    def test_cost_includes_all_failed_attempts(self):
        c, m = fixture()
        for row in c[1:]: row['versions']['X']['delivery_obligations']['private_current_all_must_passed'] = False
        r = summarize(c, 'A', m)
        self.assertEqual(r['cost']['successful_delivery_seconds'], 150)
        self.assertEqual(r['cost']['combined_successful_delivery_seconds'], 165)
        self.assertEqual(r['complete_delivery_fraction']['value'], .2)

    def test_zero_delivery_cost_is_na(self):
        c, m = fixture()
        for row in c: row['versions']['X']['delivery_obligations']['source_all_must_passed'] = False
        r = summarize(c, 'A', m)
        self.assertEqual(r['cost']['all_attempt_public_seconds'], 150)
        self.assertIsNone(r['cost']['successful_delivery_seconds'])

    def test_unknown_is_not_removed_or_delivery(self):
        c, m = fixture(); c[0]['confirmed_initial_causes'] = [{'id': 'a'}]
        c[0]['versions']['X']['initial_relations'] = [{'initial_cause_id': 'a', 'status': 'unresolved', 'evidence': ['raw']}]
        r = summarize(c, 'A', m)
        self.assertEqual(r['repair_fraction']['value'], 0)
        self.assertEqual(r['unresolved_initial_relation_fraction']['value'], 1)
        self.assertEqual(r['counts']['delivered'], 4)

    def test_removed_without_detection_stays_removed(self):
        c, m = fixture(); c[0]['confirmed_initial_causes'] = [{'id': 'a'}]
        c[0]['versions']['X']['initial_relations'] = [{'initial_cause_id': 'a', 'status': 'removed', 'evidence': ['raw']}]
        r = summarize(c, 'A', m)
        self.assertEqual(r['repair_fraction']['value'], 1)
        self.assertEqual(r['initial_detection_fraction']['value'], 0)

    def test_alarm_classes_and_repeated_repairs_have_distinct_denominators(self):
        c, m = fixture(); c[0]['confirmed_initial_causes'] = [{'id': 'a'}, {'id': 'b'}]
        v = c[0]['versions']['X']
        v['initial_relations'] = [{'initial_cause_id': 'a', 'status': 'removed', 'evidence': ['raw']},
                                 {'initial_cause_id': 'b', 'status': 'present', 'evidence': ['raw']}]
        v['defect_alarms'] = [{'id': 'd1', 'verdict': 'true', 'initial_cause_ids': ['a']},
                              {'id': 'd2', 'verdict': 'false', 'initial_cause_ids': []},
                              {'id': 'd3', 'verdict': 'unresolved', 'initial_cause_ids': []}]
        v['positive_validation_claims'] = [{'id': 'p1', 'verdict': 'false'}]
        v['attempted_repairs'] = [{'id': 'r1', 'initial_cause_ids': ['a'], 'evidence': ['patch']},
                                 {'id': 'r2', 'initial_cause_ids': ['a'], 'evidence': ['patch']}]
        r = summarize(c, 'A', m)
        self.assertEqual(r['false_discovery_fraction']['value'], .5)
        self.assertEqual(r['counts']['unresolved_alarm'], 1)
        self.assertEqual(r['counts']['false_positive_validation'], 1)
        self.assertEqual(r['attempted_repair_fraction'], {'numerator': 1, 'denominator': 1, 'value': 1})

    def test_regressions_block_otherwise_passing_delivery(self):
        c, m = fixture(); c[0]['versions']['X']['new_regressions'] = [{'id': 'new', 'evidence': ['raw']}]
        r = summarize(c, 'A', m)
        self.assertEqual(r['counts']['regression'], 1)
        self.assertEqual(r['counts']['delivered'], 4)

    def test_missing_cause_relation_rejected(self):
        c, m = fixture(); c[0]['confirmed_initial_causes'] = [{'id': 'a'}]
        with self.assertRaises(ValueError): summarize(c, 'A', m)

    def test_invalid_clock_not_clamped(self):
        for invalid in [-.1, float('nan'), float('inf'), True]:
            c, m = fixture(); c[0]['versions']['X']['public_wall_seconds'] = invalid
            with self.assertRaises(ValueError): summarize(c, 'A', m)

    def test_four_tasks_or_duplicate_units_rejected(self):
        c, m = fixture()
        with self.assertRaises(ValueError): summarize(c[:-1], 'A', m)
        c[0]['versions']['X']['defect_alarms'] = [{'id': 'd', 'verdict': 'false', 'initial_cause_ids': []}] * 2
        with self.assertRaises(ValueError): summarize(c, 'A', m)

    def test_unknown_cannot_receive_detection_credit(self):
        c, m = fixture(); c[0]['confirmed_initial_causes'] = [{'id': 'a'}]
        v = c[0]['versions']['X']; v['initial_relations'] = [{'initial_cause_id': 'a', 'status': 'present', 'evidence': ['raw']}]
        v['defect_alarms'] = [{'id': 'd', 'verdict': 'unresolved', 'initial_cause_ids': ['a']}]
        with self.assertRaises(ValueError): summarize(c, 'A', m)


if __name__ == '__main__': unittest.main(verbosity=2)
