#!/usr/bin/env python3
"""Replay the two exact source samples retained by the original failed probe.

This is a minimized synthetic packet, not a native SDK run. The original full
reports remain under replay-002/C08_calibration; no original report was edited.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
scripts = Path(sys.argv[1]) if len(sys.argv)>1 else REPO/'native-ui-agent/scripts'
sys.path.insert(0,str(scripts))
import native_checks
plan=json.loads((HERE/'plan.json').read_text())
observation=json.loads((HERE/'observation.json').read_text())
result=native_checks.evaluate(plan,observation,'ios')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['assertions'][0]['status']=='unassessed'else 1)
