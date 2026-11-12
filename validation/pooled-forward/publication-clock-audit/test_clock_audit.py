"""Bounded synthetic hostile controls; no original data/grade body needed."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from clock_audit import (BASIS, SnapshotReader, check_correction, digest,
                         future_cost, gap, interval, parse, pinned, summarize, union)


def helper(a=100, b=160):
    return ({'started_at_unix': 1000, 'started_at_clock_gettime': a,
             'started_at_monotonic': .1, 'started_process_id': 101, 'shared_clock_basis': BASIS},
            {'finished_at_unix': 1060, 'finished_at_clock_gettime': b,
             'finished_at_monotonic': .2, 'finished_process_id': 202, 'shared_clock_basis': BASIS})


def row(name, a, b, seconds=None):
    return {'id': name, 'interval': {'status': 'measured', 'started_at_unix': a,
            'finished_at_unix': b, 'duration_seconds': b-a if seconds is None else seconds}}


class Memory:
    def __init__(self):
        self.values = {}

    def put(self, path, value):
        data = json.dumps(value, sort_keys=True).encode()
        self.values[path] = data
        return {'path': path, 'sha256': digest(data)}

    def read_bytes(self, path):
        if path not in self.values:
            raise ValueError('Missing original key')
        return self.values[path]


class ClockControls(unittest.TestCase):
    def test_kernel_different_processes_is_comparable(self):
        a, b = helper()
        self.assertEqual(interval(a, b, mode='helper')['duration_seconds'], 60)

    def test_source_bound_v3_alias_is_used(self):
        a = {'started_at_unix': 100, 'started_at_clock_gettime_monotonic': 500}
        b = {'finished_at_unix': 140, 'finished_at_clock_gettime_monotonic': 545}
        result = interval(a, b, mode='v3')
        self.assertEqual(result['duration_seconds'], 45)
        self.assertEqual(result['selected_minus_unix_seconds'], 5)

    def test_conflicting_aliases_refused(self):
        a, b = helper()
        a['started_at_clock_gettime_monotonic'] = 100
        b['finished_at_clock_gettime_monotonic'] = 161
        self.assertEqual(interval(a, b, mode='helper')['status'], 'invalid')

    def test_negative_kernel_not_unix_fallback(self):
        a, b = helper(20, 10)
        self.assertEqual(interval(a, b, mode='helper')['status'], 'invalid')

    def test_wrong_shared_basis_refused(self):
        a, b = helper()
        b['shared_clock_basis'] = 'time.monotonic'
        self.assertEqual(interval(a, b, mode='helper')['status'], 'invalid')

    def test_bracket_contains_endpoint_and_bounds_interval(self):
        a, b = helper()
        a['started_shared_clock_bounds'] = [99, 100]
        b['finished_shared_clock_bounds'] = [159, 160]
        self.assertEqual(interval(a, b, mode='helper')['kernel_bounds_seconds'], [59, 61])

    def test_endpoint_outside_bracket_refused(self):
        a, b = helper()
        a['started_shared_clock_bounds'] = [100, 101]
        b['finished_shared_clock_bounds'] = [150, 159]
        self.assertEqual(interval(a, b, mode='helper')['status'], 'invalid')

    def test_same_parent_process_difference_valid(self):
        a = {'started_at_unix': 1000, 'started_at_monotonic': 20}
        b = {'finished_at_unix': 1040, 'finished_at_monotonic': 65, 'wall_seconds': 45.00001}
        result = interval(a, b, mode='same-parent')
        self.assertEqual(result['duration_seconds'], 45)
        self.assertAlmostEqual(result['reported_minus_selected_seconds'], .00001)

    def test_public_preappend_report_and_event_endpoint_both_retained(self):
        a, b = helper(100, 160.003)
        b['wall_seconds'] = 60
        result = interval(a, b, mode='helper')
        self.assertAlmostEqual(result['duration_seconds'], 60.003)
        self.assertEqual(result['original_reported_wall_seconds'], 60)
        self.assertAlmostEqual(result['reported_minus_selected_seconds'], -.003)

    def test_raw_cross_parent_wait_does_not_replace_unix_gap(self):
        first, following = row('old parent', 100, 160), row('new parent', 500, 600)
        following['raw_inter_episode_wait_seconds'] = -90
        self.assertEqual(gap(first, following)['seconds'], 340)
        self.assertEqual(following['raw_inter_episode_wait_seconds'], -90)

    def test_same_numbers_cross_cli_do_not_prove_duration(self):
        a = {'started_at_unix': 1000, 'started_at_monotonic': 20}
        b = {'finished_at_unix': 1040, 'finished_at_monotonic': 65, 'wall_seconds': 45}
        result = interval(a, b, mode='legacy')
        self.assertEqual(result['duration_seconds'], 40)
        self.assertEqual(result['raw_process_monotonic_delta_seconds'], 45)

    def test_negative_cross_cli_raw_retained_and_not_clamped(self):
        result = interval({'started_at_unix': 1000, 'started_at_monotonic': 20},
                          {'finished_at_unix': 1600, 'finished_at_monotonic': .01, 'wall_seconds': -19.99}, mode='legacy')
        self.assertEqual(result['duration_seconds'], 600)
        self.assertEqual(result['original_reported_wall_seconds'], -19.99)
        self.assertLess(result['raw_process_monotonic_delta_seconds'], 0)

    def test_partial_kernel_uses_explicit_unix_fallback(self):
        a, b = helper()
        del a['started_at_clock_gettime']
        result = interval(a, b, mode='helper')
        self.assertIn('Unix fallback', result['basis'])

    def test_missing_comparable_clocks_unknown_not_zero(self):
        result = interval({'started_at_monotonic': .1}, {'finished_at_monotonic': .2}, mode='legacy')
        self.assertIsNone(result['duration_seconds'])
        self.assertEqual(result['status'], 'unmeasured')

    def test_negative_unix_not_clamped(self):
        result = interval({'started_at_unix': 100}, {'finished_at_unix': 99}, mode='legacy')
        self.assertIsNone(result['duration_seconds'])
        self.assertEqual(result['status'], 'invalid')

    def test_kernel_with_wall_jump_keeps_duration_and_limit(self):
        a, b = helper()
        b['finished_at_unix'] = 900
        result = interval(a, b, mode='helper')
        self.assertEqual(result['duration_seconds'], 60)
        self.assertTrue(result['limitations'])

    def test_boolean_and_nonfinite_not_clock_numbers(self):
        for bad in [True, float('nan'), float('inf'), '1']:
            result = interval({'started_at_unix': bad}, {'finished_at_unix': 100}, mode='legacy')
            self.assertIsNone(result['duration_seconds'])

    def test_overlap_union_counted_once(self):
        result = union([(1, 10), (5, 15), (2, 8)])
        self.assertEqual(result['seconds'], 14)
        self.assertEqual(result['overlap_seconds_not_added'], 11)

    def test_no_sum_for_overlapping_actors(self):
        result = summarize([row('J1', 1, 10), row('J2', 5, 15)])
        self.assertIsNone(result['active_seconds_nonoverlapping'])
        self.assertEqual(result['recorded_unix_coverage']['seconds'], 14)

    def test_pair_wall_once_not_times_two(self):
        pair = row('pair J1 and J2', 1, 10)
        pair['parallel_actor_count'] = 2
        self.assertEqual(summarize([pair])['active_seconds_nonoverlapping'], 9)

    def test_serial_gaps_separate_from_active(self):
        a, b = row('original', 10, 20), row('supplement', 30, 45)
        self.assertEqual(summarize([a, b])['active_seconds_nonoverlapping'], 25)
        self.assertEqual(gap(a, b)['seconds'], 10)

    def test_failed_segment_not_dropped(self):
        failed = row('failed v2', 100, 386.37)
        failed['status'] = 'failed'
        passed = row('v3', 500, 600)
        self.assertAlmostEqual(summarize([failed, passed])['active_seconds_nonoverlapping'], 386.37)

    def test_future_pending_not_measured_zero(self):
        for result in future_cost().values():
            self.assertIsNone(result['seconds'])
            self.assertIn('pending', result['status'])

    def test_duplicate_and_nonfinite_json_refused(self):
        for bad in [b'{"clock":1,"clock":2}', b'{"clock":NaN}']:
            with self.assertRaises(ValueError):
                parse(bad)

    def test_reader_exact_pin_and_missing_original_key(self):
        r = Memory()
        ref = r.put('/old/START.json', {'started_at_unix': 1})
        self.assertEqual(pinned(r, ref)['started_at_unix'], 1)
        bad = dict(ref, sha256='0'*64)
        with self.assertRaises(ValueError):
            pinned(r, bad)
        with self.assertRaises(ValueError):
            pinned(r, {'path': '/old/missing.json', 'sha256': '0'*64})

    def test_snapshot_changed_copy_and_no_original_fallback(self):
        # Owned temp root, two tiny files; no read of an original absolute key.
        own = Path(__file__).resolve().parent/'HOST'
        own.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='generic-reader-', dir=own) as name:
            root = Path(name)
            (root/'old.json').write_bytes(b'{}')
            reader = SnapshotReader(root, {'/original.json': {'copy': 'old.json', 'sha256': digest(b'{}')}})
            self.assertEqual(reader.read_bytes('/original.json'), b'{}')
            (root/'old.json').write_bytes(b'{ }')
            with self.assertRaises(ValueError):
                reader.read_bytes('/original.json')
            with self.assertRaises(ValueError):
                reader.read_bytes(str(root/'old.json'))

    def test_split_correction_retains_original_negative_numbers(self):
        r = Memory()
        a = r.put('/cause/START.json', {'started_at_unix': 100})
        b = r.put('/cause/ORIGINAL-END.json', {'finished_at_unix': 160, 'wall_seconds': -1})
        c = r.put('/supplement/START.json', {'started_at_unix': 200})
        d = r.put('/supplement/END.json', {'finished_at_unix': 280, 'wall_seconds': -2, 'start': c})
        aggregate = r.put('/cause/END.json', {'original_episode': b, 'complete_input_supplement_episode': d,
                                             'active_episode_wall_seconds': -3, 'inter_episode_research_wait_seconds': .5})
        correction = {'kind': 'original-split-cause-append-only-clock-correction',
                      'original_aggregate': aggregate, 'original_first_start': a, 'original_first_end': b,
                      'original_second_start': c, 'original_second_end': d, 'component_intervals': [{'wall_seconds': 60}, {'wall_seconds': 80}],
                      'active_episode_wall_seconds': 140, 'inter_episode_research_wait_seconds': 40, 'complete_span_seconds': 180,
                      'original_reported_active_seconds': -3, 'original_reported_wait_seconds': .5}
        ref = r.put('/cause/CLOCK-CORRECTION.json', correction)
        checked = check_correction(r, ref)
        self.assertEqual(checked['verified_seconds'], 140)
        self.assertEqual(checked['original_reported_active_seconds'], -3)
        correction['active_episode_wall_seconds'] = 0
        ref = r.put('/bad-correction.json', correction)
        with self.assertRaises(ValueError):
            check_correction(r, ref)

    def test_correction_changed_original_pin_refused(self):
        r = Memory()
        a = r.put('/START', {'started_at_unix': 1})
        b = r.put('/END', {'finished_at_unix': 3, 'wall_seconds': -1})
        c = r.put('/CORRECTION', {'kind': 'original-episode-append-only-clock-correction', 'original_start': a,
                                  'original_end': b, 'corrected_interval': {'wall_seconds': 2}})
        r.values['/END'] = b'{"finished_at_unix":4}'
        with self.assertRaises(ValueError):
            check_correction(r, c)


def original_helper_observations():
    """Retained v1 behavior on generic inputs, original file never edited."""
    base = Path(__file__).resolve().parent/'HOST/recorded-metadata/raw/business-quality-tools/quality_clock.py'
    need_sha = '8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c'
    if digest(base.read_bytes()) != need_sha:
        raise ValueError('Frozen original clock helper byte pin differs')
    spec = importlib.util.spec_from_file_location('original_quality_clock_synthetic_only', base)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    observations = []
    for name, a, b, mode in [
        ('v3 alias is not recognized by original helper', {'started_at_unix': 100, 'started_at_clock_gettime_monotonic': 500}, {'finished_at_unix': 140, 'finished_at_clock_gettime_monotonic': 545}, 'v3'),
        ('original helper has no same-parent qualification', {'started_at_unix': 100, 'started_at_monotonic': 1}, {'finished_at_unix': 140, 'finished_at_monotonic': 46}, 'same-parent'),
        ('cross CLI negatives preserved with Unix correction', {'started_at_unix': 100, 'started_at_monotonic': 20}, {'finished_at_unix': 140, 'finished_at_monotonic': .1, 'wall_seconds': -19.9}, 'legacy'),
    ]:
        observations.append({'name': name, 'start': a, 'end': b, 'original_helper': old.interval(a, b), 'independent_interpretation': interval(a, b, mode=mode)})
    return {'kind': 'retained-original-helper-generic-scope-observations', 'source_sha256': need_sha, 'observations': observations,
            'limitation': 'Scope differences, not edits or replacements of the original helper. Both helper alias limitation and valid same-parent source qualification remain explicit.'}


if __name__ == '__main__':
    unittest.main(verbosity=2)
