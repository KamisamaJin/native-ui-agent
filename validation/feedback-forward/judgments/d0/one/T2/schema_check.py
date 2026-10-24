from pathlib import Path
import json,sys,hashlib,time,traceback,importlib.util
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/d0/one/T2'
sys.path.insert(0,str(B/'candidate-v9/scripts'))
import acceptance,design_contract
# The explicitly permitted audit module imports the already-loaded frozen design_contract.
spec=importlib.util.spec_from_file_location('isolated_implementation_audit',str(B.parent.parent/'tools/implementation_audit.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lock=load(B/'design/T2/public/design-lock.json');policy=load(B/'design/T2/public/policy.json')
for attempt in [1,2]:
 summary={'startedAtUnix':time.time(),'method':'The exact same assessor submission occupies both judge parameters solely for schema/binding self-check; this is not independent agreement.','results':{}}
 for p in sorted((B/'evaluation-inputs/d0/T2').glob('*/*/*')):
  inp=load(p/'inputs.json');plat,case=p.parts[-2:];judge=load(O/f'initial/{plat}/{case}/judge.json');obspath=B/inp['observation'];request={'function':'frozen acceptance.evaluate','plan':str(p/'plan.json'),'design_lock':str(B/'design/T2/public/design-lock.json'),'design_sha256':inp['approval']['design_lock_sha256'],'policy':str(B/'design/T2/public/policy.json'),'policy_sha256':inp['approval']['policy_sha256'],'observation':str(obspath),'observation_sha256':sha(obspath),'root':str(B/inp['raw']),'platform':plat,'environment':str(B/inp['environment']),'judge_one':str(O/f'initial/{plat}/{case}/judge.json'),'judge_two':str(O/f'initial/{plat}/{case}/judge.json'),'non_independent_self_check':True}
  dest=O/f'schema-attempt-{attempt}/{plat}/{case}';dest.mkdir(parents=True,exist_ok=True);(dest/'request.json').write_text(json.dumps(request,indent=2)+'\n')
  try:
   result=acceptance.evaluate(load(p/'plan.json'),lock,request['design_sha256'],policy,request['policy_sha256'],load(obspath),sha(obspath),B/inp['raw'],plat,load(B/inp['environment']),judge,judge)
   (dest/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');summary['results'][f'{plat}/{case}']={'schema':'accepted','counts':result['counts'],'strict_failures':[{'id':r['id'],'cause':r['cause_category']}for r in result['rows']if r['status']=='failed'],'unassessed_ids':[r['id']for r in result['rows']if r['status']=='unassessed']}
  except Exception as exc:
   err={'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()};(dest/'rejection.json').write_text(json.dumps(err,indent=2)+'\n');summary['results'][f'{plat}/{case}']={'schema':'rejected',**err}
 cat=load(B/'source-evaluation-inputs/d0/T2/initial/catalog.json');judge=load(O/'initial/source-judge.json')
 try:
  assert design_contract.digest(cat)==judge['review']['catalog_sha256']
  # Recompute exact original source catalog using shared gate and frozen lock parser.
  rebuilt=audit.catalog(lock,cat['design_lock_sha256'],load(B/'design/T2/public/implementation-audit.json'),cat['policy_sha256'],B/'submissions/T2/d0/source',B/'design/T2/public')
  assert rebuilt==cat
  result=audit.bind(rebuilt,judge['review']);(O/f'schema-attempt-{attempt}/source-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');summary['results']['source']={'schema':'accepted','counts':result['counts']}
 except Exception as exc:
  err={'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()};(O/f'schema-attempt-{attempt}/source-rejection.json').write_text(json.dumps(err,indent=2)+'\n');summary['results']['source']={'schema':'rejected',**err}
 summary['endedAtUnix']=time.time();(O/f'schema-attempt-{attempt}/summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n');print(json.dumps(summary,ensure_ascii=False))
