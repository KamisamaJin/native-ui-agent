#!/usr/bin/env python3
"""Make a labelled index of original native frames; never alter raw images."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
o=json.loads((a.capture/'observation.json').read_text())
indices=[0]+[s['immediate_after'] for s in o.get('steps',[]) if 'immediate_after' in s]+[i for s in o.get('steps',[]) for i in s.get('observation_set',{}).get('snapshot_indices',[])]
indices=list(dict.fromkeys(indices));cards=[]
for i in indices:
 im=Image.open(a.capture/o['snapshots'][i]['screenshot']).convert('RGB');im.thumbnail((195,350))
 c=Image.new('RGB',(205,380),'white');c.paste(im,(5,25));ImageDraw.Draw(c).text((5,4),f'snapshot {i}',fill='black');cards.append(c)
out=Image.new('RGB',(205*4,380*((len(cards)+3)//4)),'#cccccc')
for n,c in enumerate(cards):out.paste(c,(n%4*205,n//4*380))
a.output.parent.mkdir(parents=True,exist_ok=True);out.save(a.output)
print(json.dumps({'frames':len(o['snapshots']),'contact_frames':indices,'output':str(a.output)}))
