#!/usr/bin/env python3
"""Equal source-sealed diagnostic service for both blind repair conditions."""
import argparse,fcntl,time
from pathlib import Path
import study as s
R=s.R
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--case',action='append',choices=['P1','P2']);p.add_argument('--state',action='append');a=p.parse_args()
w=a.workspace.resolve();unit=w.name;assignment=s.read(R/'private/assignment.json');cfg=assignment['units'][unit]
assert w==R/'cache'/unit
s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify();s.host_verify(w)
initial=s.read(R/'submissions'/cfg['task']/'d0/seal.json')['files'];current=s.fingerprint(w)
assert {k for k in set(initial)|set(current)if initial.get(k)!=current.get(k)}<=set(cfg['allowed_paths']),'Only approved component edits are allowed before SDK launch'
protocol=s.read(w/'SESSION.json');assert time.time()<=protocol['handoffAtUnix']+1200,'Repair budget closed; in-flight requests may drain'
registry=R/'feedback'/unit;registry.mkdir(parents=True,exist_ok=True)
with (R/'cache'/('request-'+unit+'.lock')).open('a')as stream:
 fcntl.flock(stream,fcntl.LOCK_EX)
 existing=sorted(registry.glob('request-*'));assert len(existing)<2,'Two-request diagnostic budget exhausted'
 request=registry/('request-'+str(len(existing)+1));request.mkdir()
 source=R/'submissions'/unit/('feedback-'+str(len(existing)+1));s.capsule(w,source)
 s.save(request/'request.json',{'startedAtUnix':time.time(),'unit':unit,'cases':a.case or ['P1','P2'],'states':a.state,'sourceSealSHA256':s.sha(source/'seal.json'),'scope':'Diagnostic, full fresh final remains mandatory'})
 raw=R/'cache/acquisitions'/unit/request.name
 result=s.collect(w,R/'design'/cfg['task']/'public',raw,cfg['simulator'],states=a.state,cases=a.case,required_stage='d0-raw',source_seal=source/'seal.json',phase='feedback')
 s.archive(raw,request/'evidence')
 s.save(request/'completed.json',{'finishedAtUnix':time.time(),'producerFinishedAtUnix':result['finishedAtUnix'],'withinBudgetAtFinish':time.time()<=protocol['handoffAtUnix']+1200,'corpus':'evidence/corpus.json'})
print(str(request/'evidence'))
