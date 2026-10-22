#!/usr/bin/env python3
"""Verify independently sealed design and approvals before candidate launch."""
import json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
roots=[R/'design-v2',R/'design-review-v2/one',R/'design-review-v2/two'];records=[]
for folder in roots:
 p=folder/('seal.json'if folder.name=='design-v2'else'SEAL.json');v=json.loads(p.read_text());files=v.get('files',v.get('files_sha256'));assert isinstance(files,dict)
 for rel,h in files.items():
  if isinstance(h,dict):h=h['sha256']
  assert sha(folder/rel)==h,rel
 records.append({'path':str(folder.relative_to(R)),'sealSHA256':sha(p),'files':len(files)})
for panel in ['one','two']:assert json.loads((R/'design-review-v2'/panel/'review.json').read_text())['overall']=='approve'
assert not(R/'DESIGN-ROOT.json').exists()
(R/'DESIGN-ROOT.json').write_text(json.dumps({'directory':'design-v2','approvedAtUnix':time.time(),'independentApprovals':records[1:],'scope':'Independent sealed typed design; tools and metrics predate first task design. Nonblocking editorial notes remain disclosed, formal typed API and fixtures authoritative.'},indent=2)+'\n')
paths=['evaluation_adapter.py','prepare_judge_prompts.py','prepare_claims.py','claim_panels.py','pair_replay.py','preflight_submission.py','costs.py','build_summary.py','verify_study.py'];(R/'operators/preimplementation-adapter-freeze.json').write_text(json.dumps({'atUnix':time.time(),'files':{p:sha(R/p)for p in paths},'scope':'Shared field adapters and cost projections frozen before any candidate implementation; prospective evaluator/metrics remain tool-stage pinned.'},indent=2)+'\n')
seals=['design-v2/'+name for name in ['seal.json','SEAL.json']if(R/'design-v2'/name).is_file()]
members={task:['design-v2/'+task,*seals,'DESIGN-ROOT.json','design-review-v2/one','design-review-v2/two','operators/preimplementation-adapter-freeze.json','operators/pristine-settings.json','operators/pristine-workspaces.json']for task in ['T1','T2','T3']};(R/'operators/design-members.json').write_text(json.dumps(members,indent=2)+'\n');print(json.dumps(records))
