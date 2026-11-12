"""Real private files/locks with explicitly simulated native packets/inventories."""
import copy
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import capture_validity as cv
import design_contract as d
import resource_manager as rm
import source_identity as si
import workflow_state as ws


class PlatformValidityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.roots = [self.root / name for name in ['ios', 'android', 'shared']]
        for p in self.roots:
            p.mkdir(); (p / 'same-name.txt').write_text(p.name)
        self.policy = {'scope': 'deterministic_component_fixture', 'max_age_seconds': 60,
                       'reset': 'fresh_native_fixture', 'external_state': 'all_dependencies_pinned'}
        self.lock = {'sources': {'reference': {'document': {'validity': self.policy}}}}
        self.config = {'source_roots': list(map(str, self.roots)),
                       'platform_source_roots': {'ios': [str(self.roots[0])], 'android': [str(self.roots[1])]},
                       'native_options': {}, 'capture_validity_ref': {'source': 'reference', 'pointer': '/validity'},
                       'launch_ref': {'source': 'reference', 'pointer': '/launch'}}
        for key, value in [('plan', {'design_contract': {'platform': 'ios'}}), ('design_lock', self.lock),
                           ('fixtures', {'initial': {}, 'updates': []}), ('routes', {}), ('environment', {})]:
            p = self.root / (key + '.json'); p.write_text(json.dumps(value)); self.config[key] = str(p)
        bridge = self.root / 'bridge.swift'; bridge.write_text('unchanged transport'); self.config['bridge'] = str(bridge)
        self.config.update(design_sha256=d.digest(self.lock), routes_sha256=d.digest({}), environment_sha256=d.digest({}),
                           workflow={'root': str(self.root / 'workflow')})

    def packet(self):
        base = self.root / 'packet'; base.mkdir()
        ctx = cv.context(self.config, 'ios'); model = si.model(self.config, 'ios')
        for name, value in [('source-before.json', si.fingerprint(self.config, 'ios')), ('source-model.json', model), ('capture-context.json', ctx)]:
            (base / name).write_text(json.dumps(value))
        receipt = {'status': 'verified_capture', 'scope': 'full', 'native_exit_code': 0,
                   'finishedAtUnix': time.time(), 'coverage_satisfied': True, 'environment_status': 'P',
                   'finishedLeaseClock': rm.lease_clock(), 'host_boot_id': rm.boot_identity(),
                   'source_model': model, 'source_model_sha256': d.digest(model),
                   'capture_context_sha256': d.digest(ctx), 'reset_contract': 'fresh_native_fixture'}
        import execution_plan
        receipt['packet_files'] = execution_plan.packet_inventory(base)
        p = base / 'result.json'; p.write_text(json.dumps(receipt))
        return p, receipt, ctx

    def test_platform_only_edit_preserves_other_and_shared_edit_invalidates_both(self):
        before = {p: si.fingerprint(self.config, p) for p in ['ios', 'android']}
        (self.roots[0] / 'same-name.txt').write_text('actual iOS-only edit')
        self.assertNotEqual(before['ios'], si.fingerprint(self.config, 'ios'))
        self.assertEqual(before['android'], si.fingerprint(self.config, 'android'))
        (self.roots[2] / 'new.txt').write_text('unclassified shared addition')
        self.assertNotEqual(before['android'], si.fingerprint(self.config, 'android'))
        self.assertIn('2/new.txt', si.fingerprint(self.config, 'ios'))

    def test_deleted_renamed_and_symlink_source_cannot_keep_stale_identity(self):
        before = si.fingerprint(self.config, 'ios')
        p = self.roots[0] / 'same-name.txt'; p.rename(p.with_name('new-name.txt'))
        self.assertNotEqual(before, si.fingerprint(self.config, 'ios'))
        (self.roots[0] / 'alias').symlink_to(self.roots[1] / 'same-name.txt')
        with self.assertRaises(ValueError): si.fingerprint(self.config, 'ios')

    def test_original_packet_preflight_reuse_and_scoped_expiry(self):
        p, receipt, ctx = self.packet()
        def assess(): return cv.assess(self.config, p, cv.sha(p), captured_context=ctx)
        self.assertTrue(assess()['eligible'])
        (self.roots[1] / 'same-name.txt').write_text('other platform changed')
        self.assertTrue(assess()['eligible'])
        (self.roots[0] / 'same-name.txt').write_text('changed native dependency')
        self.assertFalse(assess()['eligible'])
        (self.roots[0] / 'same-name.txt').write_text('ios')
        for timestamp in [receipt['finishedAtUnix'] - 61, time.time() + 100]:
            receipt['finishedAtUnix'] = timestamp; p.write_text(json.dumps(receipt))
            self.assertFalse(assess()['eligible'])

    def test_environment_or_oracle_change_cannot_adopt_previous_conclusions(self):
        p, _, ctx = self.packet()
        Path(self.config['environment']).write_text('{"theme":"different"}')
        self.assertFalse(cv.assess(self.config, p, cv.sha(p), captured_context=ctx)['eligible'])
        self.assertFalse(cv.assess(self.config, p, cv.sha(p), captured_context=None)['eligible'])

    def test_altered_collector_report_is_rejected_even_with_unchanged_outer_receipt(self):
        p, receipt, ctx = self.packet()
        metadata = p.parent / 'native'; metadata.mkdir()
        manifest = metadata / 'manifest.json'; manifest.write_text('{"native_test_count":1}')
        import execution_plan
        receipt['packet_files'] = execution_plan.packet_inventory(p.parent); p.write_text(json.dumps(receipt))
        self.assertTrue(cv.assess(self.config, p, cv.sha(p), captured_context=ctx)['eligible'])
        manifest.write_text('{"native_test_count":0}')
        with self.assertRaisesRegex(ValueError, 'inventory/bytes'):
            cv.assess(self.config, p, cv.sha(p), captured_context=ctx)

    def test_unsupported_unbounded_or_missing_reuse_policy_is_not_passed(self):
        p, _, ctx = self.packet()
        del self.config['capture_validity_ref']
        self.assertFalse(cv.assess(self.config, p, cv.sha(p), captured_context=ctx)['eligible'])
        for value in [0, 3601, True]:
            self.config['capture_validity_ref'] = {'source': 'reference', 'pointer': '/validity'}
            self.lock['sources']['reference']['document']['validity']['max_age_seconds'] = value
            Path(self.config['design_lock']).write_text(json.dumps(self.lock)); self.config['design_sha256'] = d.digest(self.lock)
            with self.assertRaises(ValueError): cv.approved_policy(self.config, self.lock)

    def test_explicit_external_build_dependency_is_pinned_without_a_package(self):
        p = self.root / 'theme-input'; p.write_text('first')
        self.config['dependency_files'] = {'shared': [str(p)]}
        first = cv.context(self.config, 'ios')
        p.write_text('second')
        self.assertNotEqual(first, cv.context(self.config, 'ios'))

    def test_effective_build_environment_is_platform_scoped_and_redacted(self):
        self.config['dependency_environment'] = {'ios': ['PRIVATE_THEME'], 'shared': ['SHARED_FLAG']}
        with patch.dict(os.environ, {'PRIVATE_THEME': 'secret-theme-value', 'SHARED_FLAG': 'a'}, clear=True):
            before = {pl: cv.context(self.config, pl) for pl in ['ios', 'android']}
            self.assertNotIn('secret-theme-value', json.dumps(before))
            os.environ['COMPOSE_SNAPSHOT_ID'] = '123'
            self.assertEqual(before['ios'], cv.context(self.config, 'ios'))
            self.assertNotEqual(before['android'], cv.context(self.config, 'android'))
            os.environ['PRIVATE_THEME'] = 'other'
            self.assertNotEqual(before['ios'], cv.context(self.config, 'ios'))
            before_android = cv.context(self.config, 'android')
            os.environ['SHARED_FLAG'] = 'b'
            self.assertNotEqual(before_android, cv.context(self.config, 'android'))
        with patch.dict(os.environ, {'DEVELOPER_DIR': 'ignored-inherited'}, clear=True):
            self.config['native_options'] = {'developer-dir': '/actual-selected'}
            got = cv.environment_dependencies(self.config, 'ios')
            self.assertEqual(got['DEVELOPER_DIR']['sha256'], __import__('hashlib').sha256(b'/actual-selected').hexdigest())

    def test_build_context_retains_environment_and_build_inputs_but_excludes_fixtures(self):
        first = cv.context(self.config, 'ios')
        Path(self.config['fixtures']).write_text('{"initial":{"new-caller":"data"}}')
        second = cv.context(self.config, 'ios')
        self.assertNotEqual(first, second)
        self.assertEqual(cv.build_context(first), cv.build_context(second))
        self.config['dependency_environment'] = {'ios': ['PRIVATE_THEME']}
        self.assertNotEqual(cv.build_context(first), cv.build_context(cv.context(self.config, 'ios')))

    def test_repair_completion_requires_real_source_diff_and_current_task(self):
        capture = self.root / 'receipt.json'; capture.write_text('{"type":"simulated transport"}')
        with ws.Session(self.config, self.root / 'out') as session:
            task = {'capture': ws.reference(capture), 'source_map': si.fingerprint(self.config, 'ios'), 'context_sha256': session.context_sha}
            task_path = self.root / 'task.json'; ws.save(task_path, task)
            ref = ws.reference(task_path); session.state['task'] = ref; session.checkpoint()
            with self.assertRaisesRegex(ValueError, 'no actual'): session.complete(ref, explicit=True)
            (self.roots[0] / 'same-name.txt').write_text('actual patch')
            result = session.complete(ref, explicit=True)
            self.assertEqual(result['status'], 'patched_needs_native_retest')
            self.assertEqual(result['measured_changed_files'], ['0/same-name.txt'])
            with self.assertRaises(ValueError): session.complete(ref, explicit=True)

    def test_typed_cycle_handoff_retains_original_receipt_and_rejects_tampering(self):
        capture = self.root / 'receipt.json'; capture.write_text(json.dumps({'parent_plan_sha256': 'x', 'source_unchanged': True}))
        cycle = self.root / 'cycle.json'; cycle.write_text(json.dumps({'capture_result': str(capture), 'capture_sha256': cv.sha(capture)}))
        self.assertEqual(ws.capture_handle(cycle, cv.sha(cycle)), ws.reference(capture))
        capture.write_text('{}')
        with self.assertRaises(ValueError): ws.capture_handle(cycle, cv.sha(cycle))

    def test_default_continuation_cannot_hide_open_failure_by_changing_oracle(self):
        capture = self.root / 'receipt.json'; capture.write_text('{}')
        with ws.Session(self.config, self.root / 'out') as session:
            task = {'capture': ws.reference(capture), 'source_map': si.fingerprint(self.config, 'ios'), 'context_sha256': session.context_sha}
            target = self.root / 'open-task.json'; ws.save(target, task)
            session.state['task'] = ws.reference(target); session.checkpoint()
        Path(self.config['plan']).write_text('{"design_contract":{"platform":"ios"},"changed_expected":true}')
        import feedback_loop
        with patch.object(feedback_loop, '_managed_cycle') as native:
            with self.assertRaisesRegex(ValueError, 'new-scope admission'):
                feedback_loop.run_cycle(self.config, self.root / 'next')
            native.assert_not_called()

    def test_pending_failed_retest_still_rejects_new_oracle_without_open_task(self):
        capture = self.root / 'receipt.json'; capture.write_text('{}')
        with ws.Session(self.config, self.root / 'out') as session:
            task = {'capture': ws.reference(capture), 'source_map': si.fingerprint(self.config, 'ios'),
                    'context_sha256': session.context_sha, 'failed_assertions': [{'id': 'after/count', 'status': 'failed'}]}
            target = self.root / 'pending-task.json'; ws.save(target, task)
            session.state['task'] = ws.reference(target); session.checkpoint()
            (self.roots[0] / 'same-name.txt').write_text('still broken patch')
            session.complete(session.state['task'])
            # Exercise recovery from an older or interrupted task transition:
            # pending proof must independently guard its original context.
            session.state['task'] = None; session.checkpoint()
        Path(self.config['plan']).write_text('{"design_contract":{"platform":"ios"},"changed_expected":true}')
        import feedback_loop
        with patch.object(feedback_loop, '_managed_cycle') as native:
            with self.assertRaisesRegex(ValueError, 'Pending native retest'):
                feedback_loop.run_cycle(self.config, self.root / 'next')
            native.assert_not_called()

    def test_revert_is_a_measured_revision_and_older_packet_cannot_close_handoff(self):
        capture = self.root / 'receipt.json'; capture.write_text('{}')
        with ws.Session(self.config, self.root / 'out') as session:
            task = {'capture': ws.reference(capture), 'source_map': si.fingerprint(self.config, 'ios'),
                    'context_sha256': session.context_sha, 'failed_assertions': [{'id': 'after/count', 'status': 'failed'}]}
            target = self.root / 'revert-task.json'; ws.save(target, task)
            ref = ws.reference(target); session.state['task'] = ref; session.checkpoint()
            (self.roots[0] / 'same-name.txt').write_text('first attempted patch')
            session.complete(ref)
            (self.roots[0] / 'same-name.txt').write_text('ios')
            revised = session.complete(ref)
            self.assertTrue(revised['previous_completion'])
            pending = session.state['completion']
            receipt = {'status': 'verified_capture', 'source_unchanged': True,
                       'source_sha256': revised['source_after_sha256'], 'capture_context_sha256': session.context_sha,
                       'host_boot_id': rm.boot_identity(), 'finishedLeaseClock': revised['submittedLeaseClock'] - 1}
            report = {'assertions': [{'id': 'after/count', 'status': 'passed'}]}
            self.assertEqual(ws.retest_gate(pending, receipt, report, {}, revised['source_after_sha256'])['status'], 'unassessed')
            receipt['finishedLeaseClock'] = rm.lease_clock()
            self.assertEqual(ws.retest_gate(pending, receipt, report, {}, revised['source_after_sha256'])['status'], 'passed')

    def test_interrupted_final_publication_recovers_exact_payload_after_checkpoint(self):
        out = self.root / 'evidence'; out.mkdir()
        payload = out / 'cycle-payload.json'; ws.save(payload, {'status': 'feedback_complete', 'scope': 'simulated publication only'})
        metadata = out / 'handoff.json'; ws.save(metadata, {'kind': 'simulated transaction metadata'})
        cycle = out / 'cycle.json'
        with ws.Session(self.config, out) as session:
            session.state['pending_publish'] = {'payload': ws.reference(payload),
                'cycle': {'path': str(cycle), 'sha256': cv.sha(payload)}, 'files': [ws.reference(metadata)], 'capture': None}
            session.checkpoint()
        self.assertFalse(cycle.exists())
        with ws.Session(self.config, self.root / 'reentry') as session:
            self.assertEqual(cycle.read_bytes(), payload.read_bytes())
            self.assertNotIn('pending_publish', session.state)


