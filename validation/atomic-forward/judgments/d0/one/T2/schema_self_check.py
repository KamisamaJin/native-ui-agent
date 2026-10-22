import pathlib,json,sys,time
sys.dont_write_bytecode=True
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/one/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import acceptance
load=lambda p:json.loads(p.read_text())
lock=load(B/'design-v2/T2/public/design-lock.json');policy=load(B/'design-v2/T2/public/policy.json');results=[]
for p in sorted((B/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T2'));i=load(p/'inputs.json');judge=load(O/key/'judge.json');started=time.time()
 try:
  report=acceptance.evaluate(load(p/'plan.json'),lock,i['approval']['design_lock_sha256'],policy,i['approval']['policy_sha256'],load(B/i['observation']),i['observation_sha256'],B/i['root'],i['platform'],load(B/i['environment']),judge,judge)
  result={'case':key,'schema':'accepted','startedAtUnix':started,'finishedAtUnix':time.time(),'purpose':'Schema/binding self-check only. The identical reviewer request was passed in both panel positions; this is not independent consensus.','report':report}
 except Exception as e:
  result={'case':key,'schema':'rejected','startedAtUnix':started,'finishedAtUnix':time.time(),'exception':type(e).__name__,'error':str(e)}
 results.append(result);print(key,result['schema'],flush=True)
 (O/'schema-self-check-01.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
