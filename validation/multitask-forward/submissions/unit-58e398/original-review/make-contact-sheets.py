from pathlib import Path
import json,hashlib,math,time
from PIL import Image,ImageDraw
root=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/own-corpora/unit-58e398/d0')
output=Path(__file__).resolve().parent
states=['loaded','chosen','details','optioned','submitted','replaced']
manifest=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  base=root/platform/case;obs=json.loads((base/'observation.json').read_text()); rows=[]
  for state in states:
   cap=next(x for x in obs['state_captures'] if x['state_id']==state)
   thumbs=[]
   for idx in cap['snapshot_indices']:
    snap=obs['snapshots'][idx];p=base/snap['screenshot'];im=Image.open(p).convert('RGB')
    if platform=='ios':
     v=snap['viewport'];scale=im.width/snap['app_frame']['width']
     im=im.crop((round(v['x']*scale),round(v['y']*scale),round((v['x']+v['width'])*scale),round((v['y']+v['height'])*scale)))
    width=240; im=im.resize((width,round(im.height*width/im.width)))
    tile=Image.new('RGB',(width+8,im.height+30),'#ddd');tile.paste(im,(4,26));ImageDraw.Draw(tile).text((4,5),f'{case} {platform} {state} index {idx}',fill='black');thumbs.append(tile)
    manifest.append({'case':case,'platform':platform,'state':state,'index':idx,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
   row=Image.new('RGB',(sum(x.width for x in thumbs),max(x.height for x in thumbs)),'#ddd');x=0
   for im in thumbs:row.paste(im,(x,0));x+=im.width
   rows.append(row)
  sheet=Image.new('RGB',(max(x.width for x in rows),sum(x.height for x in rows)),'#ccc');y=0
  for im in rows:sheet.paste(im,(0,y));y+=im.height
  p=output/f'{case}-{platform}-all-selected-states.png';sheet.save(p);print(p)
(output/'contact-sheet-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
