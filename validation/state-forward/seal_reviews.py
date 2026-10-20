#!/usr/bin/env python3
"""Deliver both original self-reviews only after both FINAL grades seal."""
import hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert(R/'evaluation/FINAL/SEAL.json').exists()
 out=R/'evaluation-inputs/selfreview';assert not out.exists();out.mkdir(parents=True)
 corpora=[]
 for alias,unit in read(R/'private/grade-assignment.json')['mapping'].items():
  dst=out/alias;shutil.copytree(R/'submissions'/unit/'original-review',dst/'original')
  corpora.append({'anonymousID':alias,'originalReviewDirectory':str((dst/'original').resolve()),'ownD0NativeCaptures':str((R/'own-corpora'/unit/'d0').resolve()),'independentD0Grade':str((R/'evaluation/D0'/alias/'grade.json').resolve()),'independentFinalGrade':str((R/'evaluation/FINAL'/alias/'grade.json').resolve())})
 batch={'stage':'selfreview','corpora':corpora,'scope':'Original pre-repair manual claims and actual typed failed rows, format-neutral eligibility. No FINAL self-checks or repair narratives are finding evidence. Preserve all uncertain/unmapped/duplicate claims; never infer detection from later repair. Main anonymous D0/FINAL quality grades are already sealed. Original formats/producer paths may reveal versions; procedural blindness is limited and those originals are not redacted.'}
 (out/'batch.json').write_text(json.dumps(batch,indent=2)+'\n')
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
 (out/'DELIVERY-SEAL.json').write_text(json.dumps({'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'priorFinalGradeSealSHA256':sha(R/'evaluation/FINAL/SEAL.json'),'files':files},indent=2)+'\n')
 print(json.dumps({'stage':'selfreview','files':len(files),'batch':str(out/'batch.json')}))
if __name__=='__main__':main()
