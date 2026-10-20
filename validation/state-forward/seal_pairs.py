#!/usr/bin/env python3
"""Deliver both same-source collector pairs after self-review matching seals."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert(R/'evaluation/selfreview/SEAL.json').exists()
 out=R/'evaluation-inputs/paired-D0';assert not out.exists();out.mkdir(parents=True)
 corpora=[]
 for alias in ['source-a','source-b']:
  paths={'v4':R/'paired-corpora'/alias/'v4','v5':R/'common-corpora'/alias/'d0'}
  a,b=[read(p/'corpus.json')for p in paths.values()];assert a['source']==b['source']
  for platform in ['ios','android']:
   assert[(x['case'],x['inputHashes'])for x in a['platformRuns'][platform]]==[(x['case'],x['inputHashes'])for x in b['platformRuns'][platform]]
  for p in paths.values():
   s=read(p/'corpus-seal.json');assert sha(p/'portable-sha256.json')==s['portableManifestSHA256']
   for rel,h in read(p/'portable-sha256.json').items():assert sha(p/rel)==h
  corpora.append({'anonymousID':alias,'sourceCapsule':str((R/'evaluation-inputs/D0'/alias/'source-capsule').resolve()),'v4Captures':str(paths['v4'].resolve()),'v5Captures':str(paths['v5'].resolve()),'v5ReusedD0Grade':str((R/'evaluation/D0'/alias/'grade.json').resolve()),'v5ReusedD0Normalized':str((R/'evaluation/D0'/alias/'normalized.json').resolve()),'portableManifests':{k:sha(p/'portable-sha256.json')for k,p in paths.items()}})
 batch={'stage':'paired-D0','corpora':corpora,'nativeInputs':str((R/'evaluation-inputs/D0/native-inputs').resolve()),'mappings':str((R/'evaluation-inputs/D0/mappings').resolve()),'immutableHelper':str((R/'candidate-v5/scripts/native_checks.py').resolve()),'scope':'Four public cases, same D0 source and exact native stimulus/action bytes per pair. V5 raw captures are byte-exact common-D0 reuse, not fresh captures. Preserve v5 original D0 literal row judgments. Score actual v4 sparse-view evidence only; no source or unseen screenshots to fill it. Collector formats are deliberately identified; builder treatment assignment remains unreleased.'}
 (out/'batch.json').write_text(json.dumps(batch,indent=2)+'\n')
 (out/'DELIVERY-SEAL.json').write_text(json.dumps({'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'priorSelfReviewGradeSealSHA256':sha(R/'evaluation/selfreview/SEAL.json'),'files':{'batch.json':sha(out/'batch.json')},'corpora':corpora},indent=2)+'\n')
 print(json.dumps({'stage':'paired-D0','pairs':2,'batch':str(out/'batch.json')}))
if __name__=='__main__':main()
