from pathlib import Path
import subprocess,sys,os,json,hashlib
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');ROOT=BASE/'business-design-v2';OUT=BASE/'business-design-review/v2';TOOL=BASE/'candidate-v13.9/scripts'
def load(p):return json.loads(p.read_text())
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');runs=[];matches=[]
def run(group,name,argv,expected=0):
 target=OUT/group;target.mkdir(parents=True,exist_ok=True)
 p=subprocess.run([sys.executable,'-B']+argv,cwd=str(BASE.parent.parent),env=env,text=True,capture_output=True)
 (target/(name+'.stdout.txt')).write_text(p.stdout);(target/(name+'.stderr.txt')).write_text(p.stderr)
 runs.append({'group':group,'stage':name,'argv':[sys.executable,'-B']+argv,'expected_exit_zero':expected==0,'exit_code':p.returncode,'success':p.returncode==0 if expected==0 else p.returncode!=0,'stdout':p.stdout,'stderr':p.stderr})
 return p.returncode==0
for t in range(1,6):
 for phase in ['public','private']:
  family=ROOT/f'T{t}'/phase;approval=load(family/'PROFILE-APPROVAL.json');ash=digest(approval)
  for platform in ['ios','android']:
   src=family/platform;group=f'T{t}/{phase}/{platform}';dst=OUT/group;dst.mkdir(parents=True,exist_ok=True);s=load(src/'seal.json');locksha=s['design_sha256'];scenario=load(src/'generated/plan.json')['design_contract']['scenario'];bridge=src/('ObserverBridge.swift'if platform=='ios'else'ObserverBridge.kt')
   run(group,'seal',[str(TOOL/'design_contract.py'),'seal','--contract',str(src/'contract.json'),'--root',str(src),'--output',str(dst/'resealed-lock.json')])
   ok=run(group,'compile',[str(TOOL/'design_contract.py'),'compile','--lock',str(src/'lock.json'),'--lock-sha256',locksha,'--scenario',scenario,'--platform',platform,'--bindings',str(src/'bindings.json'),'--actions',str(src/'actions.json'),'--output',str(dst/'generated')])
   if ok:
    plan=dst/'generated/plan.json'
    run(group,'catalog',[str(TOOL/'review_contract.py'),'catalog','--plan',str(plan),'--design-lock',str(src/'lock.json'),'--design-sha256',locksha,'--policy',str(src/'policy.json'),'--policy-sha256',s['policy_sha256'],'--platform',platform,'--output',str(dst/'catalog.json')])
    run(group,'route-audit',[str(TOOL/'requirement_routes.py'),'audit','--plan',str(plan),'--design-lock',str(src/'lock.json'),'--design-sha256',locksha,'--routes',str(src/'routes.json'),'--routes-sha256',s['routes_sha256'],'--output',str(dst/'route-audit.json')])
    run(group,'execution',[str(TOOL/'execution_plan.py'),'--plan',str(plan),'--design-lock',str(src/'lock.json'),'--design-sha256',locksha,'--fixtures',str(src/'fixtures.json'),'--bridge',str(bridge),'--launch-source','launch','--launch-pointer','/'+platform,'--output',str(dst/'execution')])
   run(group,'admission',[str(family/'admit_profile.py'),'--root',str(family),'--approval',str(family/'PROFILE-APPROVAL.json'),'--approval-sha256',ash,'--platform',platform,'--config',str(src/'admission-config.json')])
   run(group,'wrong-platform-rejection',[str(family/'admit_profile.py'),'--root',str(family),'--approval',str(family/'PROFILE-APPROVAL.json'),'--approval-sha256',ash,'--platform','android'if platform=='ios'else'ios','--config',str(src/'admission-config.json')],expected=1)
   for name,destination in [('lock.json','resealed-lock.json'),('generated/plan.json','generated/plan.json'),('generated/actions.json','generated/actions.json'),('catalog.json','catalog.json'),('route-audit.json','route-audit.json'),('execution/execution.json','execution/execution.json'),('execution/actions.json','execution/actions.json'),('execution/fixtures.json','execution/fixtures.json')]:
    a,b=src/name,dst/destination;matches.append({'group':group,'artifact':name,'exists':b.exists(),'canonical_equal':b.exists()and load(a)==load(b),'author_sha256':digest(load(a)),'reviewer_sha256':digest(load(b))if b.exists()else None})
dump(OUT/'pure-run-log.json',runs);dump(OUT/'rebuild-comparison.json',matches)
print(json.dumps({'positive_runs':sum(r['expected_exit_zero']for r in runs),'positive_passes':sum(r['success']and r['expected_exit_zero']for r in runs),'expected_negative_runs':sum(not r['expected_exit_zero']for r in runs),'expected_negative_passes':sum(r['success']and not r['expected_exit_zero']for r in runs),'rebuilt_artifacts':len(matches),'matching_artifacts':sum(r['canonical_equal']for r in matches),'unexpected_failures':[{'group':r['group'],'stage':r['stage'],'stderr':r['stderr']}for r in runs if not r['success']]},indent=2))
