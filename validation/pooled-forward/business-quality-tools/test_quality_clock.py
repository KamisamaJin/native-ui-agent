import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

from quality_clock import BASIS, interval, point


class Clocks(unittest.TestCase):
    def test_recorded_shared_clock_wins_over_small_process_difference(self):
        a = {'started_at_unix': 1000, 'started_at_clock_gettime': 2000, 'started_at_monotonic': .04, 'shared_clock_basis': BASIS}
        b = {'finished_at_unix': 1600, 'finished_at_clock_gettime': 2600, 'finished_at_monotonic': .08, 'shared_clock_basis': BASIS}
        self.assertEqual(interval(a, b)['wall_seconds'], 600)

    def test_old_unix_endpoints_recover_cross_process_cost(self):
        d = interval({'started_at_unix': 1000, 'started_at_monotonic': 20},
                     {'finished_at_unix': 1600, 'finished_at_monotonic': .01, 'wall_seconds': 0})
        self.assertEqual(d['wall_seconds'], 600)
        self.assertLess(d['raw_process_monotonic_delta_not_comparable'], 0)
        self.assertEqual(d['original_reported_wall_seconds'], 0)
        self.assertIn('fallback', d['limitation'])

    def test_invalid_shared_clock_does_not_silently_use_unix(self):
        with self.assertRaises(ValueError):
            interval({'started_at_unix': 1000, 'started_at_clock_gettime': 20, 'shared_clock_basis': BASIS},
                     {'finished_at_unix': 1100, 'finished_at_clock_gettime': 10, 'shared_clock_basis': BASIS})

    def test_negative_unix_not_clamped_to_zero(self):
        with self.assertRaises(ValueError):
            interval({'started_at_unix': 1000}, {'finished_at_unix': 999})

    def test_nonfinite_and_boolean_times_rejected(self):
        for bad in [float('nan'), float('inf'), True, '10']:
            with self.assertRaises(ValueError):
                interval({'started_at_unix': bad}, {'finished_at_unix': 1100})

    def test_points_are_shared_across_independent_python_processes(self):
        module = Path(__file__).resolve().parent
        code = 'import sys,json;sys.path.insert(0,sys.argv[1]);from quality_clock import point;print(json.dumps(point("started")))'
        before = time.clock_gettime(time.CLOCK_MONOTONIC)
        outputs = [json.loads(subprocess.check_output([sys.executable, '-B', '-c', code, str(module)], text=True)) for _ in range(2)]
        after = time.clock_gettime(time.CLOCK_MONOTONIC)
        for row in outputs:
            self.assertEqual(row['shared_clock_basis'], BASIS)
            self.assertLessEqual(before, row['started_at_clock_gettime'])
            self.assertLessEqual(row['started_at_clock_gettime'], after)
        self.assertNotEqual(outputs[0]['started_process_id'], outputs[1]['started_process_id'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
