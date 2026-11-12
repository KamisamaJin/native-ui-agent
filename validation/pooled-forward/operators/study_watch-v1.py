#!/usr/bin/env python3
"""Continuous whole-study sampling. Stop only with an explicit owner stop file."""
import json
from pathlib import Path
import time
from measure import Meter

R = Path(__file__).resolve().parent
spec = json.loads((R / 'operators/whole-study-meter-spec.json').read_text())
with Meter(spec, R / 'operators/whole-study-meter.jsonl') as meter:
    (R / 'operators/whole-study-meter.ready').write_text(str(time.time()) + '\n')
    while not (R / 'operators/whole-study-meter.stop').exists():
        if meter.error or any(v['budget_exceeded'] for v in meter.samples[-1:]):
            halt = R / 'operators/RESOURCE-HALT.json'
            if not halt.exists(): halt.write_text(json.dumps({'at_unix': time.time(), 'error': meter.error, 'last_sample': meter.samples[-1]}) + '\n')
        time.sleep(.5)
