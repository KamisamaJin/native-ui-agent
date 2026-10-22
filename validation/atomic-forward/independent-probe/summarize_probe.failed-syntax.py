import json,sys,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parents[2]/'native-ui-agent/scripts'))
from native_checks import callback_verdict
r=R/'captures/preflight-android';o=json.loads((r/'observation.json').read_text())
checks=[]
for i,step in enumerate(o['steps']):
 checks.append({'index':i,'actual_type':step['type'],'outcome':step.get('outcome'),'actual_callback':step.get('callback_delta'),'dispatch':step.get('dispatch'),'binding_after':step.get('binding_after')})
result={'observation_sha256':hashlib.sha256((r/'observation.json').read_bytes()).hexdigest(),'test_count':json.loads((r/'manifest.json').read_text())['native_test_count'],'steps':checks,'all_state_sweeps_complete':all(s['complete']for s in o['state_captures']),'session_ids':list({s['binding']['instance']for s in o['state_captures']}),'original_images_seen':['000-state_initial_0.png'],'scope':'Original generic observer capability evidence. Not a product substitute or physical Android touch proof.'}
(R/'preflight-android-facts.json').write_text(json.dumps(result,indent=2)+'\n')
# Record exact requested environment ahead of any acceptance consideration; no second judge is fabricated.
e=R/'environment';e.mkdir(exist_ok=True)
for p in ['ios','android']:
 for scenario in ['normal','narrow-large']:
  n=scenario=='narrow-large';env={'width':260 if n else390,'height':600,'direction':'ltr','theme':'light'}
  env.update({'dynamic_type':'accessibility3'if n else'large'}if p=='ios'else{'font_scale':1.7 if n else1.0})
  (e/f'{p}-{scenario}.json').write_text(json.dumps(env,indent=2)+'\n')
