#!/usr/bin/env python3
"""Seal a complete anonymous common-observer batch; never deliver one arm alone."""
import argparse,hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['D0','FINAL']);a=p.parse_args();phase=a.stage.lower()
 out=R/'evaluation-inputs'/a.stage;assert not(out/'DELIVERY-SEAL.json').exists()
 corpus=[]
 for alias in ['source-a','source-b']:
  raw=R/'common-corpora'/alias/phase;seal=read(raw/'corpus-seal.json')
  assert sha(raw/'portable-sha256.json')==seal['portableManifestSHA256']
  for rel,h in read(raw/'portable-sha256.json').items():assert sha(raw/rel)==h,(alias,rel)
  source=out/alias/'source-capsule';assert read(source/'seal.json')['files']==seal['source']
  for rel,h in seal['source'].items():assert sha(source/'source'/rel)==h
  corpus.append({'anonymousID':alias,'sourceCapsule':str(source.resolve()),'captures':str(raw.resolve()),'portableManifestSHA256':sha(raw/'portable-sha256.json'),'sourceSealSHA256':sha(source/'seal.json')})
 for name,src in [('native-inputs','common-inputs-'+phase),('mappings','common-mappings-'+phase)]:shutil.copytree(R/'private'/src,out/name)
 batch={'stage':a.stage,'corpora':corpus,'nativeInputs':str((out/'native-inputs').resolve()),'mappings':str((out/'mappings').resolve()),'immutableHelper':str((R/'candidate-v5/scripts/native_checks.py').resolve()),'scope':'Both anonymous corpora supplied simultaneously; read only this named stage. Current native facts, stimulus behavior, visual/source/input reviews and attribution remain separate.'}
 (out/'batch.json').write_text(json.dumps(batch,indent=2)+'\n')
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
 (out/'DELIVERY-SEAL.json').write_text(json.dumps({'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'files':files,'corpora':corpus},indent=2)+'\n')
 print(json.dumps({'stage':a.stage,'files':len(files),'batch':str(out/'batch.json')}))
if __name__=='__main__':main()
