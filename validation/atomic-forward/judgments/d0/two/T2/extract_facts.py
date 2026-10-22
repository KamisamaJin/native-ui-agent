from pathlib import Path
import json,sys
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');OUT=R/'judgments/d0/two/T2';sys.path.insert(0,str(R/'candidate-v8/scripts'));import native_checks,native_pixels
allfacts={};failure_samples={}
for p in sorted((R/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=str(p.relative_to(R/'evaluation-inputs/d0/T2'));i=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());auto=json.loads((p/'automatic.json').read_text());obs=json.loads((R/i['observation']).read_text());case={}
 for state in plan['states']:
  found,complete,reason,cap=native_checks.bound_state_evidence(obs,state);frames=[]
  for ind,s in found:
   targetfacts={}
   for tid in ['river.canvas','river.title','river.notice','river.choice.a','river.choice.b','river.choice.c','river.choice.d','river.choice.e','river.choice.f','river.disclosure','river.summary','river.submit','river.footer']:
    targetfacts[tid]=native_checks.resolve(s,{'identifier':tid},i['platform'])
   frames.append({'snapshot_index':ind,'binding':s.get('binding'),'binding_after_capture':s.get('binding_after_capture'),'capture_consistent':s.get('capture_consistent'),'targets':targetfacts})
  case[state['id']]={'complete':complete,'reason':reason,'frames':frames,'after_action':state['after_action'],'action_step':obs['steps'][state['after_action']]}
 allfacts[key]=case
 failure_samples[key]={}
 for rule in auto['assertions']:
  if rule['status']=='failed':
   row=next(v for v in cat['rows'] if v['id']==rule['id'])
   samples=[dict(native_pixels.sample(obs['snapshots'][n],row['target'],i['platform'],R/i['root'],row['sampling']),snapshot_index=n) for n in rule['snapshot_indices']]
   failure_samples[key][rule['id']]=samples
   print(key,rule['id'],[(s['snapshot_index'],s['status'],hex(s.get('argb',0)),s.get('support'),s.get('proof',{}).get('native_box')) for s in samples])
(OUT/'native-state-facts.json').write_text(json.dumps(allfacts,indent=2)+'\n');(OUT/'failure-pixel-proofs.json').write_text(json.dumps(failure_samples,indent=2)+'\n')
