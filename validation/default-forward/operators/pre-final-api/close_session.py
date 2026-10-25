#!/usr/bin/env python3
"""Operator-enforced source barrier and full-public final for either arm."""
import argparse,time
from pathlib import Path
import study as s
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();w=a.workspace.resolve();unit=w.name
R=s.R;cfg=s.read(R/'private/assignment.json')['units'][unit];assert w==R/'cache'/unit
s.gate.authorize(R/'gates','d0-raw',R);s.host_verify(w);s.tool_verify()
initial=s.read(R/'submissions/initial/seal.json')['files'];current=s.fingerprint(w)
changed={k for k in set(initial)|set(current)if initial.get(k)!=current.get(k)};assert changed<=set(cfg['allowed_paths'])
assert(w/'agent-output/repair.json').is_file()and(w/'agent-output/claims.json').is_file()
source=R/'submissions'/unit/'final';s.capsule(w,source);s.shutil.copytree(w/'agent-output',R/'submissions'/unit/'agent-output')
protocol=s.read(w/'SESSION.json');s.save(R/'submissions'/unit/'repair-closed.json',{'closedAtUnix':time.time(),'changed_files':sorted(changed),'handoffAtUnix':protocol['handoffAtUnix'],'sourceSealSHA256':s.sha(source/'seal.json')})
raw=R/'cache/acquisitions'/unit/'final'
result=s.collect(w,R/'design/public',raw,cfg['simulator'],required_stage='d0-raw',source_seal=source/'seal.json',phase='final-public',mode=cfg['mode'],previous=protocol['previous'],final=True,adoptions=protocol['adoptions'])
s.archive(raw,R/'corpora'/unit/'final-public')
s.save(R/'endpoints'/(unit+'.json'),{'finishedAtUnix':result['finishedAtUnix'],'handoffAtUnix':protocol['handoffAtUnix'],'sourceSealSHA256':s.sha(source/'seal.json'),'status':'public_capture_endpoint_only; independent quality/hidden gates still required'})
print('Closed source and public verification endpoint for '+unit)
