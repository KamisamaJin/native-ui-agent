#!/usr/bin/env python3
"""Identical study safety envelope; no routing, oracle or optimization decisions.

Both frozen arms run unmodified behind this external supervisor. SDK work,
cleanup on error and all measured allocations remain charged to the episode.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'baseline-v12.6/scripts'))
import resource_manager as rm
import measure


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    with Path(path).open('x') as f: f.write(json.dumps(value, indent=2) + '\n')


def owned_device_paths(spec):
    paths = []; slots = 0
    for group in spec['groups'].values():
        for item in group.get('resource_journals', []):
            p = Path(item)
            if not p.is_file(): continue
            j = json.loads(p.read_text()); marker = json.loads((p.parent / 'owner.json').read_text())
            if j.get('format') != rm.FORMAT or marker.get('format') != rm.FORMAT or j['token'] != marker['token']:
                raise ValueError('Foreign study ownership journal')
            identity = {'device': p.parent.stat().st_dev, 'inode': p.parent.stat().st_ino}
            if j.get('root_identity') != identity: raise ValueError('Replaced study resource root')
            for row in j['devices']:
                if not row['name'].startswith('NativeUI-' + marker['token'][:12] + '-'):
                    raise ValueError('Device lacks positive study create identity')
                slots += 1
                if row.get('udid'): paths.append(Path.home() / 'Library/Developer/CoreSimulator/Devices' / row['udid'])
    if slots > 2: raise RuntimeError('Whole-study owned-device cap exceeded')
    return paths


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--skill', type=Path, required=True)
    p.add_argument('--record', type=Path, required=True)
    p.add_argument('--timeout', type=float, default=1200)
    p.add_argument('argv', nargs=argparse.REMAINDER)
    a = p.parse_args(); argv = a.argv[1:] if a.argv[:1] == ['--'] else a.argv
    if not argv or not 0 < a.timeout <= 7200: raise ValueError('Explicit command and bounded time required')
    a.record = a.record.resolve(); a.record.mkdir(parents=True, exist_ok=False)
    config = json.loads(a.config.read_text()); spec_path = R / 'operators/whole-study-meter-spec-v2.json'
    spec = json.loads(spec_path.read_text())
    protected = [Path(v).resolve() for v in config['source_roots']]
    def source_map():
        return {str(i) + '/' + str(v.relative_to(root)): sha(v) for i, root in enumerate(protected)
                for v in sorted(root.rglob('*')) if v.is_file()}
    started = time.time(); start_clock = time.perf_counter()
    result = {'started_at_unix': started, 'argv': argv, 'config_sha256': sha(a.config),
              'skill': str(a.skill.resolve()), 'source_before': source_map(), 'envelope_sha256': sha(__file__), 'meter_spec_sha256': sha(spec_path),
              'purpose': 'Common external resource safety only. No treatment quality, reuse or repair credit.'}
    save(a.record / 'request.json', result)
    policy = {'source_roots': config['source_roots'], 'native_options': {'build-cache': str(R)},
              'resources': {'root': str(R / 'cache/supervision' / a.record.name),
                            'max_bytes': spec['max_total_allocated_bytes'], 'min_free_bytes': spec['min_free_bytes'],
                            'sample_seconds': spec['sample_seconds'], 'max_simulators': 2,
                            'command_timeout_seconds': a.timeout}}
    class StudyResources(rm.Resources):
        def sample(self):
            self.borrowed_paths = [R] + owned_device_paths(spec)
            return super().sample()
        def check_budget(self):
            if (R / 'operators/RESOURCE-HALT.json').exists(): raise RuntimeError('Whole-study monitor requested resource halt')
            return super().check_budget()
    error = None; code = None
    try:
        with StudyResources(policy, a.record / 'supervision', final=True) as supervisor:
            with (a.record / 'command.log').open('x') as stream:
                code = supervisor.run(argv, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=stream)
    except BaseException as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
        (a.record / 'exception.log').write_text(traceback.format_exc())
    recovery = None
    if error is not None or code != 0:
        # The frozen SUT reconciles its own exact process/device tokens. The
        # external envelope never guesses ownership or deletes user resources.
        import subprocess
        out = a.record / 'error-recovery'
        command = [sys.executable, '-B', str(a.skill / 'scripts/resource_manager.py'), '--config', str(a.config),
                   '--output', str(out), 'cleanup']
        at = time.time()
        try:
            with (a.record / 'recovery.log').open('x') as stream:
                recovered = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
            recovery = {'argv': command, 'exit_code': recovered.returncode, 'started_at_unix': at, 'finished_at_unix': time.time()}
        except BaseException as exc: recovery = {'error': {'type': type(exc).__name__, 'message': str(exc)}}
    result.update(finished_at_unix=time.time(), wall_seconds=time.perf_counter()-start_clock,
                  exit_code=code, error=error, recovery=recovery, source_after=source_map())
    result['source_unchanged'] = result['source_before'] == result['source_after']
    save(a.record / 'result.json', result)
    print(json.dumps({k: result[k] for k in ['exit_code', 'error', 'wall_seconds', 'source_unchanged']}))
    return code if code is not None else 1


if __name__ == '__main__': raise SystemExit(main())
