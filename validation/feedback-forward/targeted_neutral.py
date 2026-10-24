#!/usr/bin/env python3
"""A real fresh scoped run through the unified wrapper; never a full acceptance."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;N=R/'neutral';T=R/'development/candidate-attempt-3';sys.path.insert(0,str(T/'scripts'))
import design_contract as d,execution_plan as xp

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(v,indent=2)+'\n')
def main():
 assert(R/'operators/benchmark-logs/narrow280-large-r2-legacy.result.json').is_file(),'Complete the paired benchmark first'
 for rel,h in d.load(N/'SEAL.json')['source_and_test_inputs_sha256'].items():assert sha(N/rel)==h
 for rel,h in d.load(R/'operators/candidate-attempt-3.json')['files'].items():assert sha(T/rel)==h
 plan=d.load(N/'generated/ordinary400/design/plan.json');lock=d.load(N/'design/lock.json');fixtures=d.load(N/'inputs/ordinary400.json');bridge=N/'source/Bridge.swift'
 value=xp.compile_execution(plan,lock,d.digest(lock),fixtures,sha(bridge),launch_ref={'source':'launch','pointer':'/ordinary400'},states=['replaced'])
 fixed=next(v for v in d.load(N/'oracle.json')['cases']if v['case']=='ordinary400')['required_environment'];env={k:fixed[k]for k in ['theme','dynamic_type','direction']};env.update(width=fixed['offered_width_pt'],height=fixed['viewport_height_pt'])
 out=R/'cache/neutral-targeted';save(R/'operators/targeted-neutral-request.json',{'fixedAtUnix':time.time(),'execution':value,'environment':env,'environment_sha256':d.digest(env),'neutral_seal_sha256':sha(N/'SEAL.json'),'tool_snapshot_sha256':sha(R/'operators/candidate-attempt-3.json')})
 result=xp.run_execution(value,plan,lock,d.digest(lock),fixtures,bridge,out,[bridge],{'simulator':'CA7BB2E0-0C2B-49C1-B368-5D0DC816F4D2','developer-dir':'/Applications/Xcode.app/Contents/Developer','build-cache':R/'cache/benchmark-build'},expected_environment=env,environment_sha=d.digest(env))
 subprocess.run([sys.executable,'-B',str(R.parents[1]/'validation/dispatch-forward/helpers/portable.py'),str(out),str(R/'neutral-targeted')],check=True)
 print(json.dumps(result));assert result['status']=='verified_capture'
if __name__=='__main__':main()
