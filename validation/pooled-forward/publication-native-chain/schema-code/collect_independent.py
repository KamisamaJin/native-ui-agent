#!/usr/bin/env python3
"""Execute the pinned finite independent-acquisition schedule, without retries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

RUNNER_SHA = '3c305880a818ab87c21c0c1043064b02af5991633efc7d3ab8d31405c4990a5d'
INITIAL_SHA = '178b49172cee5c10f9101650e2adfe1c193b54c0720884fa8e4e587f37a10c79'
ORDER_SHA = 'cbf3a8489dfb46dc9cfc55504b6947ab75cb604311b58266efd17756dacb754f'


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def positive(path):
    if not path.is_file():
        return False
    value = load(path)
    return value.get('final') is True and all(value.get(key) == [] for key in ['cleanup_errors', 'remaining_directories', 'remaining_devices'])


def progress(root, task, arm, profile, stage, complete):
    path = root / 'operators/cohort2/coordination/INDEPENDENT-NATIVE-PROGRESS.json'
    value = {'version': 1, 'kind': 'mutable-independent-native-progress', 'updated_at_unix': time.time(),
             'active': {'task': task, 'arm': arm, 'profile': profile, 'stage': stage},
             'completed_native_episode_count': len(complete), 'completed_native_episodes': complete,
             'scope': 'Derived progress only; originals, failures and independent quality remain separate.'}
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)
    print(json.dumps({'task': task, 'arm': arm, 'profile': profile, 'stage': stage, 'completed_episodes': len(complete)}), flush=True)


def validate_order(order):
    assert len(order) == 15
    scopes = [(item['task'], item['scope']) for item in order]
    assert len(set(scopes)) == 15
    assert set(scopes) == {(f'T{i}', arm) for i in range(1, 6) for arm in ['I', 'A', 'B']}
    assert scopes[:5] == [(f'T{i}', 'I') for i in range(1, 6)]
    assert all(item['profiles'] == ['ios', 'android'] for item in order)


def close_episode(path, start_path, outcomes, closures, *, status, error=None, adoption=None):
    start = load(start_path)
    value = {'version': 1, 'kind': 'independent-native-episode-terminal', 'status': status,
             'task': start['task'], 'arm': start['arm'], 'start': ref(start_path),
             'finished_at_unix': time.time(), 'finished_at_monotonic': time.monotonic(),
             'wall_seconds': time.monotonic() - start['started_at_monotonic'], 'outcomes': outcomes,
             'positive_resource_closure': closures, 'quality_evaluated': False}
    if error is not None:
        value['stop_reason'] = error
    if adoption is not None:
        value['adopted_first_operation'] = adoption
    save(path, value)


def initialize(root, evidence, control, args):
    runner = root / 'operators/cohort2/coordination/independent_native.py'
    order_path = root / 'operators/cohort2/coordination/POST-PUBLIC-ACQUISITION-ORDER.json'
    assert sha(order_path) == ORDER_SHA
    assert args.monitor.resolve() == root / 'cache/business/initial-reference-monitor-actual'
    order = load(order_path)['episodes']
    validate_order(order)
    assert sha(runner) == RUNNER_SHA
    initial_seal = root / 'cache/business/initial-reference/PREPARATION-SEAL.json'
    assert sha(initial_seal) == INITIAL_SHA
    first = evidence / 'T1/I/ios/native/outcome.json'
    assert args.adopt_first_outcome.resolve() == first and sha(first) == args.adopt_first_outcome_sha256
    first_value = load(first)
    assert (first_value['task'], first_value['arm'], first_value['profile'], first_value['action']) == ('T1', 'I', 'ios', 'native')
    first_claim = load(evidence / 'native-claims/T1/I/ios.json')
    assert first_claim['record'] == str(first.parent) and first_value['native_claim'] == ref(evidence / 'native-claims/T1/I/ios.json')
    save(control / 'START.json', {'version': 1, 'kind': 'pinned-independent-native-collection-start', 'at_unix': time.time(),
                                'runner': ref(runner), 'order': ref(order_path), 'initial_seal': ref(initial_seal),
                                'adopted_first_original_operation': ref(first), 'monitor_ready': ref(args.monitor / 'READY.json'),
                                'scope': 'One explicit native attempt per predeclared task/version/platform. Existing first attempt retained, never resampled. Positive cleanup may recover resources, never UI facts.'})
    return runner, order_path, order, initial_seal, first, first_value


def main():
    entry_unix, entry_clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--monitor', type=Path, required=True)
    parser.add_argument('--adopt-first-outcome', type=Path, required=True)
    parser.add_argument('--adopt-first-outcome-sha256', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = root / 'cache/business/independent-evaluation'
    control = evidence / 'collection-operations'
    control.mkdir(parents=True, exist_ok=False)
    save(control / 'ENTRY.json', {'version': 1, 'started_at_unix': entry_unix, 'started_at_monotonic': entry_clock,
                                 'argv': sys.argv, 'scheduler': ref(Path(__file__).resolve())})
    complete = []
    errors = []
    monitor_closed = False
    episode = started = None
    outcomes, closures = {}, {}
    adoption = None
    try:
        runner, order_path, order, initial_seal, first, first_value = initialize(root, evidence, control, args)
        for item in order:
            task, arm = item['task'], item['scope']
            episode = evidence / 'episodes' / task / arm
            started = episode / 'START.json'
            if not started.exists():
                first_scope = (task, arm) == ('T1', 'I')
                save(started, {'version': 1, 'kind': 'independent-native-episode-start', 'task': task, 'arm': arm,
                               'started_at_unix': first_value['started_at_unix'] if first_scope else time.time(),
                               'started_at_monotonic': first_value['started_at_monotonic'] if first_scope else time.monotonic(),
                               'record_created_at_unix': time.time(), 'order': ref(order_path),
                               'scope': 'Common initial-oracle cost' if arm == 'I' else 'Own independent final hidden-native episode; separate from immutable public own delivery wall.'})
            start = load(started)
            adoption = None
            if (task, arm) == ('T1', 'I'):
                assert start['started_at_monotonic'] <= first_value['started_at_monotonic']
                assert start['started_at_unix'] <= first_value['started_at_unix']
                adoption = {**ref(first), 'registered_at_unix': time.time(),
                            'post_first_operation_adoption_gap_seconds': max(0, time.monotonic() - first_value['finished_at_monotonic']),
                            'scope': 'Gap remains inside the original full common I episode; never subtracted.'}
            outcomes, closures = {}, {}
            if arm != 'I':
                assert monitor_closed, 'Initial supplemental device window must close before hidden finals'
            for profile in item['profiles']:
                assert sha(runner) == RUNNER_SHA and sha(initial_seal) == INITIAL_SHA
                config = root / (f'cache/business/initial-reference/{task}/profiles/{profile}.json' if arm == 'I' else f'cache/business/{task}/{arm}/hidden-profiles/{profile}.json')
                folder = evidence / task / arm / profile / 'native'
                outcome_path = folder / 'outcome.json'
                progress(root, task, arm, profile, 'native-operation', complete)
                if outcome_path != first:
                    if (root / 'operators/RESOURCE-HALT.json').exists():
                        raise RuntimeError('Original common study resource halt forbids new acquisitions')
                    assert not folder.exists(), 'No retry/adoption of any later operation is allowed'
                    command = [sys.executable, '-B', str(runner), '--root', str(root), '--task', task, '--arm', arm,
                               '--profile', profile, '--config', str(config), '--record', str(folder), '--action', 'native']
                    if arm == 'I':
                        command += ['--initial-monitor', str(args.monitor), '--initial-seal', str(initial_seal), '--initial-seal-sha256', INITIAL_SHA]
                    save(episode / f'{profile}-invocation.json', {'at_unix': time.time(), 'argv': command})
                    with (episode / f'{profile}-launch.log').open('x') as stream:
                        result = subprocess.run(command, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=stream, stderr=subprocess.STDOUT)
                    save(episode / f'{profile}-process.json', {'at_unix': time.time(), 'returncode': result.returncode})
                outcome = load(outcome_path) if outcome_path.is_file() else {}
                if outcome_path.is_file():
                    outcomes[profile] = ref(outcome_path)
                candidates = [folder / 'service/resources.json', folder / 'envelope/error-recovery/resources.json']
                closure = next((path for path in candidates if positive(path)), None)
                if closure is None:
                    cleanup = evidence / task / arm / profile / 'explicit-cleanup'
                    command = [sys.executable, '-B', str(runner), '--root', str(root), '--task', task, '--arm', arm,
                               '--profile', profile, '--config', str(config), '--record', str(cleanup), '--action', 'cleanup-native-resources']
                    if arm == 'I':
                        command += ['--initial-monitor', str(args.monitor), '--initial-seal', str(initial_seal), '--initial-seal-sha256', INITIAL_SHA]
                    save(episode / f'{profile}-cleanup-invocation.json', {'at_unix': time.time(), 'argv': command,
                         'reason': 'Original native output has no positive final resource receipt; explicit owned recovery only, no UI retry.'})
                    with (episode / f'{profile}-cleanup-launch.log').open('x') as stream:
                        result = subprocess.run(command, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=stream, stderr=subprocess.STDOUT)
                    save(episode / f'{profile}-cleanup-process.json', {'at_unix': time.time(), 'returncode': result.returncode})
                    path = cleanup / 'service/resources.json'
                    if positive(path):
                        closure = path
                assert closure is not None, 'Positive owned resource closure is required before the next profile/task'
                closures[profile] = ref(closure)
                assert outcome_path.is_file(), 'Invocation has no durable terminal outcome; resources recovered, no replacement attempt'
                assert outcome.get('source_unchanged') is True, 'Source drift or failed source preflight prevents further acquisition; resources recovered'
                if (root / 'operators/RESOURCE-HALT.json').exists():
                    raise RuntimeError('Original study halted; existing acquisition resources are positively closed, no next UI')
                if outcome.get('error') or outcome.get('exit_code') != 0:
                    errors.append({'task': task, 'arm': arm, 'profile': profile, 'outcome': ref(outcome_path),
                                   'scope': 'Original failed/incomplete acquisition retained; never resampled or treated as delivery.'})
            end = episode / 'END.json'
            close_episode(end, started, outcomes, closures, status='closed', adoption=adoption)
            complete.append({'task': task, 'arm': arm, 'end': ref(end)})
            progress(root, task, arm, None, 'native-episode-closed-quality-pending', complete)
            if task == 'T5' and arm == 'I':
                preflight = [sys.executable, '-B', str(root / 'initial-reference-monitor/monitor.py'), '--record', str(args.monitor), '--preflight']
                with (control / 'monitor-before-stop-preflight.log').open('x') as stream:
                    check = subprocess.run(preflight, stdout=stream, stderr=subprocess.STDOUT)
                save(control / 'monitor-before-stop-preflight.json', {'argv': preflight, 'returncode': check.returncode})
                assert check.returncode == 0, 'Monitor must show original/new slots zero before STOP'
                save(args.monitor / 'STOP', {'at_unix': time.time(), 'reason': 'All five common initial native episodes positively retired; no more I SDK authorized.'})
                deadline = time.monotonic() + 120
                while not (args.monitor / 'CLOSED.json').exists() and time.monotonic() < deadline:
                    time.sleep(0.25)
                closed = load(args.monitor / 'CLOSED.json')
                assert closed.get('status') == 'closed' and closed.get('positive_idle', {}).get('all_clear') is True
                save(control / 'INITIAL-MONITOR-CLOSURE.json', {'at_unix': time.time(), 'closed': ref(args.monitor / 'CLOSED.json'),
                     'scope': 'Supplemental device coverage positively closed before any final hidden acquisition; original v2 meter continues.'})
                monitor_closed = True
            if arm != 'I':
                assert monitor_closed, 'Initial supplemental device window must close before hidden finals'
        save(control / 'END.json', {'version': 1, 'status': 'closed', 'finished_at_unix': time.time(), 'episodes': complete,
                                   'retained_failed_acquisitions': errors, 'initial_monitor_closed': monitor_closed,
                                   'quality_evaluated': False, 'mapping_revealed': False})
    except BaseException as error:
        detail = {'type': type(error).__name__, 'message': str(error)}
        terminal_error = None
        if episode is not None and started is not None and started.is_file() and not (episode / 'END.json').exists():
            try:
                close_episode(episode / 'END.json', started, outcomes, closures, status='failed', error=detail, adoption=adoption)
            except BaseException as terminal_failure:
                terminal_error = {'type': type(terminal_failure).__name__, 'message': str(terminal_failure)}
        save(control / 'FAILED.json', {'version': 1, 'at_unix': time.time(), 'error': {'type': type(error).__name__, 'message': str(error)},
                                      'traceback': traceback.format_exc(), 'completed_episodes': complete,
                                      'retained_failed_acquisitions': errors, 'initial_monitor_closed': monitor_closed,
                                      'current_episode': str(episode) if episode is not None else None, 'terminal_record_error': terminal_error,
                                      'entry_wall_seconds': time.monotonic() - entry_clock,
                                      'scope': 'No automatic native retry or deletion. Original entry/outcome/claim and partial facts retained.'})
        raise


if __name__ == '__main__':
    main()
