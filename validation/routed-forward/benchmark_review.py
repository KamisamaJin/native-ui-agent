#!/usr/bin/env python3
"""Bind operator's original inspected benchmark observations; never a reviewer."""
import argparse,time
from pathlib import Path
import benchmark as b
import native_checks as n,review_contract as review,design_contract as d
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--submission',type=Path);a=p.parse_args();c=b.config();capture=b.R/'cache/benchmark'/a.name
if (capture/'capture/result.json').exists():capture=capture/'capture'
op=capture/'native/observation.json';observation=b.read(op);plan=b.read(c['plan']);lock=b.read(c['design_lock']);policy=b.read(c['policy']);catalog=review.catalog(plan,lock,c['design_sha256'],policy,c['policy_sha256'],'ios')
if not a.submission:
 print([(r['id'],n.bound_state_evidence(observation,next(s for s in plan['states']if s['id']==r['state']))[0][0][0])for r in catalog['rows']]);raise SystemExit()
ref=b.evidence_review.bind(c,capture/'result.json',b.sha(capture/'result.json'),a.submission,b.sha(a.submission),Path(c['review_store'])/a.name)
b.save(b.R/'operators/benchmark'/(a.name+'-review.json'),dict(ref,finishedAtUnix=time.time()));print(ref)
