"""Record uniform all15 prepare/build commands without hiding failed attempts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o444)


def point(prefix):
    return {prefix + '_at_unix': time.time(), prefix + '_at_clock_gettime': time.clock_gettime(time.CLOCK_MONOTONIC)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--id', required=True)
    for key in ['batch', 'metadata-authority', 'admission']:
        p.add_argument('--' + key, required=True, type=Path)
        p.add_argument('--' + key + '-sha256', required=True)
    a = p.parse_args(); root = a.root.resolve()
    if not (a.id.isascii() and a.id.replace('-', '').isalnum()): raise ValueError('Fresh finite ID required')
    for key in ['batch', 'metadata_authority', 'admission']:
        if ref(getattr(a, key))['sha256'] != getattr(a, key + '_sha256'): raise ValueError('External operator/code pin differs')
    control = root / 'operators/cohort2/coordination' / ('alarm-actual-' + a.id)
    control.mkdir(parents=True, exist_ok=False)
    started = point('started')
    base = [sys.executable, '-B', str(a.batch)]
    command = base + ['prepare', '--root', str(root), '--id', a.id,
        '--cause-index', str(root/'operators/cohort2/coordination/cause-barrier-v1/INDEX.json'),
        '--cause-index-sha256', '798c543cb040be1f743413c572be3d3ed9a810659e7bac950f484ccf2ec87680',
        '--native-snapshot', str(root/'publication-native-chain/HOST/actual-whole-pre-binding-v1/SNAPSHOT.json'),
        '--native-snapshot-sha256', '9b1ea5e2a26c165483fa0c6c4fdf479b1894a85cbbe0e0519cbcae524257fca5',
        '--native-result', str(root/'publication-native-chain/HOST/actual-whole-pre-binding-v1/RESULT.json'),
        '--native-result-sha256', '636c0658b4a4a471a7ac70f19fd0009580a45dbe71b74dbae1207914b14ad8e5',
        '--metadata-authority', str(a.metadata_authority), '--metadata-authority-sha256', a.metadata_authority_sha256]
    save(control/'ENTRY.json', {'version': 1, 'kind': 'original-alarm-uniform-preparation-entry',
        **started, 'argv': command, 'operator_source': ref(Path(__file__).resolve()), 'admission': ref(a.admission),
        'metadata_authority': ref(a.metadata_authority), 'phase2_dispatched': False,
        'quality_or_assignment_read_by_root': False,
        'scope': 'Common presentation/record infrastructure only; no new native sample, source/oracle change, judgment or treatment credit.'})
    def run(name, argv):
        begin = point('started')
        with (control/(name+'.stdout')).open('xb') as out, (control/(name+'.stderr')).open('xb') as err:
            completed = subprocess.run(argv, stdout=out, stderr=err, check=False)
        end = point('finished')
        for suffix in ['.stdout', '.stderr']: (control/(name+suffix)).chmod(0o444)
        record = {'version': 1, 'argv': argv, **begin, **end, 'exit_code': completed.returncode,
                  'wall_seconds': end['finished_at_clock_gettime'] - begin['started_at_clock_gettime'],
                  'stdout': ref(control/(name+'.stdout')), 'stderr': ref(control/(name+'.stderr'))}
        save(control/(name+'-END.json'), record)
        return completed.returncode
    code = run('PREPARE', command)
    selection = root/'operators/cohort2/coordination/alarm-material-selections'/a.id/'ALL-SPECS-SEAL.json'
    if code == 0:
        command = base + ['build', '--root', str(root), '--id', a.id,
                          '--selection-seal', str(selection), '--selection-seal-sha256', ref(selection)['sha256']]
        code = run('BUILD', command)
    finished = point('finished')
    summary = {'version': 1, 'kind': 'uniform-alarm-material-operation-end', **finished,
               'entry': ref(control/'ENTRY.json'), 'exit_code': code,
               'wall_seconds': finished['finished_at_clock_gettime'] - started['started_at_clock_gettime'],
               'phase2_dispatched': False, 'quality_adjudicated': False, 'mapping_revealed': False}
    if code == 0:
        summary['selection_seal'] = ref(selection)
        summary['packets_index'] = ref(selection.parent/'ALL-PACKETS-SEAL.json')
    save(control/'END.json', summary)
    print(json.dumps({'record': ref(control/'END.json'), 'exit_code': code,
                      'selection_seal': summary.get('selection_seal'), 'packets_index': summary.get('packets_index')}))
    return code


if __name__ == '__main__': raise SystemExit(main())
