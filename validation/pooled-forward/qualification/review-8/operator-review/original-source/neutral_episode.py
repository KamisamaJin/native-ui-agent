#!/usr/bin/env python3
"""Predeclared same-code C0/R0/W1/F2 episode, identical external requests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from measure import Meter

R = Path(__file__).resolve().parent
PY = sys.executable


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: f.write(json.dumps(value, indent=2) + '\n')


def verify_tree(root, seal):
    entries = seal['files']
    assert {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts} == entries


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--block', choices=['block-1', 'block-2'], required=True)
    p.add_argument('--arm', choices=['A', 'B'], required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--freeze', required=True)
    p.add_argument('--baseline', required=True)
    p.add_argument('--baseline-freeze', required=True)
    a = p.parse_args(); skill = R / (a.baseline if a.arm == 'A' else a.candidate)
    freeze = R / (a.baseline_freeze if a.arm == 'A' else a.freeze)
    # Baseline seal uses the historical inventory schema; never mutate it.
    sealed = load(freeze)
    entries = sealed.get('files', sealed.get('source_files'))
    if isinstance(entries, dict):
        expected = {rel: v if isinstance(v,str) else v['sha256'] for rel,v in entries.items()}
        verify_tree(skill, {'files': expected})
    else: raise ValueError('Unknown frozen-source inventory')
    root = R / 'cache/benchmark' / a.block / a.arm
    if root.exists(): raise ValueError('Episode roots must begin empty')
    root.mkdir(parents=True)
    prep = [PY, '-B', str(R / 'prepare_neutral.py'), '--workspace', str(root / 'workspace'),
            '--resource-root', str(root / 'resources'), '--workflow-root', str(root / 'workflow'),
            '--stores', str(root / 'stores'), '--profiles', str(root / 'profiles')]
    with (root / 'prepare.log').open('x') as stream:
        subprocess.run(prep, stdout=stream, stderr=subprocess.STDOUT, check=True)
    save(root / 'ADMISSION.json', {'at_unix': time.time(), 'arm': a.arm, 'block': a.block,
         'skill_seal_sha256': sha(freeze), 'profile_admission_sha256': sha(root / 'profiles/ADMISSION.json'),
         'driver_sha256': sha(__file__), 'envelope_sha256': sha(R / 'native_envelope.py'),
         'spec_sha256': sha(R / 'qualification/spec/EFFECTIVE-SEAL.json'), 'source_map': load(root / 'profiles/ADMISSION.json')['production_files'],
         'workload': ['C0 android+ios-cold', 'R0 bind independently inspected thin bridge actuals then unchanged default',
                      'W1 ios-warm new deterministic caller fixture, unchanged production', 'F2 ordinary full final ios-warm+android with final retirement'],
         'controls': 'Private episode cache/pool initially empty. Shared SDK/Gradle caches are measured as common warm infrastructure, never purged. No source or oracle edits.'})
    meter_spec = {'groups': {'episode': {'paths': [str(root)], 'resource_journals': [str(root / 'resources/ios/journal.json')]}},
                  'sample_seconds': 2, 'max_total_allocated_bytes': 32 * 2**30, 'min_free_bytes': 5 * 2**30, 'filesystem_root': str(root)}
    stages = []; captures = {}; failed = None
    def invoke(case, name, arguments):
        config = root / 'profiles' / (case + '.json')
        record = root / 'commands' / (a.block + '-' + a.arm + '-' + name)
        command = [PY, '-B', str(R / 'native_envelope.py'), '--config', str(config), '--skill', str(skill),
                   '--record', str(record), '--timeout', '1200', '--', PY, '-B', str(skill / 'scripts/ui_loop.py')] + arguments
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        save(root / 'commands' / (name + '.driver.json'), {'argv': command, 'exit_code': result.returncode, 'stdout': result.stdout})
        if result.returncode: raise RuntimeError('Episode command failed: ' + name)
        return load(record / 'result.json')
    def native(case, name, final=False, previous=None):
        output = root / 'evidence' / name
        arguments = ['native', '--config', str(root / 'profiles' / (case + '.json')), '--output', str(output)]
        if final: arguments.append('--final')
        if previous is not None and a.arm == 'A':
            arguments += ['--previous', str(previous), '--previous-sha256', sha(previous)]
        invoke(case, name, arguments)
        cycle = load(output / 'cycle.json')
        if cycle.get('capture_result'): captures[case] = Path(cycle['capture_result'])
        return cycle
    def source_bind(case, name):
        pl = 'android' if case == 'android' else 'ios'
        original = load(R / 'qualification/admission-review' / ('source-submission-' + pl + '.json'))
        current = load(root / 'profiles' / (case + '.json'))
        # Reuse a human source observation only for byte-identical inspected
        # bridge content; its current actual citations are re-bound by the tool.
        bridge = Path(current['bridge'])
        fixed = R / 'qualification/spec/modular-fixture' / ('ios/bridge/ObserverBridge.swift' if pl == 'ios' else 'android/bridge/ObserverBridge.kt')
        assert sha(bridge) == sha(fixed)
        for row in original['observations']:
            for cite in row['citations']: cite['path'] = str(bridge)
        path = root / 'reviews' / (name + '.json'); save(path, original)
        invoke(case, name, ['bind-source-review', '--config', str(root / 'profiles' / (case + '.json')),
                            '--submission', str(path), '--output', str(root / 'reviews' / (name + '-bound.json'))])
    def stage(name, body):
        at = time.time(); start = time.perf_counter(); before = len(list((root / 'commands').glob('*.driver.json')))
        try: return body()
        finally:
            stages.append({'stage': name, 'started_at_unix': at, 'finished_at_unix': time.time(),
                           'wall_seconds': time.perf_counter() - start,
                           'new_commands': len(list((root / 'commands').glob('*.driver.json'))) - before})
            save(root / ('stage-' + name + '.json'), stages[-1])
    collection_started_at = time.time(); collection_clock = time.perf_counter()
    with Meter(meter_spec, root / 'meter.jsonl'):
        try:
            stage('C0', lambda: [native('android', 'C0-android'), native('ios-cold', 'C0-ios')])
            def r0():
                for case in ['android', 'ios-cold']:
                    source_bind(case, 'R0-source-' + case)
                    native(case, 'R0-' + case, previous=captures[case])
            stage('R0', r0)
            stage('W1', lambda: native('ios-warm', 'W1-ios'))
            def f2():
                for case in ['ios-warm', 'android']:
                    c = native(case, 'F2-' + case, final=True, previous=captures[case])
                    if c['status'] != 'accepted': raise RuntimeError('Final delivery unresolved: ' + case + ': ' + c['status'])
                    resource = load(root / 'evidence' / ('F2-' + case) / 'resources.json')
                    if resource['cleanup_errors'] or resource['remaining_devices'] or resource['remaining_directories']:
                        raise RuntimeError('Final resources not retired')
            stage('F2', f2)
        except BaseException as exc:
            failed = {'type': type(exc).__name__, 'message': str(exc)}
            # One explicit positive-owned recovery; kept and charged. No retry.
            def recover():
                for case in ['ios-warm', 'android']:
                    try: invoke(case, 'failure-cleanup-' + case, ['cleanup-native-resources', '--config', str(root / 'profiles' / (case + '.json')),
                                                                '--output', str(root / 'failure-cleanup' / case)])
                    except BaseException as cleanup: save(root / ('cleanup-error-' + case + '.json'), {'type': type(cleanup).__name__, 'message': str(cleanup)})
            stage('failure-cleanup', recover)
    source_after = {str(i) + '/' + str(p.relative_to(Path(v))): sha(p) for i, v in enumerate(load(root / 'profiles/android.json')['source_roots'])
                    for p in sorted(Path(v).rglob('*')) if p.is_file()}
    collection_wall = time.perf_counter() - collection_clock
    stage_walls = sum(v['wall_seconds'] for v in stages)
    result = {'arm': a.arm, 'block': a.block, 'stages': stages, 'collection_wall_seconds': collection_wall,
              'collection_started_at_unix': collection_started_at,
              'collection_stage_seconds': stage_walls, 'operator_and_meter_seconds': collection_wall-stage_walls,
              'failed': failed, 'source_after': source_after, 'finished_at_unix': time.time(),
              'source_unchanged': source_after == {('0/' + k[len('alerttoast/Sources/'):]) if k.startswith('alerttoast/Sources/') else ('1/' + k[len('reply/Reply/app/src/main/'):]): v for k, v in load(root / 'ADMISSION.json')['source_map'].items()}}
    save(root / 'result.json', result)
    print(json.dumps({k: result[k] for k in ['arm', 'block', 'collection_wall_seconds', 'failed', 'source_unchanged']}))
    return 1 if failed else 0


if __name__ == '__main__': raise SystemExit(main())
