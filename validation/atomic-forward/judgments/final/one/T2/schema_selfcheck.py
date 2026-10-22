from pathlib import Path
import sys,json,time,hashlib,traceback
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'));import acceptance
load=lambda p:json.loads(p.read_text())
summary={'purpose':'Schema/evidence-binding self-check only. Each call supplies this one judge twice; no independent consensus is claimed. One attempt per case. Supported judgments are not changed to optimize the result.','cases':{}}
for d in sorted((B/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(d.parts[-3:]);i=load(d/'inputs.json');judge=load(O/key/'judge.json');obs=load(B/i['observation']);designroot=B/i['design_root'];t=time.time()
 try:
  result=acceptance.evaluate(load(d/'plan.json'),load(designroot/'design-lock.json'),i['approval']['design_lock_sha256'],load(designroot/'policy.json'),i['approval']['policy_sha256'],obs,i['observation_sha256'],(B/i['root']).resolve(),i['platform'],load(B/i['environment']),judge,judge)
  out=O/key/'schema-selfcheck-attempt-1.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  nativefs=[r for r in result['rows'] if r['method']=='authoritative_fact' and r['ungated_fact_status']=='failed']
  row={'accepted':True,'startedAtUnix':t,'finishedAtUnix':time.time(),'counts':result['counts'],'native_F_ids':[r['id'] for r in nativefs],'native_U_ids':[r['id'] for r in result['rows'] if r['method']=='authoritative_fact' and r['ungated_fact_status']=='unassessed'],'own_visual_F_ids':[r['id'] for r in result['rows'] if r['method']!='authoritative_fact' and r['status']=='failed'],'own_visual_U_ids':[r['id'] for r in result['rows'] if r['method']!='authoritative_fact' and r['status']=='unassessed'],'environment':result['environment']['status']}
 except Exception as ex:
  row={'accepted':False,'startedAtUnix':t,'finishedAtUnix':time.time(),'error':str(ex),'traceback':traceback.format_exc()}
  (O/key/'rejected-schema-attempt-1.json').write_text(json.dumps(row,indent=2)+'\n')
 summary['cases'][key]=row
 print(key,row,flush=True)
(O/'schema-selfcheck-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
