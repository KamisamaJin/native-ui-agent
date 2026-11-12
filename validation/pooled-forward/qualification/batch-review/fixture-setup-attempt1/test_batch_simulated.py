#!/usr/bin/env python3
"""Six strict non-forwarding HOST/SIM cases; no real child/process/SDK operation."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import types

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
TARGET = OUT / 'pinned-run_benchmark.py'
PY = sys.executable
ORDER = [['block-1', 'A'], ['block-1', 'B'], ['block-2', 'B'], ['block-2', 'A']]
REAL_OPERATIONS = []


def veto(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.kill', 'os.killpg'}:
        REAL_OPERATIONS.append(event)
        raise RuntimeError('Non-forwarding simulation forbids all real child/SDK/process actions')
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in str(args[1] or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not path.is_relative_to(OUT): raise RuntimeError('Simulation writes only batch-review')


sys.addaudithook(veto)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


class Clock:
    CLOCK_MONOTONIC = 6
    def __init__(self): self.now = 1000.0
    def clock_gettime(self, basis):
        assert basis == self.CLOCK_MONOTONIC
        return self.now
    def time(self): return 2000000000 + self.now
    def advance(self, seconds): self.now += seconds


class Signals:
    SIGALRM, ITIMER_REAL, SIGTERM, SIGKILL = 14, 0, 15, 9
    def __init__(self): self.handler = 'SIMULATED-prior-handler'; self.calls = []
    def signal(self, number, handler):
        assert number == self.SIGALRM
        previous = self.handler; self.handler = handler
        self.calls.append({'operation': 'signal-handler', 'signal': number, 'handler': 'expired' if callable(handler) else handler})
        return previous
    def setitimer(self, kind, duration):
        assert kind == self.ITIMER_REAL and duration in [0, 7200]
        self.calls.append({'operation': 'setitimer', 'duration': duration})
    def expire(self):
        assert callable(self.handler)
        self.handler(self.SIGALRM, None)


class Process:
    def __init__(self, owner, command, number):
        self.owner, self.command, self.pid = owner, command, 710000 + number
        self.exited = False; self.returncode = None
        self.waits = []
        self.block, self.arm = command[command.index('--block') + 1], command[command.index('--arm') + 1]
        self.root = owner.root / 'cache/benchmark' / self.block / self.arm
        self.root.mkdir(parents=True)
        for case in ['ios-cold', 'ios-warm', 'android']:
            save(self.root / 'profiles' / (case + '.json'), {'SIMULATED': True, 'case': case})
        save(self.root / 'profiles/ADMISSION.json', {'SIMULATED': True, 'configs': {case + '.json': 'SIMULATED' for case in ['ios-cold', 'ios-warm', 'android']}})
    def wait(self, timeout=None):
        self.waits.append(timeout); self.owner.calls.append({'operation': 'wait', 'pid': self.pid, 'timeout': timeout})
        scenario = self.owner.scenario
        if timeout is None:
            if scenario.startswith('timeout'):
                self.owner.clock.advance(7200)
                if scenario == 'timeout-already-exited': self.exited, self.returncode = True, 0
                self.owner.signals.expire()
                raise AssertionError('Expired handler failed to raise')
            self.owner.clock.advance(7)
            self.exited = True
            self.returncode = 1 if scenario == 'episode-failed-cleanup-timeout' else 0
            save(self.root / 'result.json', {'SIMULATED': True, 'failed': 'SIMULATED episode failure' if self.returncode else None, 'collection_wall_seconds': 7.0})
            return self.returncode
        if timeout == 180:
            if scenario in ['timeout-escalate', 'timeout-kill-wait-fails']:
                self.owner.clock.advance(180)
                raise subprocess.TimeoutExpired(self.command, timeout)
            self.owner.clock.advance(4); self.exited, self.returncode = True, -15
            return self.returncode
        if timeout == 10:
            if scenario == 'timeout-kill-wait-fails':
                self.owner.clock.advance(10)
                raise subprocess.TimeoutExpired(self.command, timeout)
            self.owner.clock.advance(1); self.exited, self.returncode = True, -9
            return self.returncode
        raise AssertionError('Unexpected wait request')
    def poll(self):
        value = self.returncode if self.exited else None
        self.owner.calls.append({'operation': 'poll', 'pid': self.pid, 'returncode': value})
        return value


class StrictSubprocess:
    STDOUT = 'SIMULATED-STDOUT'
    TimeoutExpired = subprocess.TimeoutExpired
    def __init__(self, root, scenario, clock, signals, admission):
        self.root, self.scenario, self.clock, self.signals, self.admission = root, scenario, clock, signals, admission
        self.calls, self.processes, self.signals_sent = [], [], []
        self.cleanup_count, self.gate_count = 0, 0
    def expected_episode(self, block, arm):
        return [PY, '-B', str(self.root / 'neutral_episode.py'), '--block', block, '--arm', arm,
                '--candidate', self.admission['arms']['B']['skill'], '--freeze', self.admission['arms']['B']['freeze'],
                '--baseline', self.admission['arms']['A']['skill'], '--baseline-freeze', self.admission['arms']['A']['freeze']]
    def Popen(self, command, **kwargs):
        index = len(self.processes)
        assert index < 4, 'Retry/extra episode forbidden'
        assert command == self.expected_episode(*ORDER[index]), 'Episode argv/order differs'
        assert kwargs['start_new_session'] is True and kwargs['stderr'] == self.STDOUT
        assert set(kwargs) == {'stdout', 'stderr', 'start_new_session'}
        self.calls.append({'operation': 'Popen', 'argv': command, 'start_new_session': True, 'SIMULATED': True})
        process = Process(self, command, index); self.processes.append(process)
        return process
    def run(self, command, **kwargs):
        if command[:4] == [PY, '-B', str(self.root / 'verify_benchmark.py'), 'gate']:
            expected = [PY, '-B', str(self.root / 'verify_benchmark.py'), 'gate', '--admission', str((self.root / 'batch-admission.json').resolve()), '--output', str(self.root / 'qualification/benchmark-gate')]
            assert command == expected and self.scenario == 'success'
            assert len(self.processes) == 4 and not self.gate_count
            assert set(kwargs) == {'stdout', 'stderr'} and kwargs['stderr'] == self.STDOUT
            self.gate_count += 1; self.clock.advance(5)
            self.calls.append({'operation': 'gate', 'argv': command, 'SIMULATED': True})
            return types.SimpleNamespace(returncode=0)
        assert len(self.processes) == 1 and self.scenario != 'success'
        case = ['ios-warm', 'android'][self.cleanup_count]
        arm = ORDER[0][1]
        expected = [PY, '-B', str(self.root / self.admission['arms'][arm]['skill'] / 'scripts/ui_loop.py'), 'cleanup-native-resources', '--config', str(self.root / 'cache/benchmark/block-1/A/profiles' / (case + '.json')), '--output', str(self.root / 'operators/benchmark-run' / ('failure-cleanup-block-1-A-' + case))]
        assert command == expected, 'Cleanup attempted foreign/unconfigured path'
        assert set(kwargs) == {'stdout', 'stderr', 'timeout'} and kwargs['timeout'] == 180 and kwargs['stderr'] == self.STDOUT
        self.cleanup_count += 1
        self.calls.append({'operation': 'cleanup', 'argv': command, 'timeout': 180, 'SIMULATED': True})
        if self.scenario == 'episode-failed-cleanup-timeout' and self.cleanup_count == 1:
            self.clock.advance(180); raise self.TimeoutExpired(command, 180)
        self.clock.advance(3)
        return types.SimpleNamespace(returncode=0)
    def killpg(self, pid, signum):
        matches = [p for p in self.processes if p.pid == pid]
        assert len(matches) == 1 and not matches[0].exited, 'Stale/foreign PID group was signaled'
        assert signum in [Signals.SIGTERM, Signals.SIGKILL]
        self.signals_sent.append({'pid': pid, 'signal': signum, 'SIMULATED': True})
        self.calls.append({'operation': 'killpg', 'pid': pid, 'signal': signum, 'SIMULATED': True})


results = []
for scenario in ['success', 'episode-failed-cleanup-timeout', 'timeout-graceful', 'timeout-escalate', 'timeout-already-exited', 'timeout-kill-wait-fails']:
    case = OUT / 'cases' / scenario; root = case / 'root'; root.mkdir(parents=True, exist_ok=False)
    for name in ['neutral_episode.py', 'verify_benchmark.py', 'native_envelope.py', 'prepare_neutral.py']:
        (root / name).write_bytes((OUT / ('pinned-' + name)).read_bytes())
    save(root / 'qualification/prerequisite.json', {'SIMULATED': True})
    admission = {'SIMULATED': True, 'batch_sha256': sha(TARGET), 'order': ORDER, 'threshold': .20, 'required_native_atoms': 104, 'max_machine_seconds': 7200,
        'driver_sha256': sha(root / 'neutral_episode.py'), 'verifier_sha256': sha(root / 'verify_benchmark.py'), 'envelope_sha256': sha(root / 'native_envelope.py'), 'prepare_neutral_sha256': sha(root / 'prepare_neutral.py'),
        'prerequisite_files': {'qualification/prerequisite.json': sha(root / 'qualification/prerequisite.json')},
        'python_executable': PY, 'arms': {'A': {'skill': 'baseline-v12.6', 'freeze': 'BASELINE-FREEZE.json'}, 'B': {'skill': 'candidate-v13.9', 'freeze': 'CANDIDATE-FREEZE-10.json'}}}
    save(root / 'batch-admission.json', admission)
    clock, signals = Clock(), Signals()
    fake = StrictSubprocess(root, scenario, clock, signals, admission)
    spec = importlib.util.spec_from_file_location('batch_under_test_' + scenario.replace('-', '_'), TARGET)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.R, module.time, module.signal, module.subprocess = root, clock, signals, fake
    module.os = types.SimpleNamespace(killpg=fake.killpg)
    module.sys = types.SimpleNamespace(executable=PY)
    output = io.StringIO(); raised = None; code = None; old_argv = sys.argv
    sys.argv = [str(TARGET), '--admission', str(root / 'batch-admission.json')]
    try:
        with contextlib.redirect_stdout(output): code = module.main()
    except BaseException as error:
        raised = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
    finally: sys.argv = old_argv
    result_path = root / 'operators/benchmark-run/RESULT.json'
    value = json.loads(result_path.read_text()) if result_path.is_file() else None
    failure_path = root / 'operators/benchmark-run/FAILURE.json'
    failure = json.loads(failure_path.read_text()) if failure_path.is_file() else None
    checks = []
    def check(name, good): checks.append({'id': name, 'status': 'P' if good else 'F'})
    check('alarm-armed-once-and-restored', [call.get('duration') for call in signals.calls if call['operation'] == 'setitimer'] == [7200, 0] and signals.handler == 'SIMULATED-prior-handler')
    check('no-stale-or-foreign-group-selected', all(row['pid'] in [p.pid for p in fake.processes] for row in fake.signals_sent))
    if scenario == 'success':
        check('exact-four-ABBA-episodes-and-one-gate', code == 0 and raised is None and len(fake.processes) == 4 and fake.gate_count == 1)
        check('no-success-cleanup-or-signals', fake.cleanup_count == 0 and not fake.signals_sent)
        check('all-four-simulated-rows-retained', value is not None and value['failed'] is None and len(value['episodes']) == 4 and value['enclosing_wall_seconds'] == 28)
    else:
        check('failure-stops-order-and-blocks-gate', len(fake.processes) == 1 and fake.gate_count == 0)
        check('final-failure-result-retained', code == 1 and raised is None and value is not None and value['failed'] is not None)
        check('known-configured-cleanup-attempted', fake.cleanup_count == 2)
        check('cleanup-and-failure-wall-retained', value is not None and value['enclosing_wall_seconds'] == clock.now - 1000 and value['enclosing_wall_seconds'] >= (7200 if scenario.startswith('timeout') else 7))
        if scenario == 'timeout-already-exited': check('exited-child-never-signaled', fake.signals_sent == [])
        if scenario == 'timeout-graceful': check('only-own-TERM-and-grace-wait', fake.signals_sent == [{'pid': 710000, 'signal': Signals.SIGTERM, 'SIMULATED': True}] and fake.processes[0].waits == [None, 180])
        if scenario in ['timeout-escalate', 'timeout-kill-wait-fails']: check('only-own-TERM-KILL-and-bounded-waits', [row['signal'] for row in fake.signals_sent] == [Signals.SIGTERM, Signals.SIGKILL] and fake.processes[0].waits == [None, 180, 10])
    record = {'scenario': scenario, 'evidence_class': 'HOST/SIM non-forwarding mock', 'all_times_are_simulated': True, 'exit_code': code, 'raised': raised, 'stdout': output.getvalue(), 'fake_calls': fake.calls, 'signal_controls': signals.calls, 'result': value, 'failure': failure, 'checks': checks, 'status': 'P' if all(check['status'] == 'P' for check in checks) else 'F'}
    save(case / 'RAW.json', record)
    results.append({'scenario': scenario, 'status': record['status'], 'failed_checks': [check['id'] for check in checks if check['status'] == 'F'], 'raw': str(case / 'RAW.json')})
save(OUT / 'RESULTS.json', {'cases': results, 'case_counts': {state: sum(row['status'] == state for row in results) for state in ['P', 'F']}, 'real_operation_attempts': REAL_OPERATIONS, 'actual_native_tests': 0, 'actual_performance_samples': 0, 'scope': 'Six strict HOST/SIM cases, no native forwarding or performance credit'})
print(json.dumps({'cases': results, 'real_operation_attempts': REAL_OPERATIONS}, indent=2))
