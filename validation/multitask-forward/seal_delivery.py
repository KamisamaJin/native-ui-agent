#!/usr/bin/env python3
"""Deliver only one anonymous complete cohort grade batch at a time."""
import argparse,json,shutil,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('stage',choices=['D0','FINAL']);a=p.parse_args();required='own-final'if a.stage=='D0'else'grade-d0';receipt=ex.gate.authorize(R/'gates',required,R);assignment=ex.read(R/'private/assignment.json');d=R/ex.read(R/'DESIGN-ROOT.json')['directory'];phase=a.stage.lower();out=R/'evaluation-inputs'/a.stage
for task,aliases in assignment['gradeAliases'].items():
 for alias in aliases:
  raw=R/'common-corpora'/task/alias/phase;assert(raw/'corpus-seal.json').is_file();ex.gate.verify(R/'gates','own-final',R)
  for rel,h in ex.read(raw/'portable-sha256.json').items():assert ex.sha(raw/rel)==h
assert not out.exists();out.mkdir(parents=True)
for task,aliases in assignment['gradeAliases'].items():
 corpora=[]
 for alias,unit in aliases.items():
  source=R/'submissions'/unit/phase;dest=out/task/alias/'source-capsule';shutil.copytree(source,dest);raw=R/'common-corpora'/task/alias/phase
  assert ex.read(raw/'corpus-seal.json')['source']==ex.read(source/'seal.json')['files']
  corpora.append({'anonymousID':alias,'sourceCapsule':str(dest.relative_to(R)),'captures':str(raw.relative_to(R)),'sourceSealSHA256':ex.sha(source/'seal.json'),'portableManifestSHA256':ex.sha(raw/'portable-sha256.json')})
 ex.save(out/task/'batch.json',{'stage':a.stage,'task':task,'cases':['P1','P2']+(['H1']if a.stage=='FINAL'else[]),'corpora':corpora,'grader':str((d/task/'private/grader.py').relative_to(R)),'scope':'Read only this anonymous task/stage corpus and independently fixed design. No original review, hidden future stage, other candidates/tasks or assignment material.'})
ex.save(out/'DELIVERY-SEAL.json',{'sealedAtUnix':time.time(),'authorization':receipt,'files':{str(p.relative_to(out)):ex.sha(p)for p in sorted(out.rglob('*'))if p.is_file()}});print('Sealed anonymous complete three-task batch:',a.stage)
