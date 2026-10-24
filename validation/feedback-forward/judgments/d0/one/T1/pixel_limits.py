import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=R/'judgments/d0/one/T1'
sys.path.insert(0,str(R/'candidate-v9/scripts'))
import native_pixels,native_checks
p=R/'evaluation-inputs/d0/T1/initial/android/P2';inp=json.loads((p/'inputs.json').read_text());obs=json.loads((R/inp['observation']).read_text());plan=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());records=[]
for rule in cat['rows']:
 if rule['requirement_id']!='status-leading-clear':continue
 state=next(s for s in plan['states']if s['id']==rule['state']);found,complete,why,capture=native_checks.bound_state_evidence(obs,state)
 for idx,s in found:
  result=native_pixels.sample(s,rule['target'],'android',R/inp['raw'],rule['sampling']);proof=result.get('proof',{})
  records.append({'id':rule['id'],'index':idx,'status':result['status'],'eligible':result.get('eligible'),'reason':result['reason'],'original':str((R/inp['raw']/s['screenshot']).relative_to(R)),'sha256':proof.get('sha256'),'roi':proof.get('region_pixels'),'sample_count':proof.get('sample_count'),'histogram':proof.get('histogram')})
(O/'checks/android-P2-leading-strip-diagnostics.json').write_text(json.dumps({'scope':'Original approved sampler output, retained as unknown where solid support is insufficient. This does not alter judge values or attribute a product failure.','observation_sha256':inp['observation_sha256'],'samples':records},indent=2)+'\n')
for r in records:
 if r['eligible'] and r['status']!='measured': print(r['id'],r['index'],r['reason'],r['sample_count'],r['histogram'][:4]if r['histogram']else None)
