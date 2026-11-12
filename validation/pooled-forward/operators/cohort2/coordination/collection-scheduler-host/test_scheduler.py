#!/usr/bin/env python3
"""Synthetic protocol guards only; no actual study inputs or SDK access."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('collection_scheduler_host_subject', HERE.parent / 'collect_independent.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
FIXTURES = HERE / 'HOST' / str(time.time_ns())
FIXTURES.mkdir(parents=True)


def schedule():
    return [{'task': f'T{i}', 'scope': 'I', 'profiles': ['ios', 'android']} for i in range(1, 6)] + [
        {'task': f'T{i}', 'scope': arm, 'profiles': ['ios', 'android']} for i in range(1, 6) for arm in ['A', 'B']]


class Guards(unittest.TestCase):
    def test_complete_unique_order(self):
        m.validate_order(schedule())

    def test_duplicate_or_missing_scope_rejected(self):
        order = schedule()
        order[-1] = order[-2]
        with self.assertRaises(AssertionError):
            m.validate_order(order)

    def test_final_before_initial_rejected(self):
        order = schedule()
        order[0], order[5] = order[5], order[0]
        with self.assertRaises(AssertionError):
            m.validate_order(order)

    def test_missing_platform_rejected(self):
        order = schedule()
        order[3]['profiles'] = ['ios']
        with self.assertRaises(AssertionError):
            m.validate_order(order)

    def test_failed_episode_keeps_original_clock_and_partial_refs(self):
        folder = FIXTURES / 'failed-episode'
        start = folder / 'START.json'
        m.save(start, {'task': 'T1', 'arm': 'I', 'started_at_monotonic': 100.0, 'started_at_unix': 1000.0})
        with patch.object(m.time, 'monotonic', return_value=175.0):
            m.close_episode(folder / 'END.json', start, {'ios': {'path': 'original-outcome', 'sha256': 'not-replaced'}}, {},
                            status='failed', error={'type': 'SyntheticStop', 'message': 'retained'})
        end = m.load(folder / 'END.json')
        self.assertEqual(end['wall_seconds'], 75.0)
        self.assertEqual(end['status'], 'failed')
        self.assertEqual(end['outcomes']['ios']['path'], 'original-outcome')
        self.assertEqual(end['positive_resource_closure'], {})

    def test_precheck_failure_still_has_entry_and_terminal_failure(self):
        root = FIXTURES / 'precheck-failure'
        args = ['test', '--root', str(root), '--monitor', str(root / 'monitor'),
                '--adopt-first-outcome', str(root / 'missing-original'), '--adopt-first-outcome-sha256', 'untrusted']
        with patch.object(sys, 'argv', args), patch.object(m.subprocess, 'run', side_effect=AssertionError('No SDK')), self.assertRaises(FileNotFoundError):
            m.main()
        control = root / 'cache/business/independent-evaluation/collection-operations'
        self.assertTrue((control / 'ENTRY.json').is_file())
        self.assertTrue((control / 'FAILED.json').is_file())

    def test_existing_native_cleanup_runs_before_halt_blocks_next_ui(self):
        root = FIXTURES / 'halt-with-owned-resource'
        evidence = root / 'cache/business/independent-evaluation'
        runner = root / 'operators/cohort2/coordination/independent_native.py'
        runner.parent.mkdir(parents=True)
        runner.write_text('synthetic runner; never executed')
        initial = root / 'cache/business/initial-reference/PREPARATION-SEAL.json'
        m.save(initial, {})
        order_path = root / 'operators/cohort2/coordination/POST-PUBLIC-ACQUISITION-ORDER.json'
        m.save(order_path, {'episodes': schedule()})
        first = evidence / 'T1/I/ios/native/outcome.json'
        original = {'task': 'T1', 'arm': 'I', 'profile': 'ios', 'action': 'native', 'source_unchanged': True,
                    'started_at_monotonic': 100.0, 'started_at_unix': 1000.0, 'finished_at_monotonic': 110.0}
        m.save(first, original)
        m.save(root / 'operators/RESOURCE-HALT.json', {'synthetic': True})
        args = ['test', '--root', str(root), '--monitor', str(root / 'monitor'), '--adopt-first-outcome', str(first),
                '--adopt-first-outcome-sha256', m.sha(first)]
        calls = []
        def cleanup_only(command, **kwargs):
            calls.append(command)
            self.assertEqual(command[command.index('--action') + 1], 'cleanup-native-resources')
            folder = Path(command[command.index('--record') + 1])
            m.save(folder / 'service/resources.json', {'final': True, 'cleanup_errors': [], 'remaining_directories': [], 'remaining_devices': []})
            return subprocess.CompletedProcess(command, 0)
        fake_initialization = (runner, order_path, [{'task': 'T1', 'scope': 'I', 'profiles': ['ios', 'android']}], initial, first, original)
        with patch.object(sys, 'argv', args), patch.object(m, 'initialize', return_value=fake_initialization), \
             patch.object(m, 'RUNNER_SHA', m.sha(runner)), patch.object(m, 'INITIAL_SHA', m.sha(initial)), \
             patch.object(m.subprocess, 'run', side_effect=cleanup_only), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            m.main()
        self.assertEqual(len(calls), 1)
        end = m.load(evidence / 'episodes/T1/I/END.json')
        self.assertEqual(end['status'], 'failed')
        self.assertIn('ios', end['positive_resource_closure'])
        self.assertIn('ios', end['outcomes'])


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards))
    (FIXTURES / 'test.log').write_text(stream.getvalue())
    m.save(FIXTURES / 'RESULT.json', {'version': 1, 'kind': 'author-synthetic-scheduler-host', 'controls': result.testsRun,
                                    'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(),
                                    'actual_study_or_private_read': False, 'sdk_executed': False,
                                    'scheduler_sha256': m.sha(HERE.parent / 'collect_independent.py')})
    print(stream.getvalue(), end='')
    print(json.dumps({'result': str(FIXTURES / 'RESULT.json'), 'passed': result.wasSuccessful()}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
