#!/usr/bin/env python3
"""Validate immutable phase metadata and release only after all eight blind seals."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from contract import R,read,sha,canonical
REPO=R.parents[1]
def epoch(value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def verify_ref(base,row):
 p=(base/row['path']).resolve();assert p.is_relative_to(REPO.resolve())and p.is_file();assert sha(p)==row['sha256'],p
def stages():
 mapping=read(R/'private/grade-assignment.json')['mapping'];seals={};previous=0
 for phase in ['d0','final','selfreview','paired-d0']:
  delivery=read(R/'private/grade-deliveries'/(phase+'.json'));t=epoch(delivery['preparedAtUTC']);assert t>=previous,('Later phase prepared before BOTH previous grades sealed',phase)
  times=[]
  for anon in mapping:
   capsule=R/'private/grade-capsules'/phase/anon;cs=read(capsule/('SEAL.json'if phase=='selfreview'else'capsule-seal.json'))
   for rel,h in cs['files'].items():assert sha(capsule/rel)==h,('Original delivered capsule changed',phase,anon,rel)
   p=R/'design/private/evaluation'/phase/anon/'SEAL.json';d=read(p);assert hashlib.sha256(canonical(d['payload']).encode()).hexdigest()==d['commitment_sha256']
   x=d['payload'];assert x['phase']==phase and x['anonymous_id']==anon
   assert x['active_evaluator_commitment']==read(R/'evaluator-v3-commitment.json')['commitment_sha256']
   for row in x['files']:verify_ref(p.parent,row)
   for row in x['inputs']:verify_ref(REPO,row)
   when=epoch(x['sealed_at_utc']);assert when>=t;times.append(when);seals[str(p.relative_to(R))]=sha(p)
  previous=max(times)
 return seals,previous
def main():
 p=argparse.ArgumentParser();p.add_argument('--release',action='store_true');a=p.parse_args();seals,last=stages();out=R/'private/assignment-release.json'
 if a.release:
  assert not out.exists()
  d={'releasedAtUTC':datetime.now(timezone.utc).isoformat(),'allBlindStageSeals':seals,'assignmentSHA256':sha(R/'private/assignment.json'),'gradeAssignmentSHA256':sha(R/'private/grade-assignment.json'),'scope':'Formal assignment released only after D0, FINAL, self-review matching and paired D0 assessments seal for BOTH anonymous sources. Root may now read outcomes and perform arithmetic.'};assert epoch(d['releasedAtUTC'])>=last;out.write_text(json.dumps(d,indent=2)+'\n')
 d=read(out);assert d['allBlindStageSeals']==seals and epoch(d['releasedAtUTC'])>=last;assert d['assignmentSHA256']==sha(R/'private/assignment.json')and d['gradeAssignmentSHA256']==sha(R/'private/grade-assignment.json')
 print('PASS: all eight blind stage seals, original inputs, phase order and formal release')
if __name__=='__main__':main()
