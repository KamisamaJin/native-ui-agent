#!/usr/bin/env python3
"""Close an entire producer cohort using only its immutable phase outputs."""
import argparse,json,subprocess,sys
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['initial','review','final']);a=p.parse_args()
 units=ex.read(R/'private/assignment.json')['units'];members={}
 for unit,data in units.items():
  base=R/'submissions'/unit
  assert(base/(a.phase+'-submission.json')).is_file(),f'Missing {unit} {a.phase}'
  if a.phase=='initial':
   public=R/ex.read(R/'DESIGN-ROOT.json')['directory']/data['task']/'public'
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     original=base/'initial-agent-output/plans'/case/platform
     approved=public/'compiled'/case/platform
     assert ex.read(original/'actions.json')==ex.read(approved/'actions.json'),f'Changed approved action sequence: {unit}/{case}/{platform}'
   names=['d0','initial-agent-output','initial-submission.json']
   members[unit]=[str((base/n).relative_to(R))for n in names]+['operators/'+unit+'-initial-preflight.json']
  elif a.phase=='review':members[unit]=[str((base/n).relative_to(R))for n in ['original-review','review-submission.json']]
  else:members[unit]=[str((base/n).relative_to(R))for n in ['final','final-agent-output','final-submission.json']]
 stage={'initial':'d0-sources','review':'reviews','final':'final-sources'}[a.phase]
 path=R/'operators'/(stage+'-members.json');ex.save(path,members)
 subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),stage,'--members',str(path)],check=True)

if __name__=='__main__':main()
