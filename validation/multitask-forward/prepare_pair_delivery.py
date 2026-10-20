#!/usr/bin/env python3
"""Deliver actual v6 captures and byte-exact already sealed v7 native scores."""
import shutil,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def main():
 receipt=ex.gate.authorize(R/'gates','grade-selfreview',R);assignment=ex.read(R/'private/assignment.json');out=R/'evaluation-inputs/paired-D0';assert not out.exists()
 # Validate the complete six-source acquisition batch before any delivery exists.
 for task,aliases in assignment['gradeAliases'].items():
  for alias in aliases:
   raw=R/'paired-corpora'/task/alias/'v6';assert(raw/'corpus-seal.json').is_file()
   for rel,h in ex.read(raw/'portable-sha256.json').items():assert ex.sha(raw/rel)==h
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     base=R/'evaluation/D0'/task/alias/case/platform
     assert(base/'native-base-grade.json').is_file()and(base/'native-base.json').is_file()
 for task,aliases in assignment['gradeAliases'].items():
  corpora=[]
  for alias in aliases:
   copied=[]
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     base=R/'evaluation/D0'/task/alias/case/platform;dest=out/task/alias/'v7'/case/platform;dest.mkdir(parents=True)
     for name in ['native-base-grade.json','native-base.json']:
      shutil.copyfile(base/name,dest/name);assert ex.sha(base/name)==ex.sha(dest/name)
      copied.append({'source':str((base/name).relative_to(R)),'destination':str((dest/name).relative_to(R)),'sha256':ex.sha(base/name)})
   corpora.append({'anonymousID':alias,'v6Captures':str((R/'paired-corpora'/task/alias/'v6').relative_to(R)),'v7Captures':str((R/'common-corpora'/task/alias/'d0').relative_to(R)),'v7OriginalScores':str((out/task/alias/'v7').relative_to(R)),'exactCopies':copied})
  ex.save(out/task/'batch.json',{'stage':'paired-D0','task':task,'cases':['P1','P2'],'corpora':corpora,'sameFrameReplay':str((R/'precision-replay'/task).relative_to(R)),'scope':'Actual v6 native sessions; v7 native scores are exact immutable D0 bytes. Same-frame checker replay is a separate zero-SDK arithmetic diagnostic.'})
 ex.save(out/'DELIVERY-SEAL.json',{'sealedAtUnix':time.time(),'authorization':receipt,'files':{str(p.relative_to(out)):ex.sha(p)for p in sorted(out.rglob('*'))if p.is_file()}})
 print('Sealed exact native pair delivery for all three tasks')
if __name__=='__main__':main()
