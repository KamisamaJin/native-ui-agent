from pathlib import Path
import json,sys,time,traceback
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');OUT=BASE/'judgments/d0/one/T3'
sys.path.insert(0,str(BASE/'candidate-v8/scripts'))
import acceptance
results=[]
for p in sorted((BASE/'evaluation-inputs/d0/T3').glob('*/*/*')):
 so,pl,ca=p.parts[-3:]; i=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());design=BASE/i['design_root'];j=json.loads((OUT/so/pl/ca/'judge.json').read_text());start=time.time()
 try:
  report=acceptance.evaluate(plan,json.loads((design/'design-lock.json').read_text()),i['approval']['design_lock_sha256'],json.loads((design/'policy.json').read_text()),i['approval']['policy_sha256'],json.loads((BASE/i['observation']).read_text()),i['observation_sha256'],(BASE/i['root']).resolve(),pl,json.loads((BASE/i['environment']).read_text()),j,j)
  # One request occupies both slots solely to validate its schema and scoped identities.
  wrapper={'purpose':'Schema self-check only. The identical single reviewer request is supplied in both evaluator slots. This is NOT independent consensus or a second judgment.','startedAtUnix':start,'finishedAtUnix':time.time(),'accepted':True,'report':report}
  (OUT/so/pl/ca/'schema-self-check.json').write_text(json.dumps(wrapper,indent=2)+'\n')
  results.append({'case':'/'.join([so,pl,ca]),'schemaAccepted':True,'seconds':time.time()-start})
 except Exception as e:
  rejected={'startedAtUnix':start,'finishedAtUnix':time.time(),'error':str(e),'traceback':traceback.format_exc(),'submitted_request':j}
  (OUT/so/pl/ca/'schema-rejected-attempt-1.json').write_text(json.dumps(rejected,indent=2)+'\n');results.append({'case':'/'.join([so,pl,ca]),'schemaAccepted':False,'error':str(e)})
(OUT/'schema-self-check-summary.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
