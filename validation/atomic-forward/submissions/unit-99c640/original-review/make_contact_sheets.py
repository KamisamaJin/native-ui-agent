from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[2];O=W/'review' if W.name=='agent-output' else W/'agent-output/review'
C=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/own-corpora/unit-99c640/d0')
manifest=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  base=C/platform/case;o=json.loads((base/'observation.json').read_text())
  for state in ['baseline','selected','expanded','blocked','replaced','reselected','submitted']:
   sc=next(x for x in o['state_captures'] if x['state_id']==state)
   thumbs=[];sources=[]
   for i in sc['snapshot_indices']:
    s=o['snapshots'][i];p=base/s['screenshot'];im=Image.open(p).convert('RGB')
    if platform=='ios':
     v=s['viewport'];scale=im.width/s['app_frame']['width'];im=im.crop(tuple(round(v[k]*scale) for k in ['x','y'])+tuple(round((v[a]+v[b])*scale) for a,b in [('x','width'),('y','height')]))
    width=390 if case=='P1' else 280
    im=im.resize((width,round(im.height*width/im.width)))
    tile=Image.new('RGB',(width,im.height+26),'#FFFFFF');tile.paste(im,(0,26));ImageDraw.Draw(tile).text((5,5),f'{platform} {case} {state} index {i}',fill='black');thumbs.append(tile)
    sources.append({'snapshot_index':i,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
   ncols=min(4,len(thumbs));h=max(t.height for t in thumbs);sheet=Image.new('RGB',(ncols*thumbs[0].width,math.ceil(len(thumbs)/ncols)*h),'#DDDDEE')
   for j,t in enumerate(thumbs):sheet.paste(t,((j%ncols)*t.width,(j//ncols)*h))
   out=O/f'{platform}-{case}-{state}.png';sheet.save(out)
   manifest.append({'platform':platform,'case':case,'state':state,'contact_sheet':str(out),'complete':sc.get('complete'),'sources':sources})
(O/'contact-sheet-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('created',len(manifest),'sheets',sum(len(x['sources']) for x in manifest),'original frames')
