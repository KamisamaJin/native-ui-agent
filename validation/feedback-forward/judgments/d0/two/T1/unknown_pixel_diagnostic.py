import json,sys,collections
from pathlib import Path
sys.dont_write_bytecode=True
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');out=b/'judgments/d0/two/T1';sys.path.insert(0,str(b/'candidate-v9/scripts'))
import native_checks,native_pixels
p=b/'evaluation-inputs/d0/T1/initial/android/P2';i=json.loads((p/'inputs.json').read_text());o=json.loads((b/i['observation']).read_text());pl=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());rows=[]
for r in cat['rows']:
 if r['requirement_id']!='status-leading-clear':continue
 st=next(s for s in pl['states'] if s['id']==r['state']);found,complete,why,cap=native_checks.bound_state_evidence(o,st);samples=[]
 for n,s in found:
  z=native_pixels.sample(s,r['target'],'android',b/i['raw'],r['sampling']);samples.append({'snapshot_index':n,'status':z['status'],'eligible':z.get('eligible'),'reason':z['reason'],'source':str(b/i['raw']/s['screenshot'])})
 rows.append({'id':r['id'],'state_scoped_indices':[n for n,s in found],'samples':samples,'disposition':'U preserved; no reviewer pixel actual or failure cause supplied.'})
 print(r['id'],[(z['snapshot_index'],z['status'],z.get('eligible'),z['reason']) for z in samples])
(out/'unknown-pixel-diagnostic.json').write_text(json.dumps({'scope':'Original approved pixel rule and exact-state original frames; diagnostic only, no modified thresholds, actual overrides, failure reclassification or independence claim.','rows':rows},indent=2)+'\n')
