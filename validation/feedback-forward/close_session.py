#!/usr/bin/env python3
"""Seal one arm and immediately run its own full public final checks."""
import argparse,time
from pathlib import Path
import study as s
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();w=a.workspace.resolve();unit=w.name
R=s.R;cfg=s.read(R/'private/assignment.json')['units'][unit];assert w==R/'cache'/unit
s.gate.authorize(R/'gates','d0-raw',R);s.host_verify(w);s.tool_verify()
initial=s.read(R/'submissions'/cfg['task']/'d0/seal.json')['files'];current=s.fingerprint(w)
changed={k for k in set(initial)|set(current)if initial.get(k)!=current.get(k)}
assert changed<=set(cfg['allowed_paths']),'Only approved component source changes allowed'
assert (w/'agent-output/repair.json').is_file()and(w/'agent-output/claims.json').is_file(),'Original findings and repair record must seal before final acquisition'
source=R/'submissions'/unit/'final';s.capsule(w,source)
s.shutil.copytree(w/'agent-output',R/'submissions'/unit/'agent-output')
s.save(R/'submissions'/unit/'repair-closed.json',{'closedAtUnix':time.time(),'changed_files':sorted(changed),'handoff':s.read(w/'SESSION.json'),'sourceSealSHA256':s.sha(source/'seal.json')})
raw=R/'cache/acquisitions'/unit/'final'
result=s.collect(w,R/'design'/cfg['task']/'public',raw,cfg['simulator'],required_stage='d0-raw',source_seal=source/'seal.json',phase='final-public')
s.save(R/'endpoints'/(unit+'.json'),{'finishedAtUnix':result['finishedAtUnix'],'handoffAtUnix':s.read(w/'SESSION.json')['handoffAtUnix'],'sourceSealSHA256':s.sha(source/'seal.json'),'rawCorpusSHA256':s.sha(raw/'corpus.json'),'status':'public_capture_and_automatic_checks_result','notAcceptance':'Qualitative MUST decisions require original evidence and approved review; external panel cost is separate.'})
s.archive(raw,R/'corpora'/unit/'final-public')
print('Closed source and public verification endpoint for '+unit)
