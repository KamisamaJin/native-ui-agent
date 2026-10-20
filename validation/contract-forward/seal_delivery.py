#!/usr/bin/env python3
"""Seal both anonymous common-observer corpora before releasing a grade batch."""
import argparse,hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['D0','FINAL']);a=p.parse_args();phase=a.stage.lower();out=R/'evaluation-inputs'/a.stage;assert not out.exists();out.mkdir(parents=True)
 assignment=read(R/'private/assignment.json');corpora=[]
 if a.stage=='FINAL':assert(R/'evaluation/D0/SEAL.json').is_file(),'Both D0 grades must seal before FINAL delivery'
 for alias,unit in assignment['gradeAliases'].items():
  source=R/'submissions'/unit/phase;raw=R/'common-corpora'/alias/phase;seal=read(raw/'corpus-seal.json');assert read(source/'seal.json')['files']==seal['source']
  for rel,h in read(raw/'portable-sha256.json').items():assert sha(raw/rel)==h
  dest=out/alias/'source-capsule';shutil.copytree(source,dest)
  corpora.append({'anonymousID':alias,'sourceCapsule':str(dest.relative_to(R)),'captures':str(raw.relative_to(R)),'sourceSealSHA256':sha(dest/'seal.json'),'portableManifestSHA256':sha(raw/'portable-sha256.json')})
 shutil.copytree(R/'private'/('common-inputs-'+phase),out/'native-inputs')
 batch={'stage':a.stage,'corpora':corpora,'nativeInputs':str((out/'native-inputs').relative_to(R)),'grader':'design/private/grader.py','root':str(R),'cases':['P1','P2']+(['H1']if a.stage=='FINAL'else[]),'scope':'Anonymous dual delivery. Read only this named source/capture batch; original reviews and assignment remain sealed.'}
 (out/'batch.json').write_text(json.dumps(batch,indent=2)+'\n')
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
 (out/'DELIVERY-SEAL.json').write_text(json.dumps({'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'files':files,'corpora':corpora},indent=2)+'\n');print(json.dumps({'stage':a.stage,'files':len(files)}))
if __name__=='__main__':main()
