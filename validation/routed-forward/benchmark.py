#!/usr/bin/env python3
"""Actual same-code/same-coverage neutral native benchmark; all attempts retained."""
import argparse,hashlib,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
sys.path.insert(0,str(REPO/'native-ui-agent/scripts'))
import design_contract as d,execution_plan as xp,feedback_loop as feedback,evidence_review

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(v,indent=2)+'\n')
def config():
 b=R/'benchmark-design';sim=read(R/'operators/owned-devices.json')['devices']['neutral']
 return dict(plan=str(b/'plan.ios.json'),design_lock=str(b/'lock.json'),design_sha256=d.digest(read(b/'lock.json')),policy=str(b/'policy.json'),policy_sha256=d.digest(read(b/'policy.json')),routes=str(b/'routes.json'),routes_sha256=d.digest(read(b/'routes.json')),fixtures=str(b/'fixtures.json'),bridge=str(b/'FoldGuideBridge.swift'),source_roots=[str(b/'FoldGuideBridge.swift')],launch_ref={'source':'reference','pointer':'/launch'},environment=str(b/'environment.ios.json'),environment_sha256=d.digest(read(b/'environment.ios.json')),review_store=str(R/'cache/benchmark-reviews'),native_options={'simulator':sim,'developer-dir':'/Applications/Xcode.app/Contents/Developer','build-cache':str(R/'cache/benchmark-build')})
def main():
 p=argparse.ArgumentParser();p.add_argument('step',choices=['d0','cycle']);p.add_argument('--name',default='d0');p.add_argument('--baseline',action='store_true');p.add_argument('--final',action='store_true');p.add_argument('--origin',default='d0');a=p.parse_args();c=config();out=R/'cache/benchmark'/a.name
 if a.step=='d0':
  plan=read(c['plan']);lock=read(c['design_lock']);fixtures=read(c['fixtures'])
  value=xp.compile_execution(plan,lock,c['design_sha256'],fixtures,sha(c['bridge']),launch_ref=c['launch_ref'])
  result=xp.run_execution(value,plan,lock,c['design_sha256'],fixtures,Path(c['bridge']),out,c['source_roots'],c['native_options'],policy=read(c['policy']),policy_sha=c['policy_sha256'],expected_environment=read(c['environment']),environment_sha=c['environment_sha256'])
 else:
  if a.baseline:
   import importlib.util
   spec=importlib.util.spec_from_file_location('baseline_controller',R/'baseline-v10/scripts/feedback_loop.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  else:module=feedback
  result=module.run_cycle(c,out,previous=R/'cache/benchmark'/a.origin/'result.json',previous_sha=sha(R/'cache/benchmark'/a.origin/'result.json'),final=a.final)
 save(R/'operators/benchmark'/(a.name+'.json'),result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
