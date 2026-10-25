#!/usr/bin/env python3
"""Shared legacy-study namespace adapter: measure actual edits against pinned D0."""
import argparse
from pathlib import Path
import study as s
import design_contract as d
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
w=a.workspace.resolve();session=s.read(w/'SESSION.json');prior=session['previous'][a.platform][a.case];ticket=session['adoptions'][a.platform][a.case]
assert s.sha(ticket['path'])==ticket['sha256']and s.sha(prior['path'])==prior['sha256'];adoption=s.read(ticket['path']);receipt=s.read(prior['path']);before=s.read(Path(prior['path']).parent/'source-before.json')
roots=[w/rel for rel in s.ROOTS];assert adoption['original_receipt_sha256']==prior['sha256']and adoption['new_source_roots']==list(map(str,roots))and adoption['source_sha256']==d.digest(before)==receipt['source_sha256']
after=s.xp.source_fingerprint(roots)
s.save(a.output,{'source_before':d.digest(before),'source_after':d.digest(after),'changed_files':sorted(k for k in set(before)|set(after)if before.get(k)!=after.get(k)),
                 'original_capture_sha256':prior['sha256'],'adoption_sha256':ticket['sha256'],'basis':'Operator-measured source maps with identical-clone handoff; no new SDK run or edited capture receipt.'})
