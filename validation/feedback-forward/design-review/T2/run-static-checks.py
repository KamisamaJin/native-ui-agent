import hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
SCOPE=os.environ.get('REVIEW_SCOPE','public')
DESIGN = ROOT/'validation/feedback-forward/design/T2'/SCOPE
FROZEN = ROOT/'validation/feedback-forward/candidate-v9'
OUT = Path(__file__).resolve().parent
if SCOPE!='public':
    OUT=OUT/(SCOPE+'-checks');OUT.mkdir(exist_ok=True)
CASES=list(json.loads((DESIGN/'contract.json').read_text())['scenarios'])
PY = sys.executable
approval = json.loads((DESIGN/'approval.json').read_text())
rows=[]

def run(name,args):
    start=time.time()
    p=subprocess.run(args,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/(name+'.log')).write_text(p.stdout)
    row={'name':name,'argv':list(map(str,args)),'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':p.returncode,'log':name+'.log','sdk_invoked':False}
    rows.append(row)
    (OUT/'command-log.json').write_text(json.dumps(rows,indent=2)+'\n')
    if p.returncode: raise RuntimeError(name+' failed; retained original log')

def cli(script,*args): return [PY,'-B',str(FROZEN/'scripts'/script),*map(str,args)]

run('seal',cli('design_contract.py','seal','--contract',DESIGN/'contract.json','--root',DESIGN,'--output',OUT/'rebuilt-lock.json'))
for case in CASES:
    for platform,bridge in [('ios','Bridge.swift'),('android','ObserverBridge.kt')]:
        name=case+'-'+platform
        target=OUT/'rebuilt'/case/platform
        shared=['--design-lock',DESIGN/'design-lock.json','--design-sha256',approval['design_lock_sha256']]
        run(name+'-compile',cli('design_contract.py','compile','--lock',DESIGN/'design-lock.json','--lock-sha256',approval['design_lock_sha256'],'--scenario',case,'--platform',platform,'--bindings',DESIGN/'bindings.json','--actions',DESIGN/'cases'/case/('actions.'+platform+'.json'),'--output',target))
        run(name+'-catalog',cli('review_contract.py','catalog','--plan',target/'plan.json',*shared,'--policy',DESIGN/'policy.json','--policy-sha256',approval['policy_sha256'],'--platform',platform,'--output',target/'review-catalog.json'))
        run(name+'-routes',cli('requirement_routes.py','audit','--plan',target/'plan.json',*shared,'--routes',DESIGN/'routes.json','--routes-sha256',approval['routes_sha256'],'--output',target/'coverage.json'))
        run(name+'-execution',cli('execution_plan.py','--plan',target/'plan.json',*shared,'--fixtures',DESIGN/'cases'/case/'fixtures.json','--bridge',DESIGN/bridge,'--launch-source','reference','--launch-pointer','/launch/'+case+'/'+platform,'--output',target/'execution-inputs'))

# The shared tool is imported only after preloading the frozen design-contract
# module. Its default repository search path therefore cannot load a sibling tool.
code="import sys,runpy;sys.path.insert(0,sys.argv.pop(1));import design_contract;assert design_contract.__file__.startswith(sys.path[0]);runpy.run_path(sys.argv.pop(1),run_name='__main__')"
run('source-definitions',[PY,'-B','-c',code,str(FROZEN/'scripts'),str(ROOT/'tools/implementation_audit.py'),'definitions','--design-lock',str(DESIGN/'design-lock.json'),'--design-sha256',approval['design_lock_sha256'],'--policy',str(DESIGN/'implementation-audit.json'),'--policy-sha256',approval['implementation_audit_sha256'],'--source-root',str(OUT/'nonexistent-production'),'--design-root',str(DESIGN),'--output',str(OUT/'source-audit-definitions.json')])

sys.path.insert(0,str(FROZEN/'scripts'))
import design_contract as d, execution_plan as e
assert Path(d.__file__).resolve().is_relative_to(FROZEN.resolve())
lock=d.load(DESIGN/'design-lock.json')
summary={'rebuilt_lock_matches':d.load(OUT/'rebuilt-lock.json')==lock,'mechanical':[]}
for case in CASES:
 for platform,bridge in [('ios','Bridge.swift'),('android','ObserverBridge.kt')]:
    target=OUT/'rebuilt'/case/platform
    plan=d.load(target/'plan.json');x=d.load(target/'execution-inputs/execution.json');fixtures=d.load(DESIGN/'cases'/case/'fixtures.json')
    start=time.time();verified=e.verify_execution(x,plan,lock,approval['design_lock_sha256'],fixtures,hashlib.sha256((DESIGN/bridge).read_bytes()).hexdigest());finish=time.time()
    cat=d.load(target/'review-catalog.json');coverage=d.load(target/'coverage.json')
    summary['mechanical'].append({'case':case,'platform':platform,'required_assertions':len(plan['assertions']),'states':len(plan['states']),'manual_atoms':len(cat.get('rows',cat.get('items',[]))),'must_route_gaps':coverage['must_route_gaps'],'unowned_assertions':coverage['unowned_assertions'],'execution_reconstruction_equal':verified==x,'verificationStartedAtUnix':start,'verificationFinishedAtUnix':finish,'actions':len(x['actions']),'production_not_accessed':True})
summary['source_audit_definitions']=len(d.load(OUT/'source-audit-definitions.json')['rows'])
(OUT/'static-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
