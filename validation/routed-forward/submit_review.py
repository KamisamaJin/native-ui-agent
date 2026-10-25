#!/usr/bin/env python3
"""Integration review intake: bind original actuals and auto-register for planning."""
import argparse,time
from pathlib import Path
import study as s
import evidence_review as review
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--case',required=True);p.add_argument('--capture-result',type=Path,required=True);p.add_argument('--submission',type=Path,required=True);a=p.parse_args()
R=s.R;w=a.workspace.resolve();unit=w.name;assignment=s.read(R/'private/assignment.json')['units'][unit];assert w==R/'cache'/unit
s.tool_verify();s.host_verify(w);capture=a.capture_result.resolve()
allowed=[R/s.read(R/'operators/active-D0.json')['path'],R/'cache/acquisitions'/unit,R/'feedback'/unit,R/'corpora'/unit/'final-public']
assert any(capture.is_relative_to(v)for v in allowed),'Review must use shared D0 or own original capture'
config=s.configuration(w,R/'design/public',a.case,a.platform,assignment['simulator'])
session=s.read(w/'SESSION.json');config['adoption']=session['adoptions'][a.platform][a.case]
started=time.time();store=Path(config['review_store']);key=s.sha(a.submission)
reference=review.bind(config,capture,s.sha(capture),a.submission,s.sha(a.submission),store/('review-'+key))
s.save(store/('intake-'+key+'.json'),{'startedAtUnix':started,'finishedAtUnix':time.time(),'captureSHA256':s.sha(capture),'reference':reference,'scope':'Actuals-only immutable intake; discovery is automatic on the next service call.'})
print(reference)
