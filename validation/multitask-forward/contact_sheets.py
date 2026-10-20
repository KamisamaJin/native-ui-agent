#!/usr/bin/env python3
"""Review aid only: original native PNGs remain the assertion evidence."""
import argparse,json,math
from pathlib import Path
from PIL import Image,ImageDraw
import experiment as ex

def main():
 p=argparse.ArgumentParser();p.add_argument('corpus',type=Path);p.add_argument('output',type=Path);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True);index=[]
 for op in sorted(a.corpus.glob('*/*/observation.json')):
  obs=ex.read(op);groups={}
  for i,s in enumerate(obs['snapshots']):groups.setdefault(s.get('state_id','unknown'),[]).append((i,s))
  for state,items in groups.items():
   for page in range(0,len(items),4):
    tiles=[];proofs=[]
    for i,s in items[page:page+4]:
     imagepath=op.parent/s['screenshot'];im=Image.open(imagepath).convert('RGB');crop=None
     app=s.get('app_frame');vp=s.get('viewport')
     if app and vp and app.get('width',0)>0 and app.get('height',0)>0:
      sx,sy=im.width/app['width'],im.height/app['height'];x=(vp['x']-app['x'])*sx;y=(vp['y']-app['y'])*sy
      crop=[max(0,math.floor(x)),max(0,math.floor(y)),min(im.width,math.ceil(x+vp['width']*sx)),min(im.height,math.ceil(y+vp['height']*sy))]
      if crop[2]>crop[0]and crop[3]>crop[1]:im=im.crop(crop)
     height=round(im.height*360/im.width);im=im.resize((360,height));tile=Image.new('RGB',(360,height+32),'#eeeeee');tile.paste(im,(0,32));draw=ImageDraw.Draw(tile);draw.text((6,6),'snapshot '+str(i)+' | '+state,fill='black');tiles.append(tile)
     proofs.append({'snapshot_index':i,'state':state,'original':str(imagepath),'sha256':ex.sha(imagepath),'review_crop_only':crop})
    h=max(t.height for t in tiles);sheet=Image.new('RGB',(720,h*2),'#dddddd')
    for j,tile in enumerate(tiles):sheet.paste(tile,((j%2)*360,(j//2)*h))
    name='-'.join([op.parent.parent.name,op.parent.name,state,str(page//4)])+'.png';sheet.save(a.output/name);index.append({'sheet':name,'observation':str(op),'observationSHA256':ex.sha(op),'tiles':proofs})
 ex.save(a.output/'index.json',{'scope':'Deterministic review-only viewport crops/downscales. Does not measure, replace or alter original evidence. Cite original state PNGs with hashes in manual decisions.','pages':index});print(json.dumps({'reviewSheets':len(index)}))
if __name__=='__main__':main()
