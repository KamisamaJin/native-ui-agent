#!/usr/bin/env python3
"""HOST/SIM v3 terminal-D0 readiness tests. No SDK/native forwarding."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import test_blind_study as base

b, put = base.b, base.put


class TerminalD0Tests(unittest.TestCase):
    def setUp(self): base.ControllerTests.setUp(self)
    def tearDown(self): base.ControllerTests.tearDown(self)

    def begin(self):
        f = self.fixture; s = f.init(); s.admit('T1')
        return f, s

    def failure(self, request, profile, argv, folder):
        self.fixture.calls.append({'arm': request['arm'], 'profile': profile, 'kind': 'HOST/SIM failed collection'})
        put(Path(folder) / 'service/failure.log', 'HOST/SIM initial runtime/collector failure; NO SDK executed\n')
        raise RuntimeError('HOST/SIM initial collection failed; original source intact')

    def test_both_profiles_fail_logs_ready_unlock_patch_then_d1_succeeds(self):
        f, s = self.begin()
        cohort_sha = b.sha(s.root / 'INITIAL-COHORT.json')
        capsule = s.folder('T1', 'A') / 'initial/files/0/Opaque.txt'; capsule_sha = b.sha(capsule)
        for alias in ['A', 'B']:
            initial = b.source(s.arm('T1', alias)['source_roots'])
            ticket = s.enqueue('T1', alias, 'diagnostic'); result = s.serve(self.failure)
            self.assertEqual(len(result['outcomes']), 2)
            self.assertTrue(all(o.get('error') and o['integrity']['passed'] and not o['accepted'] and o['new_ui_acquisition'] is None for o in result['outcomes']))
            for row in result['outcomes']:
                self.assertIn('initial runtime/collector failure', (Path(row['service_output']) / 'failure.log').read_text())
                self.assertFalse((Path(row['service_output']) / 'failure.log').stat().st_mode & 0o222)
            self.assertTrue(s.d0_complete('T1', alias))
            anchor = s.one('T1', alias, 'repair_started')
            self.assertEqual(anchor['d0_request_id'], ticket['request_id'])
            self.assertAlmostEqual(anchor['deadline_clock'] - result['finished_at_clock'], 1200, delta=.001)
            self.assertEqual(b.source(s.arm('T1', alias)['source_roots']), initial)
            source = Path(s.arm('T1', alias)['source_roots'][0]) / 'Opaque.txt'
            self.assertFalse(source.stat().st_mode & 0o222)
            s.feedback_ready('T1', alias); source.write_text('HOST/SIM repair from initial failure logs ' + alias)
            s.enqueue('T1', alias, 'diagnostic'); second = s.serve(f.execute)
            self.assertTrue(all(o.get('native_collection_success') is True and not o.get('error') for o in second['outcomes']))
            self.assertEqual(s.one('T1', alias, 'repair_started'), anchor)
        self.assertEqual(b.sha(capsule), capsule_sha)
        self.assertEqual(b.sha(s.root / 'INITIAL-COHORT.json'), cohort_sha)

    def test_failed_retry_is_d1_and_cannot_extend_first_deadline(self):
        f, s = self.begin(); s.enqueue('T1', 'A', 'diagnostic'); first = s.serve(self.failure)
        anchor = s.one('T1', 'A', 'repair_started'); s.feedback_ready('T1', 'A')
        with patch.object(b.time, 'clock_gettime', return_value=anchor['at_clock'] + 300), patch.object(b.time, 'time', return_value=anchor['at_unix'] + 300):
            s.enqueue('T1', 'A', 'diagnostic'); retry = s.serve(self.failure)
        self.assertEqual(s.one('T1', 'A', 'repair_started'), anchor)
        self.assertEqual(len(s.history('T1', 'A', 'repair_started')), 1)
        self.assertTrue(all(not o['accepted'] for o in first['outcomes'] + retry['outcomes']))
        with self.assertRaisesRegex(ValueError, 'cap'): s.enqueue('T1', 'A', 'diagnostic')
        self.assertIsNone(s.one('T1', 'B', 'repair_started'))
        self.assertIsNone(s.one('T2', 'A', 'repair_started'))

    def test_blocked_source_domain_cycle_is_terminal_without_native_facts(self):
        f, s = self.begin()
        def blocked(request, profile, argv, folder):
            output = Path(argv[argv.index('--output') + 1])
            put(output / 'cycle.json', {'status': 'review_source_domain', 'native_executed': False, 'capture_reused': False,
                                       'scope': 'HOST/SIM blocked closed-domain precondition; no native evidence'})
            put(output / 'coverage-domain-task.json', {'kind': 'review_source_domain', 'status': 'unassessed', 'scope': 'HOST/SIM'})
            return 1
        s.enqueue('T1', 'A', 'diagnostic'); result = s.serve(blocked)
        self.assertTrue(s.d0_complete('T1', 'A'))
        self.assertTrue(all(o['new_ui_acquisition'] is False and not o['accepted'] and o['service_status'] == 'review_source_domain' for o in result['outcomes']))
        s.feedback_ready('T1', 'A')
        self.assertTrue((Path(s.arm('T1', 'A')['source_roots'][0]) / 'Opaque.txt').stat().st_mode & 0o200)

    def test_interrupted_ticket_retains_partial_logs_and_never_unlocks(self):
        f, s = self.begin(); ticket = s.enqueue('T1', 'A', 'diagnostic'); calls = []
        def interrupted(request, profile, argv, folder):
            calls.append(profile); put(Path(folder) / 'service/interrupted.log', 'HOST/SIM interrupted, no complete bundle')
            raise KeyboardInterrupt('HOST/SIM explicit interruption')
        with self.assertRaises(KeyboardInterrupt): s.serve(interrupted)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(s.history(kind='request_interrupted')), 1)
        self.assertFalse((s.root / 'requests' / ticket['request_id'] / 'result.json').exists())
        self.assertFalse(s.d0_complete('T1', 'A'))
        self.assertIsNone(s.one('T1', 'A', 'repair_started'))
        with self.assertRaisesRegex(ValueError, 'in-flight'): s.serve(interrupted)
        with self.assertRaisesRegex(ValueError, 'D0 is pending'): s.feedback_ready('T1', 'A')

    def test_missing_or_empty_profile_result_is_not_ready(self):
        f, s = self.begin(); ticket = s.enqueue('T1', 'A', 'diagnostic')
        incomplete = copy.deepcopy(ticket); incomplete['profiles'] = ['ios']
        with patch.object(s, 'pending', return_value=[incomplete]): result = s.serve(self.failure)
        self.assertEqual(len(result['outcomes']), 1)
        self.assertFalse(s.d0_complete('T1', 'A')); self.assertIsNone(s.one('T1', 'A', 'repair_started'))
        # A different arm's completely empty ticket cannot start either clock.
        empty = copy.deepcopy(s.enqueue('T1', 'B', 'diagnostic')); empty['profiles'] = []
        with patch.object(s, 'pending', return_value=[empty]): result = s.serve(self.failure)
        self.assertEqual(result['outcomes'], [])
        self.assertFalse(s.d0_complete('T1', 'B')); self.assertIsNone(s.one('T1', 'B', 'repair_started'))

    def test_outcomes_must_be_durable_before_anchor(self):
        f, s = self.begin(); s.enqueue('T1', 'A', 'diagnostic'); save = b.save
        def omit_one(path, value):
            p = Path(path)
            if p.name == 'outcome.json' and p.parent.name == 'ios': return
            return save(path, value)
        with patch.object(b, 'save', side_effect=omit_one): result = s.serve(self.failure)
        self.assertEqual(len(result['outcomes']), 2)
        self.assertFalse(s.d0_complete('T1', 'A')); self.assertIsNone(s.one('T1', 'A', 'repair_started'))

    def test_source_config_or_tool_integrity_failure_never_anchors(self):
        f, s = self.begin(); s.enqueue('T1', 'A', 'diagnostic')
        config = Path(s.arm('T1', 'A')['public_configs']['ios'])
        original = config.read_bytes(); config.write_text('{"HOST_SIM":"tampered immutable input"}')
        result = s.serve(self.failure)
        self.assertTrue(all(o['integrity']['passed'] is False for o in result['outcomes']))
        self.assertIsNone(s.one('T1', 'A', 'repair_started')); self.assertEqual(f.calls, [])
        config.write_bytes(original)
        # D1 after restored bytes may run, but cannot replace invalid first D0.
        s.enqueue('T1', 'A', 'diagnostic'); s.serve(f.execute)
        self.assertIsNone(s.one('T1', 'A', 'repair_started'))
        with self.assertRaisesRegex(ValueError, 'D0 is pending'): s.feedback_ready('T1', 'A')

    def test_postfailure_integrity_check_detects_input_drift(self):
        f, s = self.begin(); s.enqueue('T1', 'A', 'diagnostic')
        def drift(request, profile, argv, folder):
            config = Path(s.arm('T1', 'A')['public_configs']['ios'])
            put(Path(folder) / 'service/failure.log', 'HOST/SIM failure plus independent input drift')
            config.write_text('{"HOST_SIM":"drift during failed collection"}')
            raise RuntimeError('HOST/SIM failed while inputs changed')
        result = s.serve(drift)
        self.assertTrue(all(o['integrity']['passed'] is False for o in result['outcomes']))
        self.assertIsNone(s.one('T1', 'A', 'repair_started'))

    def test_source_and_frozen_tool_drift_fail_closed(self):
        f, s = self.begin(); s.enqueue('T1', 'A', 'diagnostic')
        component = Path(s.arm('T1', 'A')['source_roots'][0]) / 'Opaque.txt'
        original = component.read_bytes(); component.chmod(0o644); component.write_text('HOST/SIM unauthorized initial-source drift')
        first = s.serve(self.failure)
        self.assertTrue(all(not o['integrity']['passed'] for o in first['outcomes']))
        component.write_bytes(original); component.chmod(0o444)
        s.enqueue('T1', 'B', 'diagnostic')
        tool = Path(s.manifest['tools'][s.arm('T1', 'B')['tool']]['skill_root']) / 'scripts/ui_loop.py'
        tool.write_text('# HOST/SIM unauthorized frozen-tool drift\n')
        second = s.serve(self.failure)
        self.assertTrue(all(not o['integrity']['passed'] for o in second['outcomes']))
        self.assertEqual(f.calls, [])
        self.assertIsNone(s.one('T1', 'A', 'repair_started')); self.assertIsNone(s.one('T1', 'B', 'repair_started'))

    def test_integrity_must_still_hold_at_unlock(self):
        f, s = self.begin(); s.enqueue('T1', 'A', 'diagnostic'); s.serve(self.failure)
        self.assertIsNotNone(s.one('T1', 'A', 'repair_started'))
        config = Path(s.arm('T1', 'A')['public_configs']['ios']); config.write_text('{"HOST_SIM":"post-D0 config drift"}')
        with self.assertRaisesRegex(ValueError, 'public input'): s.feedback_ready('T1', 'A')
        self.assertIsNone(s.one('T1', 'A', 'repair_unlocked'))
        self.assertFalse((Path(s.arm('T1', 'A')['source_roots'][0]) / 'Opaque.txt').stat().st_mode & 0o222)

    def test_failed_domain_precondition_can_use_unchanged_v2_admission_then_d1(self):
        from test_domain_admission import enable_domain, DomainTests
        f = self.fixture; enable_domain(f)
        # A current initial source may lack an exact approved revision while its
        # closed policy/bridge/config is intact: a source-shape precondition, not
        # an input-integrity violation. All data here is explicitly HOST/SIM.
        for task in f.manifest['tasks']:
            for arm in task['arms'].values():
                path = arm['public_configs']['ios']; config = b.load(path)
                approval_path = config['coverage_domain_ref']['path']; approval = b.load(approval_path)
                for platform in approval['platforms'].values():
                    platform['approved_component_revisions']['initial'] = {'sha256': '0' * 64, 'bytes': 1}
                put(approval_path, approval)
                for profile_path in arm['public_configs'].values():
                    c = b.load(profile_path); c['coverage_domain_ref']['sha256'] = b.digest(approval); put(profile_path, c)
        s = f.init(); s.admit('T1')
        def blocked(request, profile, argv, folder):
            put(Path(folder) / 'service/cycle.json', {'status': 'review_source_domain', 'native_executed': False, 'scope': 'HOST/SIM no native facts'})
            return 1
        s.enqueue('T1', 'A', 'diagnostic'); s.serve(blocked); anchor = s.one('T1', 'A', 'repair_started')
        s.feedback_ready('T1', 'A')
        (Path(s.arm('T1', 'A')['source_roots'][0]) / 'Opaque.txt').write_text('HOST/SIM source repair after blocked D0')
        event = s.request_domain_review('T1', 'A', 'ios')
        admitted = s.admit_domain_review(**DomainTests.review(self, event))
        self.assertEqual(admitted['source_deadline_clock'], anchor['deadline_clock'])
        s.enqueue('T1', 'A', 'diagnostic'); result = s.serve(f.execute)
        self.assertTrue(all(not o.get('error') for o in result['outcomes']))
        self.assertEqual(s.one('T1', 'A', 'repair_started'), anchor)

    def test_guard_startup_failure_cannot_postpone_durable_anchor(self):
        f, s = self.begin(); ticket = s.enqueue('T1', 'A', 'diagnostic')
        with patch.object(b, 'start_guard', side_effect=RuntimeError('HOST/SIM guard startup failed')):
            with self.assertRaisesRegex(RuntimeError, 'guard startup'): s.serve(self.failure)
        self.assertTrue(s.d0_complete('T1', 'A'))
        anchor = s.one('T1', 'A', 'repair_started')
        result = b.load(s.root / 'requests' / ticket['request_id'] / 'result.json')
        self.assertEqual(anchor['deadline_clock'], result['finished_at_clock'] + 1200)
        with patch.object(b, 'guard_live', return_value=False):
            with self.assertRaisesRegex(ValueError, 'live deadline guard'): s.feedback_ready('T1', 'A')
        self.assertFalse((Path(s.arm('T1', 'A')['source_roots'][0]) / 'Opaque.txt').stat().st_mode & 0o222)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TerminalD0Tests))
    put(base.ARTIFACTS / 'TERMINAL-D0-RESULT.json', {'kind': 'HOST/SIM', 'native_execution': False, 'sdk_forwarding': False,
        'scope': 'Terminal failed-D0 repair admission and integrity/interrupt fail-closed tests only; synthetic logs/receipts, no business/native outcomes',
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful()})
    raise SystemExit(0 if result.wasSuccessful() else 1)
