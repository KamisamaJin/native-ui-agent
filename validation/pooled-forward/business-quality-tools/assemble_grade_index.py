#!/usr/bin/env python3
"""Close explicit role records; never synthesize a cause or alarm judgment."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


ROOT_GROUPS = {'Case0%d-%s' % (i, v) for i in range(1, 6) for v in ['I', 'X', 'Y']}
PINS = {'anonymous_projection.py': '5bc14d37d11bd755dad38cf1f13b5bbc133eccedceb13ebb1e037dbd07361f2b',
        'phase_barriers.py': 'd940081fc9589df43589a1967442da5e78f6b45cb9c15c97ae7f5dca56407d9d'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path): return {'path': str(path), 'sha256': sha(path)}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', required=True, type=Path)
    p.add_argument('--phase', choices=['cause', 'alarm'], required=True)
    p.add_argument('--actors', required=True, type=Path); p.add_argument('--actors-sha256', required=True)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--cause-index', type=Path); p.add_argument('--cause-index-sha256')
    a = p.parse_args(); root = a.root.resolve()
    version = root / 'publication-alarm-review/revision-v2'
    for name, wanted in PINS.items():
        if sha(version / name) != wanted: raise ValueError('Reviewed phase source pin differs')
    # A fresh CLI process has no previously imported presentation modules.
    if any(n[:-3] in sys.modules for n in PINS): raise ValueError('Fresh phase-index process required')
    sys.path.insert(0, str(version)); import phase_barriers as phase
    from anonymous_projection import strict_json, json_text
    resolver_path = root / 'publication-resolver/resolver.py'
    if sha(resolver_path) != '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204':
        raise ValueError('Frozen no-follow reader pin differs')
    spec = importlib.util.spec_from_file_location('grade_index_live_reader', resolver_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    class Reader:
        def read_bytes(self, original): return module.read_regular(original)[0]
        def read_json(self, original): return strict_json(self.read_bytes(original))
        def directory(self, original):
            path = module.absolute(str(original)); fd = module.open_directory(path); os.close(fd); return path
    reader = Reader()
    actors = phase.original(reader, {'path': str(a.actors), 'sha256': a.actors_sha256})
    if actors.get('kind') != 'original-independent-role-context-registry' or set(actors['groups']) != ROOT_GROUPS:
        raise ValueError('All fifteen original role assignments required')
    if a.output.exists(): raise ValueError('Fresh record-barrier output required')
    base = root / 'cache/business/blind-quality/episodes'
    # Check all pair closures before reading any role body through verification.
    if any(not (base / g / a.phase / 'END.json').is_file() for g in ROOT_GROUPS):
        raise ValueError('Every original pair must close before the global barrier')
    rows = []
    order = sorted(ROOT_GROUPS, key=lambda g: (0 if g.endswith('-I') else 1, g))
    for group in order:
        start_path = base / group / 'cause/START.json'
        start = reader.read_json(str(start_path)); end_path = base / group / a.phase / 'END.json'
        end = reader.read_json(str(end_path))
        seals = end.get('grade_seals')
        if seals is None: seals = {j: item['seal'] for j, item in end['outputs'].items()}
        inputs = [start['packet_seal']]
        if start.get('complete_input'): inputs.append(start['complete_input'])
        if a.phase == 'alarm':
            alarm_start = reader.read_json(str(base / group / 'alarm/START.json'))
            inputs.append(alarm_start['packet_seal'])
        rows.append({'group': group, 'actors': actors['groups'][group]['actors'],
                     'fork_turns': 'none', 'model_override': None, 'inputs': inputs,
                     'episode_end': ref(end_path), 'seals': seals})
    predecessor = None
    if a.phase == 'alarm':
        if not a.cause_index or not a.cause_index_sha256: raise ValueError('Original cause predecessor required')
        predecessor = {'path': str(a.cause_index), 'sha256': a.cause_index_sha256}
    value = phase.make_index(reader, rows, a.phase, causal_predecessor=predecessor, timestamp=time.time())
    value['actor_registry'] = {'path': str(a.actors), 'sha256': a.actors_sha256}
    a.output.mkdir(parents=True)
    def save(path, document):
        with path.open('x') as f:
            f.write(json_text(document, sort_keys=True, indent=2) + '\n'); f.flush(); os.fsync(f.fileno())
        path.chmod(0o444)
    index_path = a.output / 'INDEX.json'; save(index_path, value)
    verified = phase.verify_index(reader, ref(index_path), a.phase)
    verified.update(actor_registry=value['actor_registry'], verified_at_unix=time.time(),
                    source_code_sha256={n: sha(version / n) for n in PINS})
    save(a.output / 'VERIFICATION.json', verified)
    print(json.dumps({'phase': a.phase, 'status': verified['status'], 'contexts': verified['distinct_contexts'],
                      'index': ref(index_path), 'verification': ref(a.output / 'VERIFICATION.json')}))


if __name__ == '__main__': main()
