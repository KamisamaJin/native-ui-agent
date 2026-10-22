from pathlib import Path
import json,sys,time,traceback
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T1'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import acceptance
L=lambda p:json.loads(p.read_text())
results={}
for p in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*')):
 key='/'.join(p.parts[-3:]);i=L(p/'inputs.json');j=L(O/key/'judge.json');started=time.time()
 try:
  # Deliberately reuse this same independent request twice ONLY to self-check schema.
  report=acceptance.evaluate(L(p/'plan.json'),L(B/i['design_root']/'design-lock.json'),i['approval']['design_lock_sha256'],L(B/i['design_root']/'policy.json'),i['approval']['policy_sha256'],L(B/i['observation']),i['observation_sha256'],B/i['root'],i['platform'],L(B/i['environment']),j,j)
  (O/key/'schema-self-check.json').write_text(json.dumps({'purpose':'Same judge reused twice solely for schema self-check; this is not independent consensus.','report':report},indent=2)+'\n')
  results[key]={'startedAtUnix':started,'finishedAtUnix':time.time(),'accepted':True,'keys':list(report)}
  print(key,'accepted',flush=True)
 except Exception as e:
  (O/key/'schema-rejected-attempt-01.json').write_text(json.dumps({'error':str(e),'traceback':traceback.format_exc(),'judge':j},indent=2)+'\n');results[key]={'startedAtUnix':started,'finishedAtUnix':time.time(),'accepted':False,'error':str(e)};print(key,'REJECTED',str(e),flush=True)
 (O/'schema-check-log.json').write_text(json.dumps(results,indent=2)+'\n')
