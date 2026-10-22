from pathlib import Path
from PIL import Image,ImageDraw
import json,math,textwrap
O=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/judgments/final/one/T1');B=O.parents[3]
r=json.loads((O/'viewport-inspection-map.json').read_text());inventory=json.loads((O/'evidence-inventory.json').read_text())
for key,c in r.items():
 obs=json.loads((B/inventory[key]['input']['observation']).read_text());entries=c['mapping'];tw=310;nativew={'P1':390,'P2':248,'H1':312}[inventory[key]['input']['case']];th=round(600/nativew*300)+60
 for page,path in enumerate(c['sheets']):
  p=O/path;im=Image.open(p).convert('RGB');draw=ImageDraw.Draw(im)
  for k,e in enumerate(entries[page*12:page*12+12]):
   groups={}
   for orig in e['originals']:
    for index in orig['indices']:groups.setdefault(obs['snapshots'][index]['state_id'],[]).append(index)
   e['stateIndexMapping']=groups
   x=(k%4)*tw;y=(k//4)*th;draw.rectangle((x,y,x+tw-1,y+49),fill='#ddd')
   label=key+'\n'+' / '.join(groups)+'\nidx '+','.join(str(n) for ns in groups.values() for n in ns)
   lines=[]
   for line in label.splitlines():lines+=textwrap.wrap(line,52) or ['']
   draw.multiline_text((x+2,y+1),'\n'.join(lines),fill='black',spacing=0)
  im.save(p)
(O/'viewport-inspection-map.json').write_text(json.dumps(r,indent=2)+'\n')
print('Relabeled all inspected viewport sheets with exact original state/index associations; viewport content unchanged.')
