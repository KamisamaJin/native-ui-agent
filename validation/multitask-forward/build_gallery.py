#!/usr/bin/env python3
"""Index original native frames by fixed scene, without synthesizing pixels."""
import argparse,json,sys
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate-v7/scripts'));import native_checks as nc
SCENES=[('P1','loaded'),('P2','replaced')]
def make():
 ex.gate.verify(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];ledger=[];lines=['# Original component frames','','Fixed scenes: P1 loaded and P2 replaced. Select the first coherent state frame with a unique fully visible title; otherwise label a partial frame. These are original PNGs, not rendered reconstructions or a pixel-regression baseline. Long components may extend outside a single viewport; full state evidence remains in the observations and independent grades. Wireframes use a different renderer and do not establish native font equivalence.','']
 for task,aliases in assignment['gradeAliases'].items():
  lines += ['## '+task,'',f'[P1 reference]({design.name}/{task}/public/references/P1-loaded.png) · [P2 reference]({design.name}/{task}/public/references/P2-loaded.png)','','| Platform / arm | P1 loaded D0 | P1 loaded FINAL | P2 replaced D0 | P2 replaced FINAL |','|---|---|---|---|---|']
  for platform in ['ios','android']:
   for alias,unit in aliases.items():
    tool=assignment['units'][unit]['tool'];cells=[]
    for case,state in SCENES:
     plan=ex.read(design/task/'public/compiled'/case/platform/'plan.json');spec=next(s for s in plan['states']if s['id']==state);target=next(a['target']for a in plan['assertions']if a['state']==state and a.get('requirement_id')=='title')
     for phase in ['d0','final']:
      op=R/'common-corpora'/task/alias/phase/platform/case/'observation.json'
      if not op.is_file():cells.append('Missing native observation');continue
      obs=ex.read(op);found,complete,_,_=nc.state_evidence(obs,spec);preferred=[]
      for index,snapshot in found:
       resolution=nc.resolve(snapshot,target,platform);node=resolution.get('semantic',{})
       if resolution['facts'].get('unique')and node.get('fully_within_viewport',node.get('fully_visible',False)):preferred.append((index,snapshot))
      chosen=preferred or found
      if not chosen:cells.append('No coherent state frame');continue
      index,snapshot=chosen[0];image=op.parent/snapshot['screenshot'];rel=str(image.relative_to(R));ledger.append({'task':task,'alias':alias,'tool':tool,'platform':platform,'case':case,'state':state,'phase':phase,'snapshot':index,'titleFullyVisible':bool(preferred),'nativeIntervalComplete':complete,'observation':str(op.relative_to(R)),'observationSHA256':ex.sha(op),'path':rel,'sha256':ex.sha(image)});cells.append(f'![{task} {tool} {platform} {case} {state} {phase}]({rel})')
    lines.append('| '+' | '.join([platform+' / '+tool]+cells)+' |')
  lines.append('')
 lines += ['These frames do not certify computed iOS styles, literal padding, transformed paint bounds or physical hit regions. See independent grades for actual dispositions; CI checks evidence integrity, not universal UI acceptance.','']
 return '\n'.join(lines),ledger
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();text,ledger=make();out=R/'GALLERY.md';meta=R/'gallery-images.json'
 if a.write:assert not out.exists()and not meta.exists();out.write_text(text);ex.save(meta,ledger)
 else:assert out.read_text()==text and ex.read(meta)==ledger
 print('PASS: fixed gallery scenes point to SHA-bound original state PNGs')
if __name__=='__main__':main()
