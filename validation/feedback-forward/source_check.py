#!/usr/bin/env python3
"""Shared source-only actual catalog/review service, separate from runtime facts."""
import argparse,time,sys
from pathlib import Path
import study as s
sys.path.insert(0,str(s.REPO/'tools'))
import implementation_audit as audit
import design_contract as d
R=s.R
import shared_amendment
shared_amendment.verify()
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--phase',choices=['original','final'],required=True);p.add_argument('--prepare',action='store_true');p.add_argument('--submission',type=Path);a=p.parse_args();w=a.workspace.resolve();unit=w.name;cfg=s.read(R/'private/assignment.json')['units'][unit]
assert w==R/'cache'/unit;s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify()
expected=s.read(R/'submissions'/(cfg['task']if a.phase=='original'else unit)/('d0'if a.phase=='original'else'final')/'seal.json')['files'];assert s.fingerprint(w)==expected
scope=R/'design'/cfg['task']/'public';approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'implementation-audit.json');policy_sha=approval['implementation_audit_sha256']
cat=audit.catalog(lock,approval['design_lock_sha256'],policy,policy_sha,w,scope)
if a.prepare:
 out=w/'agent-output'/('source-'+a.phase);s.save(out/'catalog.json',cat);s.save(out/'submission-template.json',{'version':1,'catalog_sha256':d.digest(cat),'decisions':[]});s.save(out/'prepared.json',{'atUnix':time.time(),'source':expected});print(out)
else:
 assert a.submission;submission=s.read(a.submission);result=audit.bind(cat,submission);assert s.fingerprint(w)==expected
 out=R/'source-self'/unit/a.phase
 for name,value in [('catalog.json',cat),('submission.json',submission),('report.json',result)]:s.save(out/name,value)
 s.save(out/'receipt.json',{'finishedAtUnix':time.time(),'source':expected,'catalog_sha256':d.digest(cat),'submission_sha256':s.sha(a.submission),'phase':a.phase,'sourceBound':True});s.seal_dir(out);print(out/'report.json')
