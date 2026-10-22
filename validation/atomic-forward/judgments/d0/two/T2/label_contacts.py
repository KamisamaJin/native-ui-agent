from pathlib import Path
import json
from PIL import Image,ImageDraw
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=R/'judgments/d0/two/T2';c=json.loads((O/'coverage.json').read_text())
for key,states in c.items():
 inp=json.loads((R/'evaluation-inputs/d0/T2'/key/'inputs.json').read_text());obs=json.loads((R/inp['observation']).read_text())
 for sid,st in states.items():
  p=O/st['contact_sheet'];im=Image.open(p).convert('RGB');d=ImageDraw.Draw(im);colw=round((390 if key.endswith('P1') else 248)*1.5)+12;cols=im.width//colw
  for col in range(cols):
   start=col*750;end=(col+1)*750;inds=[]
   for n in st['indices']:
    s=obs['snapshots'][n];off=s['viewport']['y']-s['runtime']['content_frame']['y'] if inp['platform']=='ios' else s['scroll_offset_dp']
    if off<end and off+600>start:inds.append(n)
   d.rectangle((col*colw,0,(col+1)*colw,22),fill='#dddddd');d.text((col*colw+4,6),'Original indices: '+','.join(map(str,inds)),fill='black')
  im.save(p)
print('Labeled all 56 sheets with original source indices; only header changed.')
print('Selected bound frames',sum(len(st['indices']) for states in c.values() for st in states.values()))
