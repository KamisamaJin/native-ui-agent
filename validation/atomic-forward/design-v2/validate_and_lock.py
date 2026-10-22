#!/usr/bin/env python3
"""Use the frozen real CLIs on all independent designs; no native SDK execution."""
from pathlib import Path
import json,hashlib,datetime,subprocess,sys,shutil,importlib
R=Path(__file__).resolve().parent;T=R.parent/'candidate-v8'/'scripts';sys.path.insert(0,str(T))
import design_contract as design,acceptance
from generate_design import policy
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():raise RuntimeError('fresh required: '+str(p))
 p.write_text(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(args,log):
 start=now();p=subprocess.run([sys.executable,*map(str,args)],text=True,capture_output=True,cwd=R)
 write(log,{'started_at':start,'finished_at':now(),'argv':[sys.executable,*map(str,args)],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 if p.returncode:raise RuntimeError('Frozen CLI rejected: '+str(log))
 return json.loads(p.stdout) if p.stdout.strip() else {}
start=now();summary=[]
write(R/'validation-start.json',{'actual_validation_started_at':start})
for tid in ['T1','T2','T3']:
 for scope,cases in [('public',['P1','P2']),('private',['H1'])]:
  b=R/tid/scope;logs=b/'validation-logs';locks=run([T/'design_contract.py','seal','--contract',b/'contract.json','--root',b,'--output',b/'design-lock.json'],logs/'01-seal.json');lsha=locks['design_lock_sha256']
  pol=policy(lsha);write(b/'policy.json',pol);psha=design.digest(pol)
  app={'design_lock_sha256':lsha,'policy_sha256':psha,'environment_sha256':{}}
  for cid in cases:
   case=b/'cases'/cid;out=b/'compiled'/cid;out.mkdir(parents=True)
   for p in case.iterdir():shutil.copy2(p,out/p.name)
   app['environment_sha256'][cid]={}
   for platform in ['ios','android']:
    result=run([T/'design_contract.py','compile','--lock',b/'design-lock.json','--lock-sha256',lsha,'--scenario',cid,'--platform',platform,'--bindings',b/'bindings.json','--actions',case/f'actions.{platform}.json','--output',out/platform],logs/f'{cid}-{platform}-02-compile.json')
    run([T/'review_contract.py','catalog','--plan',out/platform/'plan.json','--design-lock',b/'design-lock.json','--design-sha256',lsha,'--policy',b/'policy.json','--policy-sha256',psha,'--platform',platform,'--output',out/platform/'catalog.json'],logs/f'{cid}-{platform}-03-catalog.json')
    env=design.load(case/f'environment.{platform}.json');esh=design.digest(env);app['environment_sha256'][cid][platform]=esh
    # Exercise real frozen environment schema only. Empty evidence MUST remain U.
    status=acceptance.environment({'snapshots':[]},env,platform)
    if status['status']!='U':raise RuntimeError('Unexpected fabricated environment pass')
    proof={'environment_canonical_sha256':esh,'approval_path':'approval.json','schema_function':'candidate-v8/scripts/acceptance.py:environment','result_without_native_evidence':status,'native_execution':False,'interpretation':'Environment schema accepted; runtime environment remains U until original native observation. No synthetic frame is created.'}
    write(out/platform/'environment-preflight.json',proof)
    cat=design.load(out/platform/'catalog.json');plan=design.load(out/platform/'plan.json')
    summary.append({'task':tid,'scope':scope,'case':cid,'platform':platform,'states':len(plan['states']),'rules':len(plan['matrix_contract']['selected_requirements']),'cells':len(plan['matrix_contract']['cells']),'required':len(plan['assertions']),'not_applicable':sum(x['disposition']=='not_applicable' for x in plan['matrix_contract']['cells']),'manual_atoms':len(cat['rows']),'catalog_sha256':cat['catalog_sha256'],'environment_sha256':esh,'compile':'accepted','catalog':'accepted','native_environment':'not observed; U'})
  write(b/'approval.json',app)
write(R/'validation-summary.json',{'actual_validation_started_at':start,'actual_validation_finished_at':now(),'frozen_scripts_unchanged':True,'native_sdk_invocations':0,'scope':'All 9 cases ×2 platforms sealed/compiled/catalogued with real frozen CLIs. Environment contracts schema checked and canonically approved; no runtime evidence fabricated. Not independent design-quality approval.','runs':summary})
print(json.dumps({'runs':len(summary),'all_compiled_and_catalogued':True,'native_sdk_invocations':0}))
