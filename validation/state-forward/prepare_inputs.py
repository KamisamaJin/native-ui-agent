#!/usr/bin/env python3
"""Translate fixed case inputs to native routes; no product implementation."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def all_ids(case):
 suffix=['card','title','status','charge.caption','charge.value','summary','mode.title','mode.single','mode.duplex','priority','priority.helper','breakdown.toggle','balance','approve']
 suffix += ['breakdown.'+kind+'.'+part for kind in ['ink','paper','priority','total']for part in ['label','value']]
 suffix += ['job.'+j['id']+'.'+part for model in case['models']for j in model['jobs']for part in ['toggle','title','subtitle','price']]
 return list(dict.fromkeys('printbatch.'+s for s in suffix))
def translate(case,common_cells=None):
 host=case['host'];models=case['models'];actions=[];updates=[];mapping={};input_index=0
 checkpoints=[dict(case['initial'],type='initial',actionIndex=0)]+case['actions']
 for cp in checkpoints:
  sid=cp['stateID'];kind=cp['type'];trigger=None;action_sid=sid+'.trigger'if cp['full_content']else sid
  if kind=='activate':
   trigger=len(actions);actions.append({'type':'tap','target':{'identifier':cp['targetID']},'reveal':True,'allow_disabled':True,'max_steps':24,'state_id':action_sid})
  elif kind=='replaceModel':
   trigger=len(actions);input_index+=1;updates.append({'host':host,'model':models[cp['modelIndex']]});actions.append({'type':'apply_next_fixture','state_id':action_sid})
  elif kind!='initial':raise ValueError('Unknown independently supplied trigger')
  after=trigger
  if cp['full_content']:
   after=len(actions);actions.append({'type':'sweep','state_id':sid,'max_steps':24})
  elif common_cells is not None and trigger is not None:
   # Exact targets from the frozen independent denominator. Root structure and
   # proven-absent nodes need full coverage, not fruitless target searches.
   absent={c['targetID'] for c in common_cells if c.get('stateID')==sid and c.get('operator')=='presence' and c.get('expected') is False}
   ids=sorted({c['targetID']for c in common_cells if c.get('stateID')==sid and c.get('targetID') and c['targetID']!='printbatch.card' and c['targetID']not in absent and not c.get('classification','').startswith('notApplicable')})
   ids=ids[:32]
   if ids:actions[trigger]['after_targets']=[{'identifier':i}for i in ids]
  mapping[sid]={'state_id':sid,'input_index':input_index,'after_action':after,'state_action_index':after,'trigger_action_index':trigger,'logical_action_index':cp['actionIndex'],'full_content':cp['full_content'],'trigger_type':kind}
 config={'initial':{'host':host,'model':models[0]},'updates':updates,'width':host['width'],'viewportHeight':600,'theme':host['theme'],'direction':host['direction'],'dynamic_type':'large','fontScale':1.0,'state_capture':False,'max_scrolls':24,'observation_targets':[{'identifier':i}for i in all_ids(case)]}
 return config,actions,mapping
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--common',action='store_true');p.add_argument('--heldout',action='store_true');a=p.parse_args();assert not a.output.exists()
 cases=read(R/'design/public/cases.json')['cases']
 if a.heldout:cases+=read(R/'design/private/heldout-cases.json')['cases']
 cells=read(R/'design/private/oracle.json')['cells']if a.common else None
 for case in cases:
  fixture,actions,mapping=translate(case,cells)
  for name,value in [('fixtures.json',fixture),('actions.json',actions),('mapping.json',mapping)]:save(a.output/case['caseID']/name,value)
 files={str(p.relative_to(a.output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(a.output.rglob('*.json'))}
 save(a.output/'seal.json',{'createdAtUTC':datetime.now(timezone.utc).isoformat(),'kind':'independent-common'if a.common else'public-builder-start','files':files,'textScalePolicy':'Presentation only; native fontScale1.0 and ordinary large DynamicType.','targetSelection':'Common: deduplicated non-root expected-present selectors sorted, max32. Other required native/absent/style cells retain full denominator.'if a.common else'No after-target set supplied; builder owns its review plan.'})
 print(json.dumps({'cases':len(cases),'output':str(a.output)}))
if __name__=='__main__':main()
