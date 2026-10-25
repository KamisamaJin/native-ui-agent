#!/usr/bin/env python3
"""Replay independent original actuals, without rewriting judgments or raw F/U."""
import argparse,time
from pathlib import Path
import study as s
import design_contract as d,review_contract as review,native_checks,requirement_routes as rr,acceptance
from source_self import audit
R=s.R
p=argparse.ArgumentParser();p.add_argument('panel',choices=['panel-one','panel-two']);a=p.parse_args();panel=R/'quality-panels'/a.panel
s.gate.authorize(R/'gates','quality-inputs',R);s.verify_dir(panel)
out=R/'quality-evaluation'/a.panel;out.mkdir(parents=True,exist_ok=False);source_rows={};runtime=[];alarms=[]
for phase in ['public','private']:
 for folder in sorted((R/'quality-inputs/source-review'/phase).iterdir()):
  if not folder.is_dir():continue
  cat=s.read(folder/'catalog.json');submission=panel/'source'/phase/folder.name/'submission.json'
  bound=audit.bind(cat,s.read(submission));s.save(out/'source'/phase/(folder.name+'.json'),bound);source_rows[phase+':'+folder.name]=bound['counts']
for candidate in sorted(p for p in(R/'quality-inputs').iterdir()if p.name.startswith('candidate-')):
 for phase in ['public','private']:
  scope=R/'design'/phase;approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'policy.json')
  for pl in ['ios','android']:
   for case in sorted((scope/'cases').iterdir()):
    base=candidate/'native'/phase/pl/case.name;op=base/'native/observation.json';plan=s.read(base/'parent-plan.json');observation=s.read(op)
    submission=panel/'visual'/candidate.name/phase/pl/case.name/'submission.json'
    manual=review.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],observation,s.sha(op),op.parent,s.read(submission),pl)
    evaluated=native_checks.evaluate(plan,observation,pl,manual,op.parent,s.sha(op),lock,approval['design_lock_sha256'],policy,approval['policy_sha256'])
    coverage=rr.audit(lock,approval['design_lock_sha256'],plan,s.read(scope/'routes.json'),approval['routes_sha256'])
    admitted=rr.admission(coverage,plan,evaluated,environment=acceptance.environment(observation,s.read(case/('environment.'+pl+'.json')),pl))
    dest=out/'runtime'/candidate.name/phase/pl/case.name;s.save(dest/'manual.json',manual);s.save(dest/'evaluated.json',evaluated);s.save(dest/'obligations.json',admitted['obligations'])
    runtime.append({'candidate':candidate.name,'scope':phase,'platform':pl,'case':case.name,'counts':evaluated['counts']})
    alarms.extend((candidate.name,phase,pl,case.name,row['id'])for row in s.read(base/'automatic.json')['assertions']if row['status']=='failed')
judgments=s.read(panel/'alarm-judgments.json');keys=[(v['candidate'],v['scope'],v['platform'],v['case'],v['assertion_id'])for v in judgments]
assert len(keys)==len(set(keys))and set(keys)==set(alarms),'Every original automatic alarm needs exact independent attribution'
assert all(v['cause']in {'product','false_alarm','uncertain'}and v['reason'].strip()and v['evidence']for v in judgments),'Original evidence and known attribution required'
s.save(out/'summary.json',{'closedAtUnix':time.time(),'source_counts':source_rows,'runtime':runtime,'alarm_count':len(alarms),'original_review_seal_sha256':s.sha(panel/'SEAL.json'),'scope':'Replayed actuals; native F/U retained. Overall acceptance and defect consensus computed separately after both panels close.'})
print(out)
