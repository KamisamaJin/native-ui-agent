#!/usr/bin/env python3
"""Equal fresh full final review service; checks original actuals, never edits code."""
import argparse,time
from pathlib import Path
import study as s
import design_contract as d,review_contract,native_checks,requirement_routes,acceptance
R=s.R
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();w=a.workspace.resolve();unit=w.name
cfg=s.read(R/'private/assignment.json')['units'][unit];assert w==R/'cache'/unit
s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify();s.host_verify(w)
source=R/'submissions'/unit/'final';assert s.fingerprint(w)==s.read(source/'seal.json')['files'],'Source changed after final close'
assert (R/'endpoints'/(unit+'.json')).is_file(),'Full public automatic endpoint required'
scope=R/'design'/cfg['task']/'public';s.verify_dir(scope);approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'policy.json');routes=s.read(scope/'routes.json');rows=[];began=time.time()
for case in ['P1','P2']:
 for pl in ['ios','android']:
  raw=R/'corpora'/unit/'final-public'/pl/case;op=raw/'native/observation.json';plan=s.read(scope/'compiled'/case/pl/'plan.json')
  if not op.is_file():
   row={'platform':pl,'case':case,'status':'not_accepted','counts':{'passed':0,'failed':0,'unassessed':len(plan['assertions'])},'blockers':['native_observation_missing'],'scope':'No fabricated observation; original wrapper/native failure retained.'}
   s.save(R/'self-final'/unit/pl/case/'missing-native.json',row);rows.append(row);continue
  observation=s.read(op);obs_sha=s.sha(op)
  capture=s.read(raw/'result.json')if(raw/'result.json').is_file()else None
  if capture is not None:s.xp.verify_capture_images(capture,op.parent)
  submission_path=w/'agent-output/final-self'/pl/case/'submission.json';submission=s.read(submission_path)
  manual=review_contract.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],observation,obs_sha,op.parent,submission,pl)
  report=native_checks.evaluate(plan,observation,pl,manual,op.parent,obs_sha,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'])
  env=acceptance.environment(observation,s.read(scope/'cases'/case/('environment.'+pl+'.json')),pl)
  coverage=requirement_routes.audit(lock,approval['design_lock_sha256'],plan,routes,approval['routes_sha256'])
  gate=requirement_routes.admission(coverage,plan,report,execution_scope=capture['scope']if capture else'full',capture=capture,environment=env)
  out=R/'self-final'/unit/pl/case
  for name,value in [('manual.json',manual),('report.json',report),('gate.json',gate)]:s.save(out/name,value)
  s.shutil.copy2(submission_path,out/'submission.json');rows.append({'platform':pl,'case':case,'status':gate['status'],'counts':report['counts'],'blockers':gate['blocking_obligations']})
assert s.fingerprint(w)==s.read(source/'seal.json')['files']
s.shutil.copytree(w/'agent-output/final-self',R/'self-final'/unit/'original')
s.save(R/'self-final'/unit/'endpoint.json',{'startedServiceAtUnix':began,'finishedAtUnix':time.time(),'handoffAtUnix':s.read(w/'SESSION.json')['handoffAtUnix'],'accepted':all(v['status']=='accepted'for v in rows),'cases':rows,'sourceSealSHA256':s.sha(source/'seal.json'),'scope':'Source-bound full AI self-verification, not independent quality gold. No source/expected edits.'})
s.seal_dir(R/'self-final'/unit)
print(str(R/'self-final'/unit/'endpoint.json'))
