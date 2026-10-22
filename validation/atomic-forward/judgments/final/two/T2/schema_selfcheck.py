from pathlib import Path
import sys,json,traceback,time
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/two/T2';sys.path.insert(0,str(B/'candidate-v8/scripts'))
import acceptance
load=lambda p:json.loads(p.read_text())
counts=[]
for en in load(O/'inspection-index.json'):
 rel=en['case'];d=O/rel;p=B/'evaluation-inputs/final/T2'/rel;i=load(p/'inputs.json');root=B/i['root'];judge=load(d/'judge.json');started=time.time()
 try:
  report=acceptance.evaluate(load(p/'plan.json'),load(B/i['design_root']/'design-lock.json'),i['approval']['design_lock_sha256'],load(B/i['design_root']/'policy.json'),i['approval']['policy_sha256'],load(B/i['observation']),i['observation_sha256'],root,i['platform'],load(B/i['environment']),judge,judge)
  result={'purpose':'Schema self-check only: the same request is supplied in both evaluator judge slots. This is not independent consensus.','startedAtUnix':started,'finishedAtUnix':time.time(),'report':report}
  (d/'schema-selfcheck.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  counts.append({'case':rel,'accepted':True,'counts':report['counts'],'environment':report['environment']['status'],'supported_failures':[r['id'] for r in report['rows'] if r['status']=='failed']})
  print(rel,report['counts'],flush=True)
 except Exception:
  (d/'schema-selfcheck-rejected-1.txt').write_text(traceback.format_exc());counts.append({'case':rel,'accepted':False});print(rel,'REJECTED',flush=True)
(O/'schema-selfcheck-summary.json').write_text(json.dumps({'purpose':'Schema validation, not consensus','cases':counts},indent=2)+'\n')
