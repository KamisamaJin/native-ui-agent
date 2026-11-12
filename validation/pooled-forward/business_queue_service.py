#!/usr/bin/env python3
"""Serve explicit public FIFO tickets; no retries, new requests or source edits.

The frozen controller remains the only executor and supplies all stage barriers,
timers, source/input checks, fixed A/B transport and native supervision. A failed
controller process stops this pump with the original ticket/log retained.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper', required=True, type=Path)
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--logs', required=True, type=Path)
    parser.add_argument('--stop', required=True, type=Path)
    args = parser.parse_args()
    helper = args.helper.resolve()
    if hashlib.sha256(helper.read_bytes()).hexdigest() != args.helper_sha256:
        raise ValueError('Frozen controller differs')
    sys.path.insert(0, str(helper.parent))
    spec = importlib.util.spec_from_file_location('frozen_paired_controller', helper)
    controller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controller)
    args.logs.mkdir(parents=True, exist_ok=False)
    controller.save(args.logs / 'ADMISSION.json', {'at_unix': time.time(),
                    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'helper': str(helper), 'helper_sha256': args.helper_sha256, 'run': str(args.run.resolve()),
                    'scope': 'Identical shared transport only: explicit FIFO tickets, no source/oracle edit, retry, hidden access or treatment credit.'})
    (args.logs / 'ready').write_text(str(time.time()) + '\n')
    while not args.stop.exists():
        study = controller.Study(args.run.resolve())
        with controller.lock(study.root / 'state.lock'):
            pending = study.pending()
        if not pending:
            time.sleep(.5)
            continue
        request = pending[0]
        folder = args.logs / request['request_id']
        folder.mkdir(exist_ok=False)
        command = [sys.executable, '-B', str(helper), 'serve', '--run', str(args.run.resolve())]
        started = time.time()
        with (folder / 'controller.log').open('x') as stream:
            code = subprocess.run(command, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                  stdout=stream, stderr=subprocess.STDOUT).returncode
        controller.save(folder / 'RESULT.json', {'request_id': request['request_id'], 'argv': command,
                        'started_at_unix': started, 'finished_at_unix': time.time(), 'exit_code': code,
                        'scope': 'Controller exit only. Native execution/acceptance and errors remain in original per-profile outcomes.'})
        if code:
            raise RuntimeError('Controller interrupted/rejected; ticket and original log retained, no automatic retry')
    controller.save(args.logs / 'STOPPED.json', {'at_unix': time.time(), 'owner_stop_file': str(args.stop),
                    'scope': 'Stopped between requests only; no native/source/resource cleanup implied.'})


if __name__ == '__main__':
    main()
