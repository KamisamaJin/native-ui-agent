#!/usr/bin/env python3
"""Additive immutable post-repair/original-unaffected packet replay; no native calls."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
import types

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
R = OUT.parents[1]
SKILL = R / 'candidate-v13.9'
P = R / 'cache/qualification/repair/evidence-candidate-v13.9-scope2'
READS, BLOCKED = set(), []


def veto(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.kill', 'os.killpg'}:
        BLOCKED.append({'event': event})
        raise RuntimeError('Read-only replay forbids process/SDK operations')
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in str(args[1] or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not path.is_relative_to(OUT):
            BLOCKED.append({'event': event, 'path': str(path)})
            raise RuntimeError('Replay writes only the new review directory')
        if not writing and path.is_relative_to(SKILL) and '__pycache__' in path.parts:
            raise FileNotFoundError('Pinned source only')
        if not writing and path.is_relative_to(R) and not path.is_relative_to(OUT):
            READS.add(str(path))
    if event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.unlink'} and args and isinstance(args[0], (str, bytes, os.PathLike)):
        if not Path(os.fsdecode(args[0])).resolve().is_relative_to(OUT): raise RuntimeError('Mutation outside review output')
    if event in {'os.rename', 'os.link', 'os.symlink'}:
        for path in args[:2]:
            if isinstance(path, (str, bytes, os.PathLike)) and not Path(os.fsdecode(path)).resolve().is_relative_to(OUT): raise RuntimeError('Mutation outside review output')


sys.addaudithook(veto)
spec = importlib.util.spec_from_file_location('pinned_post_repair_replayer', OUT / 'pinned-verify_benchmark.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
results = []
for name, stage, profile in [('D1-ios', 'D1-ios-after-measured-patch', 'ios-cold'), ('retained-C0-android', 'C0-android', 'android')]:
    packet = P / stage / 'capture/result.json'
    output = OUT / ('post-repair-replay-' + name + '.json')
    try:
        module.replay(types.SimpleNamespace(skill=str(SKILL), config=str(R / 'cache/qualification/repair/profiles-v3' / (profile + '.json')), packet=str(packet), output=str(output)))
        value = json.loads(output.read_text())
        results.append({'stage': name, 'status': 'P', 'packet_sha256': hashlib.sha256(packet.read_bytes()).hexdigest(), 'counts': value['native_counts'], 'native_tests': value['native_tests'], 'responsibility': [{k: row[k] for k in ['id', 'method', 'status']} for row in value['responsibility']['rows']]})
    except BaseException as exc:
        (OUT / ('post-repair-replay-' + name + '.error.txt')).write_text(traceback.format_exc())
        results.append({'stage': name, 'status': 'U', 'error': {'type': type(exc).__name__, 'message': str(exc)}})
readset = {}
for name in sorted(READS):
    path = Path(name)
    if path.is_file():
        raw = path.read_bytes()
        readset[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
summary = {'results': results, 'blocked_process_or_write_attempts': BLOCKED, 'readset': readset,
           'reviewer_SDK_calls': 0, 'reviewer_native_calls': 0,
           'scope': 'Pure replay of immutable fresh iOS and retained failed Android originals; no SDK, no repair code edits, no natural defect or speed claim'}
(OUT / 'POST-REPAIR-REPLAY-RESULTS.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'readset'}, indent=2))
