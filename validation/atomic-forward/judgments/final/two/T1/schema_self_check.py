import sys,json,pathlib,time,hashlib,traceback
sys.dont_write_bytecode=True
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/two/T1';sys.path.insert(0,str(B/'candidate-v8/scripts'))
import acceptance,design_contract
summary=[]
for p in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*/inputs.json')):
 i=json.loads(p.read_text());key='/'.join([i['source'],i['platform'],i['case']]);dest=O/key/'schema-self-check-1.json'
 if dest.exists():raise RuntimeError('Fresh self-check output required')
 started=time.time()
 try:
  plan=json.loads((p.parent/'plan.json').read_text());lock=json.loads((B/i['design_root']/'design-lock.json').read_text());policy=json.loads((B/i['design_root']/'policy.json').read_text());obs=json.loads((B/i['observation']).read_text());env=json.loads((B/i['environment']).read_text());judge=json.loads((O/key/'judge.json').read_text())
  assert design_contract.digest(lock)==i['approval']['design_lock_sha256']
  assert design_contract.digest(policy)==i['approval']['policy_sha256']
  assert design_contract.digest(env)==i['approval']['environment_sha256'][i['case']][i['platform']]
  assert hashlib.sha256((B/i['observation']).read_bytes()).hexdigest()==i['observation_sha256']
  # The same judgment is supplied to both arguments solely to validate our own schema.
  # This is one judge, not independent agreement and never a consensus result.
  result=acceptance.evaluate(plan,lock,i['approval']['design_lock_sha256'],policy,i['approval']['policy_sha256'],obs,i['observation_sha256'],B/i['root'],i['platform'],env,judge,judge)
  record={'schema_self_check_only':True,'not_independent_consensus':True,'own_request_used_in_both_arguments':True,'startedAtUnix':started,'finishedAtUnix':time.time(),'counts':result['counts'],'environment_status':result['environment']['status'],'recomputed_failures':[r for r in result['rows']if r['ungated_fact_status']=='failed'],'unsupported_rows':[{'id':r['id'],'reason':r['authoritative']['reason']}for r in result['rows']if r['status']=='unassessed']}
  dest.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');print(key,result['counts'],result['environment']['status'],flush=True)
  summary.append({'case':key,'accepted_schema':True,'counts':result['counts']})
 except Exception as e:
  dest=dest.with_name('schema-self-check-1-rejected.json');dest.write_text(json.dumps({'error':repr(e),'traceback':traceback.format_exc(),'startedAtUnix':started,'finishedAtUnix':time.time()},indent=2)+'\n');print(key,'REJECTED',repr(e),flush=True);summary.append({'case':key,'accepted_schema':False,'error':repr(e)})
(O/'schema-self-check-summary.json').write_text(json.dumps({'scope':'Own JSON schema and native/pixel recomputation only. This is not independent consensus.','results':summary},indent=2)+'\n')
