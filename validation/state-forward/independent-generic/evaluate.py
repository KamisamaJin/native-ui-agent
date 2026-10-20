#!/usr/bin/env python3
"""Evaluate original evidence and a clearly identified target-bundle replay."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time,datetime
p=argparse.ArgumentParser();p.add_argument('platform',choices=['ios','android']);p.add_argument('phase',choices=['probe','component']);a=p.parse_args()
root=Path(__file__).resolve().parent;repo=root.parents[2]
out=root/f'{a.platform}-{a.phase}'
copy=repo/f'validation/state-forward/cache/independent-generic/skill-{a.platform}-{a.phase}'
plan=root/('probe-plan'if a.phase=='probe'else'component-plan')/'plan.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=out/'observation.json';data=json.loads(source.read_text())
derived=out/'observation.targets-only.json'
data['state_captures']=[]
derived.write_text(json.dumps(data,indent=2)+'\n')
(out/'targets-only-derivation.json').write_text(json.dumps({'source':'observation.json','sha256':sha(source),'transformation':'Set state_captures to [] only; exact original snapshot records, steps, images and bindings retained. Evaluator replay isolates native observation_set fallback; this is not another native run.','derived_sha256':sha(derived)},indent=2)+'\n')
reviews=json.loads((root/f'{a.platform}-visual-decisions.json').read_text())if a.phase=='component'else None
logs=[]
for mode,observation in [('original',source),('targets-only',derived)]:
    cmd=[sys.executable,str(copy/'scripts/native_checks.py'),'--plan',str(plan),'--observation',str(observation),
         '--platform',a.platform,'--output',str(out/('checks.reviewed.json'if mode=='original'else'checks.targets-only.reviewed.json'))]
    if reviews:
        decisions=[]
        for state,indices in reviews[mode].items():
            snapshots=json.loads(source.read_text())['snapshots']
            decisions.append({'id':state+'/target-visual','method':'visual','status':'passed',
              'reason':reviews['reasons'][state], 'snapshot_indices':indices,
              'evidence':[{'path':snapshots[i]['screenshot'],'sha256':sha(out/snapshots[i]['screenshot'])}for i in indices]})
        manual=out/f'manual.{mode}.json'
        manual.write_text(json.dumps({'observation_sha256':sha(observation),'decisions':decisions},indent=2)+'\n')
        cmd+=['--manual',str(manual),'--root',str(out)]
    start=time.monotonic();result=subprocess.run(cmd,cwd=repo,text=True,capture_output=True)
    logs.append({'command':cmd,'cwd':str(repo),'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.monotonic()-start,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    print(result.stdout.strip(),flush=True)
(out/'evaluation-commands.json').write_text(json.dumps(logs,indent=2)+'\n')
raise SystemExit(max(x['exit_code']for x in logs))
