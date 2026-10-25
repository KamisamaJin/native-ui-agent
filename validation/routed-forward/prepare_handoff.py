#!/usr/bin/env python3
"""Identical D0 handoff plus unconditional treatment intake before agent work."""
import argparse,time
from pathlib import Path
import study as s
R=s.R
p=argparse.ArgumentParser();p.add_argument('--unit',required=True);p.add_argument('--phase',choices=['prepare','activate'],required=True);a=p.parse_args();cfg=s.read(R/'private/assignment.json')['units'][a.unit];w=R/'cache'/a.unit
s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify();s.host_verify(w);assert s.fingerprint(w)==s.read(R/'submissions/initial/seal.json')['files']
previous={};adoptions={};cases=sorted((R/'design/public/cases').iterdir())
for pl in (['ios','android']if a.phase=='prepare'else[]):
 for case in cases:
  receipt=R/s.read(R/'operators/active-D0.json')['path']/pl/case.name/'result.json';ticket=R/'handoff'/a.unit/pl/case.name/'adoption.json';ticket.parent.mkdir(parents=True,exist_ok=True)
  s.feedback.adopt_capture(receipt,s.sha(receipt),[w/rel for rel in s.ROOTS],ticket)
  previous.setdefault(pl,{})[case.name]={'path':str(receipt),'sha256':s.sha(receipt)}
  adoptions.setdefault(pl,{})[case.name]={'path':str(ticket),'sha256':s.sha(ticket)}
if a.phase=='prepare':
 s.save(w/'ADOPTIONS.json',{'previous':previous,'adoptions':adoptions});print(w);raise SystemExit()
prepared=s.read(w/'ADOPTIONS.json');previous=prepared['previous'];adoptions=prepared['adoptions']
start=time.time();s.save(w/'SESSION.json',{'handoffAtUnix':start,'previous':previous,'adoptions':adoptions,'publicScope':str(R/'design/public'),'scope':'Only public D0; no hidden or other-arm access. Two diagnostic requests and 20-minute repair budget.'})
if cfg['mode']in {'default','baseline'}:
 for pl in ['ios','android']:
  for case in cases:
   config=s.configuration(w,R/'design/public',case.name,pl,cfg['simulator']);config['adoption']=adoptions[pl][case.name]
   prior=previous[pl][case.name]
   (s.feedback if cfg['mode']=='default'else s.legacy).run_cycle(config,R/'handoff'/a.unit/pl/case.name/'intake',previous=prior['path'],previous_sha=prior['sha256'],intake=True)
s.save(R/'handoff'/a.unit/'ready.json',{'handoffAtUnix':start,'readyAtUnix':time.time(),'sourceSealSHA256':s.sha(R/'submissions'/a.unit/'initial/seal.json')})
print(w)
