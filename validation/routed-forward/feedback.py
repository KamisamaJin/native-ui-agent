#!/usr/bin/env python3
"""Default study feedback endpoint; treatment cannot choose a verification scope."""
import argparse,fcntl,time
from pathlib import Path
import study as s
R=s.R
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--case',action='append');p.add_argument('--state',action='append');a=p.parse_args()
w=a.workspace.resolve();unit=w.name;cfg=s.read(R/'private/assignment.json')['units'][unit]
assert w==R/'cache'/unit;s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify();s.host_verify(w)
initial=s.read(R/'submissions/initial/seal.json')['files'];current=s.fingerprint(w)
assert {k for k in set(initial)|set(current)if initial.get(k)!=current.get(k)}<=set(cfg['allowed_paths'])
protocol=s.read(w/'SESSION.json')
for prior_state in sorted((R/'feedback'/unit).glob('request-*/next-previous.json')):protocol['previous']=s.read(prior_state)['previous']
assert time.time()<=protocol['handoffAtUnix']+1200,'Repair budget closed; in-flight requests may drain'
if cfg['mode']=='default'and(a.case or a.state):raise ValueError('Default feedback never accepts agent-selected cases or states')
registry=R/'feedback'/unit;registry.mkdir(parents=True,exist_ok=True)
with(R/'cache'/('request-'+unit+'.lock')).open('a')as stream:
 fcntl.flock(stream,fcntl.LOCK_EX);existing=sorted(registry.glob('request-*'));assert len(existing)<2,'Two diagnostic requests maximum'
 request=registry/('request-'+str(len(existing)+1));request.mkdir();source=R/'submissions'/unit/('feedback-'+str(len(existing)+1));s.capsule(w,source)
 s.save(request/'request.json',{'startedAtUnix':time.time(),'unit':unit,'cases':a.case,'states':a.state,'scope':'Diagnostic; default chooses scope from source-bound original evidence'})
 raw=R/'cache/acquisitions'/unit/request.name
 history={}
 for old in existing:
  for pl in ['ios','android']:
   for case in [v.name for v in(R/'design/public/cases').iterdir()]:
    cycle=old/'evidence'/pl/case/'cycle.json'
    if cycle.is_file():history.setdefault(pl,{}).setdefault(case,[]).append({'path':str(cycle),'sha256':s.sha(cycle)})
 result=s.collect(w,R/'design/public',raw,cfg['simulator'],states=a.state,cases=a.case,required_stage='d0-raw',source_seal=source/'seal.json',phase='feedback',mode=cfg['mode'],previous=protocol['previous'],history=history,adoptions=protocol['adoptions'])
 s.archive(raw,request/'evidence')
 # Common presentation: both controllers get the same original-actual template.
 # Only the treatment controller automatically consumes registered actuals.
 import evidence_review,native_checks
 for pl in ['ios','android']:
  for case in [v.name for v in(R/'design/public/cases').iterdir()]:
   cap=raw/pl/case/'capture/result.json'
   if not cap.is_file()or not(cap.parent/'automatic.json').is_file():continue
   config=s.configuration(w,R/'design/public',case,pl,cfg['simulator']);config['adoption']=protocol['adoptions'][pl][case]
   work=evidence_review.requests(config,cap,s.sha(cap),s.read(cap.parent/'automatic.json'))
   if work:
    target=request/'review-tasks'/pl/case;s.save(target/'request.json',dict(work,capture_result=str(cap)))
    observation=s.read(cap.parent/'native/observation.json');plan=s.read(config['plan'])
    s.save(target/'state-image-index.json',{state['id']:{'indices':[i for i,_ in native_checks.bound_state_evidence(observation,state)[0]],'complete':native_checks.bound_state_evidence(observation,state)[1]}for state in plan['states']})
 latest={pl:dict(values)for pl,values in protocol['previous'].items()}
 for pl in ['ios','android']:
  for case in [v.name for v in(R/'design/public/cases').iterdir()]:
   receipt=raw/pl/case/'capture/result.json'
   if receipt.is_file()and s.read(receipt).get('observation_sha256'):latest.setdefault(pl,{})[case]={'path':str(receipt),'sha256':s.sha(receipt)}
 s.save(request/'next-previous.json',{'previous':latest,'updatedAtUnix':time.time(),'scope':'Integration-owned latest original capture pointers; original SESSION is immutable.'})
 s.save(request/'completed.json',{'finishedAtUnix':time.time(),'corpus':'evidence/corpus.json'})
print(request/'evidence')
