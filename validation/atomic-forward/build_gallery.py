#!/usr/bin/env python3
"""Link deterministic original state frames; thumbnails are not a measurement basis."""
import argparse
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def render():
 ex.gate.authorize(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');parts=['# Original state-frame gallery','These links select the first and last recorded frames of baseline, expanded and submitted states for every planned case/source/platform/stage. Public P1/P2 appear at D0 and FINAL; heldout H1 appears only at FINAL. Selection is deterministic, not a favorable visual example. Read the observation JSON and full state-frame set for complete coverage. Missing/incomplete state evidence stays unknown. No image here is a golden or a computed-style proof.']
 for task,aliases in assignment['gradeAliases'].items():
  parts.append('## '+task)
  for alias,unit in aliases.items():
   parts.append('### '+alias+' — '+assignment['units'][unit]['tool']);rows=[]
   for pl in ['ios','android']:
    for phase in ['d0','final']:
     for case in ['P1','P2']+(['H1']if phase=='final'else[]):
      root=R/'common-corpora'/task/alias/phase/pl/case;op=root/'observation.json'
      if not op.is_file():rows.append([pl,phase,case,'missing','N/A','[original command/log]('+str(root.parent.relative_to(R))+')']);continue
      obs=ex.read(op);by={s.get('index',i):s for i,s in enumerate(obs['snapshots'])}
      for state in ['baseline','expanded','submitted']:
       captures=[v for v in obs.get('state_captures',[])if v.get('state_id')==state];ids=sorted({i for v in captures for i in v.get('snapshot_indices',[])if i in by})
       if not ids:ids=sorted(i for i,s in by.items()if s.get('state_id')==state)
       links=[]
       for i in sorted(set(ids[:1]+ids[-1:])):
        image=by[i].get('screenshot');path=root/image if image else None
        if path and path.is_file():links.append('[frame '+str(i)+']('+str(path.relative_to(R))+')')
       rows.append([pl,phase,case,state,str(any(v.get('complete')is True for v in captures)),' · '.join(links)or'No original PNG'])
      rows.append([pl,phase,case,'full observation','—','[native facts, identities, coverage]('+str(op.relative_to(R))+')'])
   parts.append('\n'.join(['| Platform | Stage | Case | State | Full state complete | Original evidence |','| --- | --- | --- | --- | --- | --- |']+['| '+' | '.join(row)+' |'for row in rows]))
 parts +=['## Review and repair provenance','Original self-review images/claims, including errors and uncertainty, remain in [submissions](submissions/). Only those original observations were available to builders during their single repair. Anonymous common grading and hidden data were delivered afterward. Final differences are not retroactive detection credit.','[Acceptance and repair metrics](TABLES.md) · [Failures and limits](FAILURES.md) · [Original anonymous quality judgments](judgments/) · [Independent original-claim judgments](claim-judgments/)']
 return '\n\n'.join(parts)+'\n'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=render();path=R/'GALLERY.md'
 if a.check:assert path.read_text()==value
 else:assert not path.exists();path.write_text(value)
 print('PASS original state-frame gallery')
if __name__=='__main__':main()
