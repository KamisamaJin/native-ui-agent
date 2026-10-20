from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
out=Path(__file__).resolve().parent
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/own-corpora/unit-ba8b2b/d0')
manifest=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  run=base/platform/case;obs=json.loads((run/'observation.json').read_text())
  for state in ['loaded','reasoned','advanced','classified','submitted','replaced']:
   capture=next(s for s in obs['state_captures'] if s['state_id']==state)
   indices=capture['snapshot_indices'];thumbs=[]
   for i in indices:
    snap=obs['snapshots'][i];path=run/snap['screenshot'];im=Image.open(path).convert('RGB')
    if platform=='ios':
     scale=im.width/snap['app_frame']['width'];v=snap['viewport'];im=im.crop(tuple(round(v[k]*scale) for k in ['x','y'])+tuple(round((v[a]+v[b])*scale) for a,b in [('x','width'),('y','height')]))
    im=im.resize((320,round(im.height*320/im.width)))
    tile=Image.new('RGB',(320,im.height+30),'#dddddd');tile.paste(im,(0,30));ImageDraw.Draw(tile).text((4,5),f'{case} {platform} {state} #{i}',fill='black');thumbs.append(tile)
    manifest.append({'case':case,'platform':platform,'state':state,'index':i,'original':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
   cols=min(3,len(thumbs));rows=(len(thumbs)+cols-1)//cols;h=max(im.height for im in thumbs)
   sheet=Image.new('RGB',(cols*320,rows*h),'#aaaaaa')
   for j,im in enumerate(thumbs):sheet.paste(im,((j%cols)*320,(j//cols)*h))
   sheet.save(out/f'{case}-{platform}-{state}.png')
(out/'contact-sheet-index.json').write_text(json.dumps(manifest,indent=2)+'\n')
