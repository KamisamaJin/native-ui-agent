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
protocol=s.read(w/'SESSION.json');assert time.time()<=protocol['handoffAtUnix']+1200,'Repair budget closed; in-flight requests may drain'
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
 s.archive(raw,request/'evidence');s.save(request/'completed.json',{'finishedAtUnix':time.time(),'corpus':'evidence/corpus.json'})
print(request/'evidence')
