#!/usr/bin/env python3
"""Audit preregistered materials and sealed production bytes; no UI judgment replay."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 f=read(R/'freeze.json');assert sha(R/'PREREGISTRATION.md')==f['preregistration_sha256']
 for name,digest in read(R/'design-freeze.json')['design'].items():assert sha(R/'design'/name)==digest,name
 for name,digest in f['skill_v1'].items():assert sha(R.parent/'blind-comparison/skill-v1'/name)==digest,name
 for name,digest in f['skill_v2'].items():assert sha(R/'skill-v2'/name)==digest,name
 amendments={x['file']:x for x in read(R/'host-amendments.json')['amendments']}
 for name,digest in f['harness'].items():
  if name in amendments:
   a=amendments[name];assert a['old_sha256']==digest and sha(R/a['original_archive'])==digest
   assert sha(R/'harness'/name)==a['new_sha256']
   for path,value in a.get('retained_failure_logs',{}).items():assert sha(R/path)==value
  else:assert sha(R/'harness'/name)==digest,name
 oracle=read(R/'design/private/oracle.json');assert len([c for c in oracle['cases']if c['phase']=='initial'])==6 and len([c for c in oracle['cases']if c['phase']=='repair_holdout'])==2
 for phase in ['d0','final']:
  root=R/'implementations'/phase
  if phase=='d0':assert len(list(root.glob('submission-*')))==3
  for submission in root.glob('submission-*'):
   manifest=read(submission/'manifest.json');assert manifest['files']
   for path,digest in manifest['files'].items():assert sha(submission/path)==digest
 print(json.dumps({'status':'passed_frozen_material_audit','design_cases':8,'arms':3,'skill_v2_files':len(f['skill_v2']),'uniform_host_amendments':len(amendments),'does_not_replay':'Native SDKs, AI implementation, image/semantic grading or experimental outcomes'}))
if __name__=='__main__':main()
