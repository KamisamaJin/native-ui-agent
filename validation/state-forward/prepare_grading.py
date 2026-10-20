#!/usr/bin/env python3
"""Add explicit native step pointers to a separate evaluator mapping copy.

Original sealed builder/common inputs are never rewritten. No oracle or product
value is read here; pointers and trigger identities come from delivered actions.
"""
import argparse,hashlib,json
from pathlib import Path

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists();a.output.mkdir(parents=True)
 ledger=[]
 for case in sorted(a.inputs.iterdir()):
  if not case.is_dir() or not (case/'mapping.json').is_file():continue
  for platform in ['ios','android']:
   actionfile=case/('actions.'+platform+'.json')
   if not actionfile.exists():actionfile=case/'actions.json'
   actions=read(actionfile)
   if isinstance(actions,dict):actions=actions['actions']
   mapping=read(case/'mapping.json')
   for state,spec in mapping.items():
    index=spec.get('trigger_action_index')
    if index is not None:
     assert type(index)is int and 0<=index<len(actions)
     spec['trigger_step_pointer']='/steps/'+str(index)
     spec['trigger_state_id']=actions[index]['state_id']
   target=a.output/case.name/('mapping.'+platform+'.json');target.parent.mkdir(exist_ok=True)
   target.write_text(json.dumps(mapping,indent=2,ensure_ascii=False)+'\n')
   ledger.append({'case':case.name,'platform':platform,'sourceMapping':str(case/'mapping.json'),'sourceMappingSHA256':sha(case/'mapping.json'),'sourceActions':str(actionfile),'sourceActionsSHA256':sha(actionfile),'derivedMapping':str(target.relative_to(a.output)),'derivedSHA256':sha(target)})
 (a.output/'provenance.json').write_text(json.dumps({'scope':'Additive actual-action pointer derivative, no original input/action mutation or expected-value derivation.','files':ledger},indent=2)+'\n')
 print(json.dumps({'cases':len(ledger)//2,'output':str(a.output)}))
if __name__=='__main__':main()
