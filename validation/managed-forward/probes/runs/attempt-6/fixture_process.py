#!/usr/bin/env python3
"""Probe-owned real process fixture, with no resource-manager implementation."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--token', required=True)
p.add_argument('--role', required=True)
p.add_argument('--mode', default='hang')
a = p.parse_args()
a.root.mkdir(parents=True, exist_ok=True)
if a.mode == 'ignore-term':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
record = {'pid': os.getpid(), 'ppid': os.getppid(), 'pgid': os.getpgrp(),
          'token': a.token, 'role': a.role, 'mode': a.mode, 'at': time.time()}
with (a.root / 'processes.jsonl').open('a') as f:
    f.write(json.dumps(record) + '\n')
if a.role == 'body' and a.mode in {'orphan-return', 'orphan-error', 'tree-hang', 'tree-ignore-term'}:
    child_mode = 'ignore-term' if a.mode == 'tree-ignore-term' else 'hang'
    subprocess.Popen([sys.executable, '-B', __file__, '--root', str(a.root),
                      '--token', a.token, '--role', 'descendant', '--mode', child_mode])
    deadline = time.monotonic() + 5
    while not (a.root / 'heartbeat-descendant.json').exists():
        if time.monotonic() >= deadline:
            raise SystemExit(92)
        time.sleep(.02)
if a.mode == 'simple-return':
    raise SystemExit(0)
if a.mode in {'orphan-return', 'orphan-error'}:
    raise SystemExit(7 if a.mode == 'orphan-error' else 0)
while True:
    path = a.root / ('heartbeat-' + a.role + '.json')
    tmp = a.root / ('heartbeat-' + a.role + '.tmp')
    tmp.write_text(json.dumps(dict(record, heartbeat_at=time.time(), heartbeat_monotonic=time.monotonic())))
    os.replace(tmp, path)
    time.sleep(.1)
