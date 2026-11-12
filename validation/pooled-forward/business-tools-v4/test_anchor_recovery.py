#!/usr/bin/env python3
"""HOST/SIM first-D0 durability cut matrix. NO SDK/native forwarding."""
from contextlib import contextmanager
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_blind_study as base
from test_terminal_d0 import TerminalD0Tests

b, put = base.b, base.put


class AnchorRecoveryTests(unittest.TestCase):
    def setUp(self): base.ControllerTests.setUp(self)
    def tearDown(self): base.ControllerTests.tearDown(self)

    def begin(self):
        f = self.fixture; s = f.init(); s.admit('T1')
        ticket = s.enqueue('T1', 'A', 'diagnostic')
        return f, s, ticket

    def failed(self, *args): return TerminalD0Tests.failure(self, *args)

    @contextmanager
    def at_result(self, result, seconds):
        with patch.object(b.time, 'clock_gettime', return_value=result['finished_at_clock'] + seconds), patch.object(b.time, 'time', return_value=result['finished_at_unix'] + seconds):
            yield

    def cut_append(self, s, kind, after=False):
        original = s.append
        def append(event, **values):
            if event == kind and not after: raise OSError('HOST/SIM cut before ' + kind)
            value = original(event, **values)
            if event == kind and after: raise OSError('HOST/SIM cut after ' + kind)
            return value
        return patch.object(s, 'append', side_effect=append)

    def cut_result(self, after=False, truncated=False):
        original = b.save
        def save(path, value):
            path = Path(path)
            if path.name == 'result.json':
                if truncated:
                    path.write_text('{"HOST_SIM":"truncated')
                elif after:
                    original(path, value)
                raise OSError('HOST/SIM result persistence cut')
            return original(path, value)
        return patch.object(b, 'save', side_effect=save)

    def result(self, s, ticket): return b.load(s.root / 'requests' / ticket['request_id'] / 'result.json')
    def source(self, s): return Path(s.arm('T1', 'A')['source_roots'][0]) / 'Opaque.txt'
    def restart(self, s): return b.Study(str(s.root))

    def assert_original_anchor(self, s, ticket, result):
        anchor = s.one('T1', 'A', 'repair_started')
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor['d0_request_id'], ticket['request_id'])
        self.assertEqual(anchor['deadline_clock'], result['finished_at_clock'] + 1200)
        self.assertEqual(anchor['deadline_at_unix'], result['finished_at_unix'] + 1200)
        self.assertEqual(anchor['d0_result'], {'path': str(s.root / 'requests' / ticket['request_id'] / 'result.json'),
                                               'sha256': b.sha(s.root / 'requests' / ticket['request_id'] / 'result.json')})
        self.assertEqual(len(s.history('T1', 'A', 'repair_started')), 1)
        self.assertIsNone(s.one('T1', 'B', 'repair_started'))
        return anchor

    def test_cut_before_preparation_has_no_authenticated_aggregate(self):
        f, s, ticket = self.begin()
        with self.cut_append(s, 'd0_result_prepared'):
            with self.assertRaises(OSError): s.serve(self.failed)
        fresh = self.restart(s)
        with b.lock(s.root / 'state.lock'): fresh.expire()
        self.assertFalse(fresh.d0_complete('T1', 'A')); self.assertEqual(len(fresh.pending('T1', 'A')), 1)
        self.assertIsNone(fresh.one('T1', 'A', 'repair_started')); self.assertFalse(self.source(fresh).stat().st_mode & 0o222)
        with self.assertRaisesRegex(ValueError, 'in-flight'): fresh.serve(self.failed)

    def test_prepared_but_result_missing_stays_pending_without_overwrite(self):
        f, s, ticket = self.begin()
        with self.cut_result():
            with self.assertRaises(OSError): s.serve(self.failed)
        fresh = self.restart(s)
        with b.lock(s.root / 'state.lock'): fresh.expire()
        self.assertEqual(len(fresh.history(kind='d0_result_prepared')), 1)
        self.assertFalse((s.root / 'requests' / ticket['request_id'] / 'result.json').exists())
        self.assertFalse(fresh.d0_complete('T1', 'A')); self.assertIsNone(fresh.one('T1', 'A', 'repair_started'))
        with self.assertRaisesRegex(ValueError, 'outstanding'): fresh.enqueue('T1', 'A', 'diagnostic')

    def test_cut_after_result_recovers_finish_and_original_remaining_window(self):
        f, s, ticket = self.begin()
        with self.cut_result(after=True):
            with self.assertRaises(OSError): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 100): fresh.feedback_ready('T1', 'A')
        anchor = self.assert_original_anchor(fresh, ticket, result)
        self.assertTrue(fresh.history('T1', 'A', 'request_finished')[0]['recovered_from_prepared_result'])
        self.assertTrue(self.source(fresh).stat().st_mode & 0o200)
        self.assertEqual(fresh.one('T1', 'A', 'repair_unlocked')['deadline_clock'], anchor['deadline_clock'])

    def test_cut_before_finished_recovers_expired_original_before_unlock(self):
        f, s, ticket = self.begin()
        with self.cut_append(s, 'request_finished'):
            with self.assertRaises(OSError): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 1301):
            with self.assertRaisesRegex(ValueError, 'sealed'): fresh.feedback_ready('T1', 'A')
        self.assert_original_anchor(fresh, ticket, result)
        self.assertEqual(fresh.one('T1', 'A', 'source_locked')['reason'], 'repair_deadline')
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_cut_after_finished_blocks_counterexample_d1_extension(self):
        f, s, ticket = self.begin(); initial_sha = b.sha(self.source(s))
        with self.cut_append(s, 'request_finished', after=True):
            with self.assertRaises(OSError): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 1301):
            with self.assertRaisesRegex(ValueError, 'sealed'): fresh.enqueue('T1', 'A', 'diagnostic')
            with self.assertRaisesRegex(ValueError, 'sealed'): fresh.feedback_ready('T1', 'A')
        self.assert_original_anchor(fresh, ticket, result)
        self.assertEqual(len([e for e in fresh.history('T1', 'A', 'request_enqueued') if e['action'] == 'diagnostic']), 1)
        self.assertEqual(b.sha(self.source(fresh)), initial_sha)
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_cut_before_anchor_recovery_uses_first_result_hash_and_time(self):
        f, s, ticket = self.begin()
        with self.cut_append(s, 'repair_started'):
            with self.assertRaisesRegex(ValueError, 'recovery proof'): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 1301): fresh.lock_source('T1', 'A')
        self.assert_original_anchor(fresh, ticket, result)
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_cut_after_anchor_keeps_one_anchor_and_expires_without_guard(self):
        f, s, ticket = self.begin()
        with self.cut_append(s, 'repair_started', after=True):
            with self.assertRaisesRegex(ValueError, 'recovery proof'): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 1301):
            with b.lock(s.root / 'state.lock'): fresh.expire()
        self.assert_original_anchor(fresh, ticket, result)
        self.assertIsNotNone(fresh.one('T1', 'A', 'source_locked'))
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_guard_start_failure_then_late_new_guard_cannot_buy_time(self):
        f, s, ticket = self.begin()
        with patch.object(b, 'start_guard', side_effect=RuntimeError('HOST/SIM guard startup cut')):
            with self.assertRaises(RuntimeError): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 1301):
            with self.assertRaisesRegex(ValueError, 'sealed'): fresh.feedback_ready('T1', 'A')
        self.assert_original_anchor(fresh, ticket, result)
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_truncated_result_is_retained_and_cannot_be_recovered_or_retried(self):
        f, s, ticket = self.begin()
        with self.cut_result(truncated=True):
            with self.assertRaises(OSError): s.serve(self.failed)
        path = s.root / 'requests' / ticket['request_id'] / 'result.json'; before = path.read_bytes(); fresh = self.restart(s)
        with self.assertRaisesRegex(ValueError, 'sealed result hash'): fresh.feedback_ready('T1', 'A')
        self.assertEqual(path.read_bytes(), before); self.assertIsNone(fresh.one('T1', 'A', 'repair_started'))
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_tampered_completed_result_or_outcome_never_creates_clock(self):
        f, s, ticket = self.begin()
        with self.cut_append(s, 'repair_started'):
            with self.assertRaises(ValueError): s.serve(self.failed)
        result_path = s.root / 'requests' / ticket['request_id'] / 'result.json'; original = result_path.read_bytes()
        result_path.chmod(0o644); result = b.load(result_path); result['finished_at_clock'] += 1301; put(result_path, result)
        fresh = self.restart(s)
        with self.assertRaisesRegex(ValueError, 'sealed result hash'): fresh.feedback_ready('T1', 'A')
        result_path.write_bytes(original)
        outcome = result_path.parent / 'ios/outcome.json'; outcome.chmod(0o644); outcome.write_text('{"HOST_SIM":"tampered outcome"}')
        with self.assertRaisesRegex(ValueError, 'outcome file changed'): fresh.enqueue('T1', 'A', 'diagnostic')
        self.assertIsNone(fresh.one('T1', 'A', 'repair_started')); self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_existing_anchor_is_checked_against_first_result(self):
        f, s, ticket = self.begin(); s.serve(self.failed)
        anchor = s.one('T1', 'A', 'repair_started'); path = s.root / 'events' / f"{anchor['sequence']:06d}.json"
        path.chmod(0o644); wrong = b.load(path); wrong['deadline_clock'] += 1301; put(path, wrong)
        fresh = self.restart(s)
        with self.assertRaisesRegex(ValueError, 'immutable FIRST D0'): fresh.feedback_ready('T1', 'A')
        self.assertIsNone(fresh.one('T1', 'A', 'repair_unlocked')); self.assertFalse(self.source(fresh).stat().st_mode & 0o222)

    def test_restarted_watchdog_validates_original_anchor_before_caching(self):
        f, s, ticket = self.begin(); s.serve(self.failed)
        anchor = s.one('T1', 'A', 'repair_started'); path = s.root / 'events' / f"{anchor['sequence']:06d}.json"
        path.chmod(0o644); wrong = b.load(path); wrong['deadline_clock'] += 1301; put(path, wrong)
        with self.assertRaisesRegex(ValueError, 'immutable FIRST D0'): b.watch(str(s.root))
        self.assertFalse(self.source(s).stat().st_mode & 0o222)

    def test_legitimate_queued_d1_after_crash_cannot_reset_expired_window(self):
        f, s, ticket = self.begin()
        with self.cut_append(s, 'repair_started'):
            with self.assertRaises(ValueError): s.serve(self.failed)
        result = self.result(s, ticket); fresh = self.restart(s)
        with self.at_result(result, 100): fresh.enqueue('T1', 'A', 'diagnostic')
        with self.at_result(result, 1301):
            fresh.serve(self.failed)
            with self.assertRaisesRegex(ValueError, 'sealed'): fresh.feedback_ready('T1', 'A')
        self.assert_original_anchor(fresh, ticket, result)
        self.assertEqual(len([e for e in fresh.history('T1', 'A', 'request_enqueued') if e['action'] == 'diagnostic']), 2)
        self.assertFalse(self.source(fresh).stat().st_mode & 0o222)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AnchorRecoveryTests))
    put(base.ARTIFACTS / 'ANCHOR-RECOVERY-RESULT.json', {'kind': 'HOST/SIM', 'native_execution': False, 'sdk_forwarding': False,
        'scope': 'First-D0 write-ahead proof and crash-boundary recovery; synthetic failed collection logs only, no business/native outcomes',
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful()})
    raise SystemExit(0 if result.wasSuccessful() else 1)
