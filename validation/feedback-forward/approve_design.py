#!/usr/bin/env python3
"""SDK-free exact-source design feasibility checks before initial implementation."""
import argparse
from pathlib import Path
import study as s
import design_contract as d,execution_plan as xp,requirement_routes as rr,review_contract
R=s.R

def verify(scope):
 s.verify_dir(scope);approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'policy.json');routes=s.read(scope/'routes.json')
 for key,value in [('design_lock_sha256',lock),('policy_sha256',policy),('routes_sha256',routes)]:assert d.digest(value)==approval[key],(scope,key)
 rows=[]
 for folder in sorted((scope/'cases').iterdir()):
  case=folder.name;fixtures=s.read(folder/'fixtures.json')
  for pl in ['ios','android']:
   compiled=scope/'compiled'/case/pl;plan=s.read(compiled/'plan.json');actions=d.verify_generated(plan,lock,approval['design_lock_sha256'],pl)
   assert d.canonical(actions)==d.canonical(s.read(compiled/'actions.json'))
   coverage=rr.audit(lock,approval['design_lock_sha256'],plan,routes,approval['routes_sha256']);assert not coverage['must_route_gaps'],coverage
   assert not coverage['unowned_assertions'],coverage
   review_contract.catalog(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],pl)
   bridge=scope/('Bridge.swift'if pl=='ios'else'ObserverBridge.kt')
   value=xp.compile_execution(plan,lock,approval['design_lock_sha256'],fixtures,s.sha(bridge),launch_ref={'source':'reference','pointer':'/launch/'+case+'/'+pl})
   assert value==s.read(compiled/'execution.json')
   env=s.read(folder/('environment.'+pl+'.json'));assert d.digest(env)==approval['environment_sha256'][case][pl]
   __import__('acceptance').environment({},env,pl)
   assert len(plan['states'])==4
   assert max(v['input_index']for v in plan['states'])<1+len(fixtures.get('updates',[]))
   rows.append({'case':case,'platform':pl,'assertions':len(plan['assertions']),'obligations':len(coverage['obligations']),'must_gaps':coverage['must_route_gaps']})
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('scope',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();s.save(a.output,{'checks':verify(a.scope),'scope':'Mechanical identity/coverage/launch/atomic/environment checks, not independent semantic approval.'})
