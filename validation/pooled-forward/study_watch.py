#!/usr/bin/env python3
"""Continuous whole-study sampling. Stop only with an explicit owner stop file."""
import json
import argparse
from pathlib import Path
import time
from measure import Meter

R = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--spec', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
p.add_argument('--stop', type=Path, required=True); a = p.parse_args()
spec = json.loads(a.spec.read_text())
with Meter(spec, a.output) as meter:
    a.output.with_suffix('.ready').write_text(str(time.time()) + '\n')
    while not a.stop.exists():
        if meter.error or any(v['budget_exceeded'] for v in meter.samples[-1:]):
            halt = R / 'operators/RESOURCE-HALT.json'
            if not halt.exists(): halt.write_text(json.dumps({'at_unix': time.time(), 'error': meter.error, 'last_sample': meter.samples[-1]}) + '\n')
        time.sleep(.5)
