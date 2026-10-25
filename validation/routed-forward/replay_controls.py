#!/usr/bin/env python3
"""Re-execute frozen independent controls without rewriting original outcomes."""
import json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
cache=R/'cache/ci-controls';cache.mkdir(parents=True,exist_ok=True)
output=cache/'neutral'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',NEUTRAL_PROBE_SCRIPTS=str(R/'candidate-v11/scripts'))
result=subprocess.run([sys.executable,'-B',str(R/'probe-review/replay006-adapter.py'),'--output',str(output)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(cache/'neutral.log').write_text(result.stdout)
# Independent strict oracle deliberately retains the non-acceptance C08 difference.
value=json.loads((output/'results.json').read_text());rows=value['results'];old=json.loads((R/'probe-review/replay-006/results.json').read_text())['results']
assert [(v['id'],v['status'],v['failures'])for v in rows]==[(v['id'],v['status'],v['failures'])for v in old]
print(json.dumps({'scope':'Synthetic transport only; original oracle difference retained','returncode':result.returncode,'cases':len(rows),'passed':sum(v['status']=='passed'for v in rows)}))
