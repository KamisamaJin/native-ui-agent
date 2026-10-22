from pathlib import Path
import sys,json,hashlib,time,traceback
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');OUT=R/'judgments/d0/two/T2';sys.path.insert(0,str(R/'candidate-v8/scripts'));import acceptance,design_contract
checks=[]
for p in sorted((R/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=p.relative_to(R/'evaluation-inputs/d0/T2');inp=json.loads((p/'inputs.json').read_text());panel=json.loads((OUT/key/'judge.json').read_text());started=time.time();dest=OUT/'schema-self-check'/key;dest.mkdir(parents=True,exist_ok=True)
 try:
  load=lambda p:json.loads(p.read_text());lock=load(R/inp['design_root']/'design-lock.json');policy=load(R/inp['design_root']/'policy.json');env=load(R/inp['environment']);obs=load(R/inp['observation']);plan=load(p/'plan.json')
  assert design_contract.digest(env)==inp['approval']['environment_sha256'][inp['case']][inp['platform']]
  report=acceptance.evaluate(plan,lock,inp['approval']['design_lock_sha256'],policy,inp['approval']['policy_sha256'],obs,inp['observation_sha256'],R/inp['root'],inp['platform'],env,panel,panel)
  # Deliberately the SAME panel twice: this is validation of JSON and recomputation only.
  (dest/'recomputed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  item={'case':str(key),'schema_valid':True,'startedAtUnix':started,'finishedAtUnix':time.time(),'same_panel_twice':True,'independent_consensus':False,'counts':report.get('counts'),'report':'schema-self-check/'+str(key)+'/recomputed.json'}
 except Exception as e:
  item={'case':str(key),'schema_valid':False,'startedAtUnix':started,'finishedAtUnix':time.time(),'same_panel_twice':True,'independent_consensus':False,'error':str(e),'traceback':traceback.format_exc()};(dest/'rejected-attempt-1.json').write_text(json.dumps(item,indent=2)+'\n')
 checks.append(item);print(json.dumps(item),flush=True)
(OUT/'schema-self-check'/'index.json').write_text(json.dumps(checks,indent=2)+'\n')
