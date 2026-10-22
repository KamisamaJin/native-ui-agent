from pathlib import Path
import json,math
from PIL import Image,ImageDraw
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward'); O=B/'judgments/final/two/T2'
manifest=[]
for entry in json.loads((O/'inspection-index.json').read_text()):
 rel=entry['case']; d=O/rel; ins=json.loads((d/'inspection-original.json').read_text()); inp=ins['inputs']; root=B/inp['root'];obs=json.loads((B/inp['observation']).read_text())
 cols=[];mapping={};w=260;g=28
 for st,ev in ins['state_evidence'].items():
  frames=[];h=0
  for index in ev['indices']:
   s=obs['snapshots'][index]; im=Image.open(root/s['screenshot']).convert('RGB')
   if inp['platform']=='ios':
    vp=s['viewport'];ct=s['runtime']['content_frame'];scale=im.width/s['app_frame']['width'];box=tuple(round(v*scale) for v in [vp['x'],vp['y'],vp['x']+vp['width'],vp['y']+vp['height']]);off=vp['y']-ct['y']; ch=ct['height'];offered=vp['width'];im=im.crop(box)
   else:
    offered=s['logical_viewport_dp']['width'];off=s['scroll_offset_dp'];ch=s['scroll_max_dp']+s['viewport_height_dp']
   scale=w/offered;y=round(off*scale);hh=round(600*scale);frames.append((index,im.resize((w,hh)),y));h=max(h,round(ch*scale))
  col=Image.new('RGB',(w+g,h),(245,140,235));dr=ImageDraw.Draw(col)
  for index,im,y in frames: col.paste(im,(g,y));dr.text((0,y),str(index),fill=(0,0,0))
  cols.append((st,ev,col));mapping[st]=[{'snapshot_index':j,'paste_y':y,'source':obs['snapshots'][j]['screenshot']} for j,im,y in frames]
 h=max(c.height for st,ev,c in cols);pages=math.ceil(h/1450)
 for page in range(pages):
  y=page*1450;ph=min(1450,h-y); sheet=Image.new('RGB',((w+g)*len(cols),ph+65),'white');dr=ImageDraw.Draw(sheet)
  for colno,(st,ev,c) in enumerate(cols):
   x=colno*(w+g);dr.text((x+4,4),f'{rel} / {st}',fill='black');dr.text((x+4,21),f'page {page+1}, y {y}:{y+ph}',fill='black');dr.text((x+4,38),f'complete={ev["complete"]}, n={len(ev["indices"])}',fill='black')
   if y<c.height:sheet.paste(c.crop((0,y,c.width,min(c.height,y+ph))),(x,65))
  f=d/f'contact-sheet-{page+1:02d}.png';sheet.save(f)
  manifest.append({'path':str(f.relative_to(O)),'case':rel,'page':page+1,'derived_from_original':True,'mapping':mapping,'note':'Original viewport PNG crops remapped only by observed native scroll offset; magenta is unobserved coverage or non-content margin. Index labels identify original frame starts. Original PNG hashes retained in input-hashes and inspection-original.'})
(O/'contact-sheet-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('\n'.join(m['path'] for m in manifest))
