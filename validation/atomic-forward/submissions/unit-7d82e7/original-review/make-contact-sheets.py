import json,pathlib,math,hashlib
from PIL import Image,ImageDraw
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
out=pathlib.Path(__file__).resolve().parent
manifest=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  root=b/'own-corpora/unit-7d82e7/d0'/platform/case
  o=json.loads((root/'observation.json').read_text())
  for state in ['baseline','expanded','submitted']:
   cap=next(c for c in o['state_captures'] if c['state_id']==state)
   bands=[];last=0
   for pos,idx in enumerate(cap['snapshot_indices']):
    s=o['snapshots'][idx]; im=Image.open(root/s['screenshot']).convert('RGB')
    if platform=='ios':
     v=s['viewport']; a=s['app_frame']; scale=im.width/a['width']
     im=im.crop(tuple(round(x*scale) for x in [v['x'],v['y'],v['x']+v['width'],v['y']+v['height']]))
     start,end=cap['intervals'][pos]
    else:
     start=s['scroll_offset_dp'];end=start+600
    trim=max(0,last-start)
    if trim<600:
     band=im.crop((0,round(trim/600*im.height),im.width,im.height))
     band=band.resize((360,round(band.height*360/band.width)))
     bands.append((idx,band))
    last=max(last,end)
   height=sum(b.height for i,b in bands)
   segment=1500;cols=math.ceil(height/segment)
   canvas=Image.new('RGB',(cols*408,segment+40),(230,230,230));draw=ImageDraw.Draw(canvas)
   for col in range(cols):draw.text((col*408+4,5),f'{case} {platform} {state} | part {col+1}',fill='black')
   cursor=0
   for idx,band in bands:
    consumed=0
    while consumed<band.height:
     col=cursor//segment;y=cursor%segment;n=min(segment-y,band.height-consumed)
     canvas.paste(band.crop((0,consumed,360,consumed+n)),(col*408+46,y+35))
     draw.text((col*408+2,y+35),f'#{idx}',fill='black')
     cursor+=n;consumed+=n
   path=out/f'{case}-{platform}-{state}-contact.png';canvas.save(path)
   manifest.append({'case':case,'platform':platform,'state':state,'path':str(path),'snapshot_indices':cap['snapshot_indices'],'complete':cap['complete'],'method':'Original viewport bands in native interval order, overlapping top pixels omitted only after already shown; side labels identify original snapshot indices. No new SDK capture.'})
(out/'contact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('\n'.join(x['path'] for x in manifest))
