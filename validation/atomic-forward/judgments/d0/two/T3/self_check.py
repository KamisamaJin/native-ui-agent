import sys
sys.dont_write_bytecode=True
import pathlib,json,traceback,hashlib,time
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/two/T3';sys.path.insert(0,str(B/'candidate-v8/scripts'))
import acceptance,design_contract
results=[]
for p in sorted((B/'evaluation-inputs/d0/T3').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T3'));inp=json.loads((p/'inputs.json').read_text());platform=inp['platform'];load=lambda p:json.loads(p.read_text());out=O/key/'schema-self-check-01.json';started=time.time()
 try:
  panel=load(O/key/'judge.json');report=acceptance.evaluate(load(p/'plan.json'),load(B/inp['design_root']/'design-lock.json'),inp['approval']['design_lock_sha256'],load(B/inp['design_root']/'policy.json'),inp['approval']['policy_sha256'],load(B/inp['observation']),inp['observation_sha256'],B/inp['root'],platform,load(B/inp['environment']),panel,panel)
  out.write_text(json.dumps({'purpose':'Schema and frozen fact recomputation only. Same anonymous judge passed as both requests; this is not independent consensus.','report':report},indent=2)+'\n');results.append({'case':key,'schema_accepted':True,'elapsed_seconds':time.time()-started});print(key,'schema accepted')
 except Exception as e:
  out.write_text(json.dumps({'purpose':'Rejected schema self-check attempt preserved','error':str(e),'traceback':traceback.format_exc()},indent=2)+'\n');results.append({'case':key,'schema_accepted':False,'error':str(e)});print(key,'REJECTED',str(e))
(O/'schema-self-check-summary.json').write_text(json.dumps(results,indent=2)+'\n')
with(O/'commands.log').open('a')as f:f.write('Ran self_check.py: frozen acceptance.evaluate once per case, using this same judge request twice solely for schema/evidence binding validation and native/pixel recomputation, never independent consensus. Every attempt retained under each case/schema-self-check-01.json.\n')