class PoolProtocolTests(unittest.TestCase):
    def test_persisted_lease_clock_is_shared_between_independent_processes(self):
        started = rm.lease_clock()
        code = 'import sys;sys.path.insert(0,' + repr(str(Path(rm.__file__).parent)) + ');import resource_manager as r;print(r.lease_clock())'
        child = float(subprocess.check_output([sys.executable, '-B', '-c', code], text=True))
        finished = rm.lease_clock()
        self.assertLessEqual(started, child)
        self.assertLessEqual(child, finished)

    def test_actual_guardian_retires_simulated_idle_inventory_without_next_entry(self):
        # Real child/lock/filesystem lifecycle; the SDK inventory is explicitly
        # simulated by a private executable, never a real simulator/device.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); source = root / 'source'; source.write_text('source')
            binary = root / 'bin'; binary.mkdir(); inventory = root / 'simulated.json'; inventory.write_text('{}')
            executable = binary / 'xcrun'
            executable.write_text('#!' + sys.executable + '\n' + '''import json,os,sys,uuid,fcntl
from pathlib import Path
p=Path(os.environ['NATIVE_UI_SIMULATED_INVENTORY'])
with p.with_suffix('.lock').open('a') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX);v=json.loads(p.read_text());a=sys.argv[2:]
 if a[:2]==['list','runtimes']: print(json.dumps({'runtimes':[{'identifier':'simulated-runtime','isAvailable':True,'version':'SIMULATED','buildversion':'SIMULATED'}]}))
 elif a[:2]==['list','devices']: print(json.dumps({'devices':{'simulated-runtime':list(v.values())}}))
 elif a[0]=='create':
  key=str(uuid.uuid4());v[key]={'name':a[1],'udid':key,'state':'Shutdown','isAvailable':True};print(key)
 elif a[0]=='delete': del v[a[1]]
 elif a[0]!='shutdown': raise SystemExit(2)
 p.write_text(json.dumps(v))
''')
            executable.chmod(0o700)
            config = {'source_roots': [str(source)], 'native_options': {'simulator': 'managed'},
                      'resources': {'root': str(root / 'scratch'), 'min_free_bytes': 0,
                                    'pool': {'idle_seconds': 2},
                                    'ios': {'device_type': 'simulated-type', 'runtime': 'simulated-runtime'}}}
            env = {'PATH': str(binary) + os.pathsep + os.environ['PATH'], 'NATIVE_UI_SIMULATED_INVENTORY': str(inventory)}
            with patch.dict(os.environ, env):
                guardian = None
                try:
                    with rm.Resources(config, root / 'capture') as resources:
                        resources.native_options(platform='ios')
                        import pool_watch
                        guardian = pool_watch._CHILDREN[resources.state['pool_watch']['pid']]
                    self.assertTrue(json.loads(inventory.read_text()))
                    self.assertIsNone(guardian.poll())
                    # Native delete completion precedes the durable resource
                    # journal and lock release. Wait for the owned controller,
                    # not merely the first observable disappearance.
                    self.assertEqual(guardian.wait(timeout=10), 0)
                    self.assertFalse(json.loads(inventory.read_text()))
                    journal = json.loads((root / 'scratch/journal.json').read_text())
                    self.assertFalse(journal['devices']); self.assertNotIn('pool_watch', journal)
                    self.assertTrue(list((root / 'capture').glob('pool-retirement-*/resources.json')))
                finally:
                    if guardian is not None and guardian.poll() is None:
                        rm.Resources.stop_group(guardian.pid); guardian.wait(timeout=5)
                    with rm.Resources(config, root / 'cleanup', final=True): pass

    def test_idle_slot_reuse_exclusive_cap_monotonic_expiry_and_final_retirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); source = root / 'source'; source.write_text('source')
            config = {'source_roots': [str(source)], 'native_options': {'simulator': 'managed'},
                      'resources': {'root': str(root / 'scratch'), 'min_free_bytes': 0, 'max_simulators': 1,
                                    'ios': {'device_type': 'simulated-type', 'runtime': 'simulated-runtime'}}}
            inventory = {}; calls = []
            def simulated(manager, *argv):
                calls.append(argv)
                if argv[0] == 'create':
                    udid = str(len(calls)); inventory[udid] = {'name': argv[1], 'udid': udid, 'state': 'Shutdown', 'isAvailable': True}; return udid
                if argv[:2] == ('list', 'devices'): return json.dumps({'devices': {'simulated-runtime': list(inventory.values())}})
                if argv[0] == 'delete': del inventory[argv[1]]
                return ''
            with patch.object(rm.Resources, 'simctl', simulated), patch('capture_validity.host_identity', return_value={'host': 'simulated'}), patch('pool_watch.ensure'), patch('pool_watch.stop'):
                with rm.Resources(config, root / 'first') as r:
                    one = r.native_options(platform='ios')['simulator']
                    self.assertEqual(r.native_options(platform='ios')['simulator'], one)
                    with self.assertRaises(RuntimeError):
                        with rm.Resources(config, root / 'concurrent'): pass
                with rm.Resources(config, root / 'second') as r:
                    self.assertEqual(r.native_options(platform='ios')['simulator'], one)
                    row = r.state['devices'][0]
                    row['last_used_monotonic'] -= 400
                    row['pool_idle'] = True; r.save()
                with rm.Resources(config, root / 'expired') as r:
                    two = r.native_options(platform='ios')['simulator']; self.assertNotEqual(one, two)
                with rm.Resources(config, root / 'final', final=True) as r:
                    self.assertEqual(r.native_options(platform='ios')['simulator'], two)
                self.assertFalse(inventory)
                self.assertEqual(sum(c[0] == 'create' for c in calls), 2)
                self.assertFalse(json.loads((root / 'final/resources.json').read_text())['remaining_devices'])


if __name__ == '__main__': unittest.main()
