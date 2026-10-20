#!/usr/bin/env python3
"""Uniform first-frame D0/FINAL gallery; never a coverage or style measurement."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gallery';out.mkdir(exist_ok=True);ledger=[]
 for unit in ['unit-93485d','unit-fb632e']:
  for platform in ['ios','android']:
   sheet=Image.new('RGB',(840,830),'#dddddd');draw=ImageDraw.Draw(sheet)
   for row,stage in enumerate(['d0','final']):
    for col,case in enumerate(['P1','P2','P3','P4']):
     corpus=R/'own-corpora'/unit/stage/platform/case
     observation=json.loads((corpus/'observation.json').read_text());source=corpus/observation['snapshots'][0]['screenshot']
     image=Image.open(source).convert('RGB');image.thumbnail((200,375));x=col*210;y=row*415
     sheet.paste(image,(x+5,y+25));draw.text((x+5,y+5),stage.upper()+' '+case+' snapshot0',fill='black')
     ledger.append({'unit':unit,'platform':platform,'stage':stage,'case':case,'snapshot':0,'source':str(source.relative_to(R)),'sourceSHA256':sha(source),'meaning':'Initial viewport only, not full content or numerical style proof.'})
   target=out/(unit+'-'+platform+'.png');sheet.save(target)
 (out/'provenance.json').write_text(json.dumps({'selection':'Every public case, same first native snapshot, both OS/arms/stages. No image chosen by score.','images':ledger},indent=2)+'\n')
 print(json.dumps({'galleries':4,'originalFrames':len(ledger)}))
if __name__=='__main__':main()
