import sys
sys.dont_write_bytecode=True
import json,hashlib,traceback,time,importlib.util
from pathlib import Path
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');OUT=ROOT/'judgments/d0/one/T1'
sys.path.insert(0,str(ROOT/'candidate-v9/scripts'))
import acceptance,design_contract,native_checks
load=lambda p:json.loads(p.read_text())
checks=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  p=ROOT/'evaluation-inputs/d0/T1/initial'/platform/case;inp=load(p/'inputs.json');cat=load(p/'catalog.json');plan=load(p/'plan.json');obs=load(ROOT/inp['observation']);judge=load(OUT/'initial'/platform/case/'judge.json');lock=load(ROOT/inp['scope']/'design-lock.json');policy=load(ROOT/inp['scope']/'policy.json');env=load(ROOT/inp['environment'])
  for attempt in [1,2]:
   dest=OUT/'checks'/f'{platform}-{case}-self-check-{attempt}.json';dest.parent.mkdir(parents=True,exist_ok=True)
   start=time.time()
   try:
    result=acceptance.evaluate(plan,lock,cat['design_lock_sha256'],policy,cat['policy_sha256'],obs,inp['observation_sha256'],(ROOT/inp['observation']).parent,platform,env,judge,judge)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');r={'platform':platform,'case':case,'attempt':attempt,'status':'schema_accepted','counts':result['counts'],'failures':[(x['id'],x['authoritative']['reason'])for x in result['rows']if x['status']=='failed'],'unknowns':[(x['id'],x['authoritative']['reason'])for x in result['rows']if x['status']=='unassessed'],'startedAtUnix':start,'endedAtUnix':time.time(),'independent_consensus':False}
   except Exception as ex:
    result={'error':repr(ex),'traceback':traceback.format_exc()};dest.write_text(json.dumps(result,indent=2)+'\n');r={'platform':platform,'case':case,'attempt':attempt,'status':'schema_rejected','error':str(ex),'startedAtUnix':start,'endedAtUnix':time.time(),'independent_consensus':False}
   checks.append(r);print(platform,case,attempt,r.get('counts',r.get('error')),flush=True)
# Exact source hashes, line count and reviewer schema check. Use the frozen design module already loaded.
sourcein=load(ROOT/'source-evaluation-inputs/d0/T1/initial/inputs.json');cat=load(ROOT/'source-evaluation-inputs/d0/T1/initial/catalog.json');judge=load(OUT/'initial/source-judge.json')
sourcepaths={'Sources/AlertToast/ColdStorageTransferPanel.swift':ROOT/'submissions/T1/d0/source/alerttoast/Sources/AlertToast/ColdStorageTransferPanel.swift','app/src/main/java/com/example/reply/ui/components/ColdStorageTransferPanel.kt':ROOT/'submissions/T1/d0/source/reply/Reply/app/src/main/java/com/example/reply/ui/components/ColdStorageTransferPanel.kt','@design/Bridge.swift':ROOT/'design/T1/public/Bridge.swift','@design/ObserverBridge.kt':ROOT/'design/T1/public/ObserverBridge.kt'}
for f,p in sourcepaths.items():
 assert hashlib.sha256(p.read_bytes()).hexdigest()==cat['files'][f]['sha256'];assert len(p.read_text().splitlines())==cat['files'][f]['line_count']
spec=importlib.util.spec_from_file_location('implementation_audit',ROOT.parent.parent/'tools/implementation_audit.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
result=mod.bind(cat,judge['review']);(OUT/'checks/source-bind.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print('source schema',result['counts'],flush=True)
(OUT/'checks/summary.json').write_text(json.dumps({'runtime_self_checks':checks,'source_schema_check':result['counts'],'scope':'Identical assessor input supplied twice is schema checking only. It is not independent consensus or human gold.'},indent=2)+'\n')
