#!/usr/bin/env python3
"""Capture original phase artifacts; never edits candidate code or expectations."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def files(root):return {str(p.relative_to(root)):ex.sha(p)for p in sorted(root.rglob('*'))if p.is_file()and'__pycache__'not in p.parts}
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['initial','review','final']);p.add_argument('unit');a=p.parse_args();w=R/'cache'/a.unit;out=R/'submissions'/a.unit;out.mkdir(parents=True,exist_ok=True)
 if a.phase=='initial':
  ex.capsule(w,out/'d0');shutil.copytree(w/'agent-output',out/'initial-agent-output',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  assert all((out/'initial-agent-output/plans'/case/platform/'plan.json').is_file()and(out/'initial-agent-output/plans'/case/platform/'actions.json').is_file()for case in ['P1','P2']for platform in ['ios','android'])
 else:
  assert files(w/'agent-output/plans')==files(out/'initial-agent-output/plans'),'Original plans changed after D0'
  if a.phase=='review':
   assert ex.fingerprint(w)==ex.read(out/'d0/seal.json')['files'],'Read-only review changed production source'
   shutil.copytree(w/'agent-output/review',out/'original-review')
  else:
   ex.capsule(w,out/'final');shutil.copytree(w/'agent-output/repair',out/'final-agent-output')
 record={'phase':a.phase,'unit':a.unit,'submittedAtUnix':time.time(),'files':{str(p.relative_to(out)):ex.sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name not in ['initial-submission.json','review-submission.json','final-submission.json']}}
 ex.save(out/(a.phase+'-submission.json'),record);print(json.dumps({'unit':a.unit,'phase':a.phase,'files':len(record['files'])}))
if __name__=='__main__':main()
