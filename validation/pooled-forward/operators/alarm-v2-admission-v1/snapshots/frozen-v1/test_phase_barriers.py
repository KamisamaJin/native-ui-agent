import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from phase_barriers import GROUPS, make_index, verify_index


class Reader:
    def read_bytes(self, p): return Path(p).read_bytes()
    def read_json(self, p): return json.loads(self.read_bytes(p))
    def directory(self, p): return Path(p)


class Barriers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='barrier-host-')
        self.root = Path(self.temp.name)
        self.reader = Reader(); self.rows = []
        for group in sorted(GROUPS):
            seals = {}
            for judge in ['J1', 'J2']:
                folder = self.root / group / judge
                grade = self.put(folder / 'grade.json', {'anonymous_group': group, 'judge_id': judge,
                                 'scope': 'Synthetic metadata only, no product result'})
                seals[judge] = self.put(folder / 'SEAL.json', {'version': 1, 'kind': 'independent-blind-cause-grade-seal',
                                       'anonymous_group': group, 'judge_id': judge, 'files': {'grade.json': grade['sha256']}})
            end = self.put(self.root / group / 'episode/END.json', {'anonymous_group': group, 'grade_seals': seals})
            input_ref = self.put(self.root / group / 'input/SEAL.json', {'kind': 'anonymous-fixed-version-input-seal', 'anonymous_group': group})
            self.rows.append({'group': group, 'actors': {j: '/root/synthetic_' + group + '_' + j for j in ['J1', 'J2']},
                              'seals': seals, 'inputs': [input_ref], 'episode_end': end, 'fork_turns': 'none', 'model_override': None})

    def tearDown(self): self.temp.cleanup()
    def put(self, p, value):
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(value, sort_keys=True) + '\n')
        return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    def index(self, rows=None):
        value = make_index(self.reader, self.rows if rows is None else rows)
        return self.put(self.root / 'INDEX.json', value)

    def test_all_thirty_review_records_not_quality_pass(self):
        ref = self.index(); result = verify_index(self.reader, ref)
        self.assertEqual(result['distinct_contexts'], 30)
        self.assertFalse(self.reader.read_json(ref['path'])['product_quality_verified'])

    def test_incomplete_groups_cannot_start_alarm_phase(self):
        with self.assertRaises(ValueError): verify_index(self.reader, self.index(self.rows[:-1]))

    def test_context_reuse_across_versions_rejected(self):
        rows = copy.deepcopy(self.rows); rows[1]['actors']['J1'] = rows[0]['actors']['J1']
        with self.assertRaises(ValueError): verify_index(self.reader, self.index(rows))

    def test_wrong_external_pin_rejected(self):
        ref = self.index(); ref['sha256'] = '0' * 64
        with self.assertRaises(ValueError): verify_index(self.reader, ref)

    def test_changed_sealed_review_rejected(self):
        ref = self.index(); (self.root / sorted(GROUPS)[0] / 'J1/grade.json').write_text('{}')
        with self.assertRaises(ValueError): verify_index(self.reader, ref)

    def test_unsealed_extra_output_rejected(self):
        ref = self.index(); (self.root / sorted(GROUPS)[0] / 'J1/extra.json').write_text('{}')
        with self.assertRaises(ValueError): verify_index(self.reader, ref)

    def test_alarm_barrier_requires_original_cause_barrier(self):
        with self.assertRaises(ValueError): make_index(self.reader, self.rows, 'alarm')

    def test_handwritten_alarm_index_cannot_skip_first_barrier(self):
        value = make_index(self.reader, self.rows); value['kind'] = 'global-independent-alarm-grade-barrier'
        ref = self.put(self.root / 'alarm.json', value)
        with self.assertRaisesRegex(ValueError, 'first-cause'):
            verify_index(self.reader, ref, 'alarm')

    def test_missing_input_seal_is_not_a_valid_barrier(self):
        rows = copy.deepcopy(self.rows); rows[0]['inputs'] = []
        with self.assertRaisesRegex(ValueError, 'input references'):
            verify_index(self.reader, self.index(rows))


if __name__ == '__main__': unittest.main(verbosity=2)
