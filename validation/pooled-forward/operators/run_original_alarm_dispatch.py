"""Record the frozen dispatch preparer; actual role dispatch stays explicit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def ref(path): return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
def point(prefix): return {prefix+'_at_unix': time.time(), prefix+'_at_clock_gettime': time.clock_gettime(time.CLOCK_MONOTONIC)}
def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o444)


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--group', required=True); p.add_argument('--previous-end', type=Path); p.add_argument('--previous-end-sha256')
    a = p.parse_args(); root = a.root.resolve(); coord = root/'operators/cohort2/coordination'
    order = ['Case%02d-I' % i for i in range(1, 6)] + ['Case%02d-%s' % (i, v) for i in range(1, 6) for v in ['X', 'Y']]
    if a.group not in order: raise ValueError('Original fixed-order version required')
    dispatcher = root/'publication-batch-v8-review/revision-v8/prepare_alarm_dispatch_v4.py'
    expected = '23f09afcfae61ba8da67ea60aaac57eba69598092578d73c640bfde588018913'
    if ref(dispatcher)['sha256'] != expected: raise ValueError('External reviewed dispatcher source pin differs')
    values = {
        'batch': (root/'publication-batch-v8-review/revision-v8/alarm-material-tools-v8/batch.py', '99f4cd6ebdb2ee637fdc3671afcefda1dd18e7afcdffb55e412ce3c786162d56'),
        'cause-index': (coord/'cause-barrier-v1/INDEX.json', '798c543cb040be1f743413c572be3d3ed9a810659e7bac950f484ccf2ec87680'),
        'packets-index': (coord/'alarm-material-selections/original-v5/ALL-PACKETS-SEAL.json', 'e40d8f863f53c189b0eb30ec39c5ed8de68c61e6989155e514cde3479a64a339'),
        'selection-seal': (coord/'alarm-material-selections/original-v5/ALL-SPECS-SEAL.json', 'da2407a1f101ccee4b21bc9e1207bb0a23d8dd74d3894c0f46d2722ff6972369'),
        'actors': (coord/'ORIGINAL-ROLE-CONTEXT-REGISTRY-v1.json', '61fd5f600cf4d07d791a866d1376f8f3d6cf4ab75af7671c0608c8a9357b6bd1')}
    argv = [sys.executable, '-B', str(dispatcher), '--root', str(root), '--group', a.group]
    for name, (path, digest) in values.items():
        if ref(path)['sha256'] != digest: raise ValueError('External original dispatch input pin differs: '+name)
        argv += ['--'+name, str(path), '--'+name+'-sha256', digest]
    if (a.previous_end is None) != (a.previous_end_sha256 is None): raise ValueError('Both predecessor arguments required')
    if a.previous_end is not None: argv += ['--previous-end', str(a.previous_end), '--previous-end-sha256', a.previous_end_sha256]
    out = coord/'alarm-dispatch-operators-v4'/a.group; out.mkdir(parents=True, exist_ok=False)
    started = point('started')
    save(out/'ENTRY.json', {'version': 1, **started, 'kind': 'frozen-original-alarm-dispatch-preparation-entry',
        'group': a.group, 'argv': argv, 'operator_source': ref(Path(__file__).resolve()),
        'scope': 'Common record/preparation overhead; no agent dispatch, product judgment or assignment access.'})
    with (out/'stdout').open('xb') as stdout, (out/'stderr').open('xb') as stderr:
        child = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    for filename in ['stdout', 'stderr']: (out/filename).chmod(0o444)
    finished = point('finished')
    end = {'version': 1, **finished, 'entry': ref(out/'ENTRY.json'), 'exit_code': child.returncode,
           'wall_seconds': finished['finished_at_clock_gettime'] - started['started_at_clock_gettime'],
           'stdout': ref(out/'stdout'), 'stderr': ref(out/'stderr'), 'actual_role_dispatch_performed': False}
    save(out/'END.json', end)
    result = {'record': ref(out/'END.json'), 'exit_code': child.returncode}
    if child.returncode == 0: result['dispatch'] = json.loads((out/'stdout').read_bytes())
    print(json.dumps(result)); return child.returncode


if __name__ == '__main__': raise SystemExit(main())
