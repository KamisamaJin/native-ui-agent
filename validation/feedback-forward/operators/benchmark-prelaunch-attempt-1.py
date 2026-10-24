#!/usr/bin/env python3
"""Prospective neutral same-source/coverage paired native experiment."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;N=R/'neutral';T=R/'development/candidate-attempt-1';sys.path.insert(0,str(T/'scripts'))
import design_contract as d,execution_plan as xp,native_checks,acceptance
DEV='/Applications/Xcode.app/Contents/Developer';SIM='CA7BB2E0-0C2B-49C1-B368-5D0DC816F4D2'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(v,indent=2)+'\n')
def verify():
 for rel,h in read(N/'SEAL.json')['files'].items():assert sha(N/rel)==h,rel
 for tool,freeze in [(T,R/'operators/candidate-attempt-1.json'),(R/'baseline-v8',R/'baseline-v8-freeze.json')]:
  for rel,h in read(freeze)['files'].items():assert sha(tool/rel)==h,rel
 lock=read(N/'design/lock.json');assert d.digest(lock)==read(N/'APPROVAL.json')['design_lock_sha256']
 return lock

def main():
 lock=verify();lock_sha=d.digest(lock);bridge=N/'source/Bridge.swift';requests=[]
 for case in ['ordinary400','narrow280-large']:
  for repetition,order in [(1,['legacy','coalesced']),(2,['coalesced','legacy'])]:
   for strategy in order:
    value=read(N/'generated'/case/strategy/'execution.json');plan=read(N/'generated'/case/'design/plan.json');fixtures=read(N/'inputs'/(case+'.json'))
    xp.verify_execution(value,plan,lock,lock_sha,fixtures,sha(bridge))
    tool=R/'baseline-v8'if strategy=='legacy'else T
    name=case+'-r'+str(repetition)+'-'+strategy
    raw=R/'cache/benchmark'/name;portable=R/'neutral-captures'/name
    cmd=[sys.executable,'-B',str(tool/'scripts/ios_observe.py'),'run','--bridge',str(bridge),'--fixtures',str(N/'generated'/case/strategy/'fixtures.json'),'--actions',str(N/'generated'/case/strategy/'actions.json'),'--output',str(raw),'--simulator',SIM,'--developer-dir',DEV,'--build-cache',str(R/'cache/benchmark-build')]
    requests.append({'name':name,'case':case,'repetition':repetition,'strategy':strategy,'argv':cmd,'execution_sha256':value['execution_sha256'],'parent_plan_sha256':d.digest(plan),'bridge_sha256':sha(bridge),'required_coverage':value['required_coverage']})
 save(R/'operators/benchmark-requests.json',{'fixedAtUnix':time.time(),'neutralSealSHA256':sha(N/'SEAL.json'),'runnerSHA256':sha(Path(__file__)),'requests':requests})
 for request in requests:
  verify();cmd=request['argv'];out=R/'operators/benchmark-logs'/request['name'];started=time.time();save(out.with_suffix('.start.json'),dict(request,startedAtUnix=started))
  out.parent.mkdir(parents=True,exist_ok=True)
  with out.with_suffix('.log').open('x')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR=DEV,PYTHONDONTWRITEBYTECODE='1')).returncode
  raw=Path(cmd[cmd.index('--output')+1]);case=request['case'];value=read(N/'generated'/case/request['strategy']/'execution.json');plan=read(N/'generated'/case/'design/plan.json')
  result=dict(request,startedAtUnix=started,finishedAtUnix=time.time(),exitCode=code)
  if(raw/'observation.json').is_file():
   observation=read(raw/'observation.json');report=native_checks.evaluate(plan,observation,'ios',root=raw,observation_sha=sha(raw/'observation.json'),design_lock=lock,design_sha=lock_sha)
   # Keep native facts and unknowns; this neutral timing pass supplies no visual votes.
   save(raw/'automatic.json',report);save(raw/'required-coverage.json',xp.coverage_receipt(value,observation))
   result['counts']=report['counts'];result['coverage']=read(raw/'required-coverage.json');result['operations']=observation.get('operations')
  result['wallSeconds']=result['finishedAtUnix']-started
  save(out.with_suffix('.result.json'),result)
  subprocess.run([sys.executable,'-B',str(R.parents[1]/'validation/dispatch-forward/helpers/portable.py'),str(raw),str(R/'neutral-captures'/request['name'])],check=True)
  print(json.dumps({k:result.get(k)for k in ['name','exitCode','wallSeconds','counts']}),flush=True)
if __name__=='__main__':main()
