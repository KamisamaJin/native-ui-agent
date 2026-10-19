#!/usr/bin/env python3
"""Cache-free integrity + deterministic native-fact checks; not an SDK replay."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 index=read(R/'engineering/index.json');tests=shots=0
 for name,entry in index.items():
  d=R/'engineering'/name;m=read(d/'manifest.json');o=read(d/'observation.json')
  assert m['native_test_count']==entry['native_test_count']==1
  assert sha(d/'manifest.json')==entry['manifest_sha256']
  for path,digest in read(d/'portable-sha256.json').items():assert sha(d/path)==digest,(name,path)
  for s in o['snapshots']:assert (d/s['screenshot']).is_file(),(name,s['index']if'index'in s else s['name'])
  tests+=1;shots+=len(o['snapshots'])
 first=read(R/'engineering/ios-geometry-first-failed/observation.json');assert first['status']=='failed' and not any(x['complete']for x in first['state_captures'])
 fixed=read(R/'engineering/ios-geometry-fixed/observation.json');assert fixed['status']=='passed' and len(fixed['state_captures'])==4 and all(x['complete']for x in fixed['state_captures'])
 assert all(s['same_process']for s in fixed['steps'])
 reveal=read(R/'engineering/ios-reveal-nested/observation.json');assert reveal['status']=='passed'
 nested=reveal['snapshots'][0]['control_groups'][0];assert nested['resolution']=='ambiguous_native_controls' and nested['native_control_count']==2
 lower=reveal['steps'][1];assert lower['activation_target']['fully_within_viewport'] and [e['event']for e in lower['callback_delta']]==['lower']
 assert reveal['steps'][2]['outcome']=='blocked_disabled'and not reveal['steps'][2]['callback_delta']
 assert any(n['identifier']=='lower.heading'and n['fully_within_viewport']for n in reveal['snapshots'][reveal['steps'][0]['after']]['nodes'])
 android=read(R/'engineering/android-nested-static/observation.json');a,b,c=android['steps'];assert a['native_controls']==2 and a['outcome']=='unavailable'and not a['callback_delta'];assert b['outcome']=='observed'and not b['callback_delta'];assert c['outcome']=='tapped'and c['callback_delta']==['last']
 state=read(R/'engineering/android-state-positive/observation.json');assert state['phase']=='complete'and len(state['state_captures'])==6 and all(c['complete']for c in state['state_captures'])
 assert state['steps'][0]['callback_delta']==['probe.last']and state['steps'][1]['model_update']and state['steps'][2]['outcome']=='blocked_disabled'
 spec=importlib.util.spec_from_file_location('checks',R.parents[1]/'native-ui-agent/scripts/native_checks.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 for o,p in [(fixed,'ios'),(state,'android')]:
  for c in o['state_captures']:
   result=module.state_evidence(o,{'id':c['state_id'],'input_index':c['binding']['fixture_index'],'after_action':c['after_action']});assert result[1],(p,c['state_id'],result[2])
 print(json.dumps({'status':'passed_archived_engineering_checks','native_tests':tests,'native_snapshots':shots,'retained_failed_geometry_attempt':True,'scope':'Portable evidence and deterministic facts; does not rerun native SDKs or grade styles.'}))
if __name__=='__main__':main()
