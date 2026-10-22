from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
O=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/judgments/final/one/T1')
r=json.loads((O/'evidence-inventory.json').read_text());coverage={}
for key,c in r.items():
 seen={};entries=[]
 for e in c['originals']:
  im=Image.open(e['path']).convert('RGB').crop(e['crop']);dig=hashlib.sha256(im.tobytes()).hexdigest()
  if dig in seen:
   seen[dig]['originals'].append({'path':e['path'],'indices':e['indices'],'sha256':e['sha256'],'state':e['state']});continue
  ent={'pixelSha256':dig,'originals':[{'path':e['path'],'indices':e['indices'],'sha256':e['sha256'],'state':e['state']}],'entry':e};seen[dig]=ent;entries.append(ent)
 width=c['input']['case'];nativew={'P1':390,'P2':248,'H1':312}[width];tw=310;th=round(600/nativew*300)+60;paths=[]
 for page in range(math.ceil(len(entries)/12)):
  batch=entries[page*12:page*12+12];cv=Image.new('RGB',(tw*4,th*3),'#ddd');d=ImageDraw.Draw(cv)
  for k,e in enumerate(batch):
   raw=e['entry'];im=Image.open(raw['path']).convert('RGB').crop(raw['crop']);im.thumbnail((300,th-60),Image.Resampling.LANCZOS);x=(k%4)*tw;y=(k//4)*th
   ix=[n for orig in e['originals'] for n in orig['indices']];d.multiline_text((x+2,y+1),f"{key}\nidx {','.join(map(str,ix))}",fill='black',spacing=0);cv.paste(im,(x+3,y+50))
  p=O/key/f'content-{page+1:02}.png';cv.save(p);paths.append(str(p.relative_to(O)))
 coverage[key]={'snapshotCount':c['snapshots'],'viewportDistinctImages':len(entries),'mapping':entries,'sheets':paths};print(key,len(entries),len(paths))
(O/'viewport-inspection-map.json').write_text(json.dumps(coverage,indent=2)+'\n')
