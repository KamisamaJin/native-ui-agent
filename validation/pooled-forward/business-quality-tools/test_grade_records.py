import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import grade_records as ops
from quality_clock import BASIS


class Ledgers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grade-ledger-host-')
        self.root = Path(self.temp.name).resolve()
        self.episode = self.root / 'episode'
        ops.save(self.episode / 'START.json', {'anonymous_group': 'Case03-I', 'judges': ['J1', 'J2'],
                 'started_at_unix': 1000, 'started_at_monotonic': .2,
                 'started_at_clock_gettime': 5000, 'shared_clock_basis': BASIS})
        self.seals = {}
        for judge in ['J1', 'J2']:
            folder = self.root / judge
            ops.save(folder / 'grade.json', {'version': 1, 'anonymous_group': 'Case03-I', 'judge_id': judge,
                     'scope': 'Synthetic HOST: contents are not product judgments.'})
            ops.save(folder / 'SEAL.json', {'version': 1, 'kind': 'independent-blind-cause-grade-seal',
                     'anonymous_group': 'Case03-I', 'judge_id': judge, 'files': {'grade.json': ops.sha(folder / 'grade.json')}})
            self.seals[judge] = ops.ref(folder / 'SEAL.json')

    def tearDown(self):
        self.temp.cleanup()

    def close(self):
        with patch.object(ops, 'point', return_value={'finished_at_unix': 1600, 'finished_at_monotonic': .01,
                         'finished_at_clock_gettime': 5600, 'shared_clock_basis': BASIS}):
            return ops.close_pair(self.episode, 'Case03-I', self.seals)

    def test_pair_clock_not_sum_of_parallel_reviewers(self):
        result = self.close()
        self.assertEqual(result['wall_seconds'], 600)
        self.assertEqual(result['basis'], BASIS)

    def test_only_one_judge_cannot_close(self):
        del self.seals['J2']
        with self.assertRaises(ValueError):
            self.close()

    def test_foreign_grade_not_a_second_context(self):
        self.seals['J2'] = self.seals['J1']
        with self.assertRaises(ValueError):
            self.close()

    def test_changed_sealed_member_rejected(self):
        p = self.root / 'J1/grade.json'; p.chmod(0o644); p.write_text('{}')
        with self.assertRaises(ValueError):
            self.close()

    def test_unsealed_output_rejected(self):
        (self.root / 'J1/extra.json').write_text('{}')
        with self.assertRaises(ValueError):
            self.close()

    def test_submitted_writable_member_rejected(self):
        (self.root / 'J1/grade.json').chmod(0o644)
        with self.assertRaises(ValueError):
            self.close()

    def test_prior_terminal_record_not_overwritten(self):
        self.close()
        with self.assertRaises(FileExistsError):
            self.close()

    def test_clock_correction_preserves_original_bytes(self):
        ep = self.root / 'legacy'
        ops.save(ep / 'START.json', {'started_at_unix': 1000, 'started_at_monotonic': 300})
        ops.save(ep / 'END.json', {'finished_at_unix': 1600, 'finished_at_monotonic': .1, 'wall_seconds': -.1})
        pins = [ops.sha(ep / n) for n in ['START.json', 'END.json']]
        result = ops.correct_episode(ep)
        self.assertEqual(result['interval']['wall_seconds'], 600)
        self.assertEqual([ops.sha(ep / n) for n in ['START.json', 'END.json']], pins)
        with self.assertRaises(FileExistsError):
            ops.correct_episode(ep)

    def test_split_correction_keeps_wait_separate(self):
        ep = self.root / 'legacy-split'; second = self.root / 'supplement'
        ops.save(ep / 'START.json', {'started_at_unix': 1000, 'started_at_monotonic': .1})
        ops.save(ep / 'ORIGINAL-END.json', {'finished_at_unix': 1600, 'finished_at_monotonic': .01, 'wall_seconds': -.09})
        ops.save(second / 'START.json', {'started_at_unix': 1900, 'started_at_monotonic': .05})
        ops.save(second / 'END.json', {'start': ops.ref(second / 'START.json'), 'finished_at_unix': 2500, 'finished_at_monotonic': .04, 'wall_seconds': -.01})
        ops.save(ep / 'END.json', {'original_episode': ops.ref(ep / 'ORIGINAL-END.json'),
                 'complete_input_supplement_episode': ops.ref(second / 'END.json'), 'active_episode_wall_seconds': -.1,
                 'inter_episode_research_wait_seconds': .03})
        prior = ops.sha(ep / 'END.json'); result = ops.correct_split_cause(ep)
        self.assertEqual(result['active_seconds'], 1200)
        self.assertEqual(result['research_wait_seconds'], 300)
        self.assertEqual(ops.sha(ep / 'END.json'), prior)


if __name__ == '__main__':
    unittest.main(verbosity=2)
