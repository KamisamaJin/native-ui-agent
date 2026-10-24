from pathlib import Path
import sys,json,time,traceback,hashlib
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/final/one/T2'
sys.path.insert(0,str(B/'candidate-v9/scripts'))
import acceptance,design_contract
load=lambda p:json.loads(Path(p).read_text())
summary={}
for p in sorted((B/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(p.parts[-3:]);i=load(p/'inputs.json');plan=load(p/'plan.json');judge=load(O/key/'judge.json');scope=B/i['scope'];start=time.time()
 try:
  report=acceptance.evaluate(plan,load(scope/'design-lock.json'),i['approval']['design_lock_sha256'],load(scope/'policy.json'),i['approval']['policy_sha256'],load(B/i['observation']),i['observation_sha256'],B/i['raw'],i['platform'],load(B/i['environment']),judge,judge)
  item={'schema':'accepted','counts':report['counts'],'nonpassed':[{'id':r['id'],'status':r['status'],'reason':r['reason'],'authoritative':r['authoritative']} for r in report['rows'] if r['status']!='passed'],'environment_status':report['environment']['status'],'scope':'Self-check only: the identical own request filled both judge arguments. This is neither two independent judgments nor consensus nor human gold.','startedAtUnix':start,'endedAtUnix':time.time()}
  assert not any(r['status']=='failed' for r in report['rows']),'Supported F requires independent attribution before seal'
 except Exception as e:
  item={'schema':'rejected','error':str(e),'traceback':traceback.format_exc(),'startedAtUnix':start,'endedAtUnix':time.time()}
 path=O/key/'self-schema-check.json';path.write_text(json.dumps(item,indent=2)+'\n');summary[key]={k:v for k,v in item.items() if k not in ['nonpassed','traceback']};print(key,json.dumps(summary[key]),flush=True)
(O/'schema-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
