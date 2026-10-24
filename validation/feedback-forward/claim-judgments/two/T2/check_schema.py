from pathlib import Path
import json, importlib.util, time, hashlib, traceback
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=ROOT/'claim-judgments/two/T2'
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
d=json.loads((ROOT/'claim-inputs/T2/inputs.json').read_text())
j=json.loads((OUT/'judgment.json').read_text())
request={'scope':'Schema check only: one independent panel is deliberately supplied twice. No independent agreement or performance estimate is asserted.','input_sha256':hashlib.sha256((ROOT/'claim-inputs/T2/inputs.json').read_bytes()).hexdigest(),'truth':[{k:r.get(k) for k in ['key','status','cause_category']} for r in d['initial']],'claims':{},'clusters_one':j['clusters'],'clusters_two':j['clusters']}
for alias,u in d['units'].items():
 request['claims'][alias]=[{**{k:c[k] for k in ['claim_id','origin','original_status','original_scope']},'judge_one':j['claims'][alias][c['claim_id']],'judge_two':j['claims'][alias][c['claim_id']]} for c in u['claims']]
save('schema-request.json',request)
result={'startedAtUnix':time.time(),'checks':[],'failed_attempts':[]}
try:
 assert set(j)=={'claims','clusters'}
 assert set(j['claims'])==set(d['units'])
 by={r['key']:r for r in d['initial']}
 product={k for k,r in by.items() if r['status']=='failed' and r.get('cause_category')=='product'}
 for alias,u in d['units'].items():
  expected={c['claim_id'] for c in u['claims']}
  assert set(j['claims'][alias])==expected
  for c in u['claims']:
   v=j['claims'][alias][c['claim_id']]
   assert v['status'] in ['TP','FP','U'] and v['reason']
   assert set(v['supported_rows'])<=set(c['original_scope']) and set(v['supported_rows'])<=product
   if v['status']!='TP': assert v['supported_rows']==[]
   if v['status']=='FP': assert v.get('false_alarm_supported') is True
 result['checks'].append({'check':'exact IDs, shape, supported-row subsets, FP evidence flag','status':'passed'})
 spec=importlib.util.spec_from_file_location('frozen_metrics',ROOT/'metrics.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 groups=m.agreed_clusters(request['clusters_one'],request['clusters_two'],product)
 result['checks'].append({'check':'metrics.agreed_clusters with own request twice','status':'passed','output':groups,'interpretation':'schema only'})
 for alias,claims in request['claims'].items():
  res=m.detection(request['truth'],claims,groups['confirmed'])
  result['checks'].append({'check':'metrics.detection with own request twice','alias':alias,'status':'passed','output':res,'interpretation':'schema only; not independent agreement'})
except Exception as e:
 result['failed_attempts'].append({'error':repr(e),'traceback':traceback.format_exc()})
 result['status']='failed'
else:result['status']='passed'
result['finishedAtUnix']=time.time()
save('schema-check.json',result)
print(json.dumps({'status':result['status'],'checks':len(result['checks']),'failed_attempts':len(result['failed_attempts'])}))
if result['status']!='passed':raise SystemExit(1)
