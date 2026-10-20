#!/usr/bin/env python3
"""Relocatable provenance/protocol audit, independent of product judgments."""
import argparse, hashlib, json
from datetime import datetime
from pathlib import Path
from verify_capture_sources import check

R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def epoch(v):return datetime.fromisoformat(v.replace(' UTC','+00:00').replace('Z','+00:00')).timestamp()
def envelope(path,base):
 d=read(path);assert hashlib.sha256(canonical(d['payload'])).hexdigest()==d['commitment_sha256'],path
 for row in d['payload']['files']:
  p=(base/row['path']).resolve();assert p.is_relative_to(base.resolve());assert sha(p)==row['sha256'],p
 return d
def corpus(path,capsule):
 out=[]
 for platform in ['ios','android']:
  for rel,h in read(path/platform/'portable-sha256.json').items():assert sha(path/platform/rel)==h,(path,rel)
  rows=check(capsule,path/platform,platform);out+=rows
  commands=[read(p)for p in sorted((path/platform).glob('*-command.json'))]
  assert [x['case']for x in commands]==sorted(x['case']for x in commands)
  for a,b in zip(commands,commands[1:]):assert a['finishedAtUnix']<=b['startedAtUnix']
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--engineering-only',action='store_true');a=p.parse_args()
 for name in ['pre-design-method-commitment.json']:
  for rel,h in read(R/name)['files'].items():assert sha(R/rel)==h,(name,rel)
 for rel,h in read(R/'candidate-v4-freeze.json')['files'].items():assert sha(R.parent.parent/'native-ui-agent'/rel)==h,('live skill differs',rel)
 design=envelope(R/'design/private/SEAL.json',R/'design')
 prep=R/'design/private/evaluator-prep'
 for sub,name in [('', 'PREP-SEAL.json'),('v2','V2-SEAL.json'),('v3','V3-SEAL.json')]:envelope(prep/sub/name,prep/sub)
 assert read(R/'design-commitment.json')['commitment_sha256']==design['commitment_sha256']
 for name,private,key in [('assignment-commitment.json','assignment.json','sha256'),('grade-assignment-commitment.json','grade-assignment.json','sha256')]:
  d=read(R/name);assert sha(R/'private'/private)==d[key]
 if a.engineering_only:
  print('PASS: frozen tools, design, evaluator and assignments');return
 arms=read(R/'private/assignment.json')['arms'];ledger=read(R/'private/phase-ledger.json')['events']
 final_seal=max(epoch(read(R/'private/submissions'/x['submission']/'final/seal.json')['sealedAtUTC'])for x in arms)
 assert epoch(read(R/'private/inputs/final/seal.json')['createdAtUTC'])>final_seal
 for name in ['d0','d0-v2','final']:
  inp=R/'private/inputs'/name
  for rel,h in read(inp/'seal.json')['files'].items():assert sha(inp/rel)==h
 for p in (R/'private/inputs/d0-v2').glob('*/*.json'):assert p.read_bytes()==(R/'private/inputs/final'/p.relative_to(R/'private/inputs/d0-v2')).read_bytes()
 total=[];last_primary=0
 for arm in arms:
  sid=arm['submission'];s=R/'private/submissions'/sid
  for phase in ['d0','final']:
   for rel,h in read(s/phase/'seal.json')['files'].items():assert sha(s/phase/'source'/rel)==h
   rows=corpus(R/'evidence'/('own-'+phase)/sid,s/phase);assert len(rows)==(8 if phase=='d0'else 12);total+=rows
  assert sha(s/'review.json')==read(s/'review-seal.json')['reviewSHA256']
  assert epoch(read(s/'review-seal.json')['sealedAtUTC'])<=epoch(read(s/'final/seal.json')['sealedAtUTC'])
  last_primary=max(last_primary,read(s/'final-corpus-seal.json')['sealedAtUnix'])
 for name,phase,sid,n in [('audit-v4-d0','d0','submission-e572b1',8),('audit-v4-final','final','submission-e572b1',12),('audit-v3-d0','d0','submission-3d6389',8)]:
  c=R/'evidence'/name/sid;rows=corpus(c,R/'private/submissions'/sid/phase);assert len(rows)==n;total+=rows
  for p in c.glob('*/*-command.json'):assert read(p)['startedAtUnix']>=last_primary
 assert len(total)==68
 # Shared administrative failures stay distinct from the 68 planned commands.
 failed=R/'evidence/administrative-first-d0/submission-3d6389'
 assert failed.exists()
 extras=[]
 for plat in ['ios','android']:
  for p in (failed/plat).glob('*-command.json'):extras.append((plat,read(p)))
 assert len(extras)==8 and sum(d['exitCode']==2 for _,d in extras)==4
 assert all(d['exitCode']==(2 if plat=='ios'else 0)for plat,d in extras)
 assert any(x['event']=='both_final_sources_sealed_before_heldouts'for x in ledger)
 print(json.dumps({'status':'PASS','planned_acquisitions':len(total),'administrative_extra_attempts':len(extras),'planned_native_failures':sum(x['exitCode']!=0 for x in total)}))
if __name__=='__main__':main()
