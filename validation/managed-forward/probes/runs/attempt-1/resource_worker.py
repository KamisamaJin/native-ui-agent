#!/usr/bin/env python3
"""Argument-only wrapper around the documented Resources API."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

p = argparse.ArgumentParser()
p.add_argument('--scripts', type=Path, required=True)
p.add_argument('--config', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--fixture', type=Path, required=True)
p.add_argument('--fixture-root', type=Path, required=True)
p.add_argument('--token', required=True)
p.add_argument('--mode', required=True)
p.add_argument('--final', action='store_true')
a = p.parse_args()
sys.path.insert(0, str(a.scripts))
resource_source = a.scripts / 'resource_manager.py'
source_before = resource_source.read_bytes()
a.fixture_root.mkdir(parents=True, exist_ok=True)
(a.fixture_root / 'resource-manager-source-before-import.py').write_bytes(source_before)
(a.fixture_root / 'tool-identity-before-import.json').write_text(json.dumps({'resource_manager.py': hashlib.sha256(source_before).hexdigest()}) + '\n')
from resource_manager import Resources

def write(name, value):
    (a.fixture_root / name).write_text(json.dumps(value, indent=2) + '\n')

a.fixture_root.mkdir(parents=True, exist_ok=True)
try:
    config = json.loads(a.config.read_text())
    with Resources(config, a.output, final=a.final) as manager:
        scratch = manager.directory('scratch')
        (scratch / 'payload.txt').write_text('owned temporary payload\n')
        write('entered.json', {'manager_pid': os.getpid(), 'scratch': str(scratch)})
        if a.mode == 'pause':
            while not (a.fixture_root / 'release').exists():
                time.sleep(.02)
        elif a.mode == 'raise-with-directory':
            raise RuntimeError('probe body exception after real acquisition')
        else:
            mode = 'orphan-error' if a.mode == 'raise-after-run' else a.mode
            argv = [sys.executable, '-B', str(a.fixture), '--root', str(a.fixture_root),
                    '--token', a.token, '--role', 'body', '--mode', mode]
            write('requested-run.json', {'argv': argv})
            with (a.fixture_root / 'managed-child.log').open('wb') as log:
                code = manager.run(argv, env=dict(os.environ), stdout=log)
            write('returned-run.json', {'returncode': code})
            if a.mode == 'raise-after-run':
                raise RuntimeError('probe body exception after native command return')
            if code:
                raise subprocess.CalledProcessError(code, argv)
    write('wrapper-result.json', {'completed_context': True, 'tool_identity_after': hashlib.sha256(resource_source.read_bytes()).hexdigest()})
except BaseException as error:
    write('wrapper-result.json', {'error_type': type(error).__name__, 'error': str(error),
                                 'traceback': traceback.format_exc(), 'tool_identity_after': hashlib.sha256(resource_source.read_bytes()).hexdigest()})
    traceback.print_exc()
    raise SystemExit(1)
