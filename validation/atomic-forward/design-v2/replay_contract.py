#!/usr/bin/env python3
"""Fresh evaluator compilation from approved original action route; no runtime UI."""
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
P=argparse.ArgumentParser();P.add_argument('--task',choices=['T1','T2','T3'],required=True);P.add_argument('--case',choices=['P1','P2','H1'],required=True);P.add_argument('--platform',choices=['ios','android'],required=True);P.add_argument('--output',type=Path,required=True);a=P.parse_args()
b=R/a.task/('private' if a.case=='H1' else 'public');approval=json.loads((b/'approval.json').read_text());tools=R.parent/'candidate-v8'/'scripts';sys.path.insert(0,str(tools));import design_contract as d
for name,key in [('design-lock.json','design_lock_sha256'),('policy.json','policy_sha256')]:
 if d.digest(d.load(b/name))!=approval[key]:raise RuntimeError('Approval digest changed: '+name)
env=b/'cases'/a.case/f'environment.{a.platform}.json'
if d.digest(d.load(env))!=approval['environment_sha256'][a.case][a.platform]:raise RuntimeError('Environment digest changed')
subprocess.run([sys.executable,str(tools/'design_contract.py'),'compile','--lock',str(b/'design-lock.json'),'--lock-sha256',approval['design_lock_sha256'],'--scenario',a.case,'--platform',a.platform,'--bindings',str(b/'bindings.json'),'--actions',str(b/'cases'/a.case/f'actions.{a.platform}.json'),'--output',str(a.output)],check=True)
# plan states + stimulus_action preserve exact checkpoint and callback interval.
