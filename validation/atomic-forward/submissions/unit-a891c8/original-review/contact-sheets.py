from pathlib import Path
import hashlib,json,math,time,traceback
started=time.time()
o=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-a891c8/agent-output/review')
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/own-corpora/unit-a891c8/d0')
record={'command':'python3 agent-output/review/contact-sheets.py','startedAtUnix':started}
try:
 from PIL import Image,ImageDraw
 entries=[]
 for case in ['P1','P2']:
  for platform in ['ios','android']:
   base=b/platform/case;d=json.loads((base/'observation.json').read_text())
   for state in ['baseline','expanded','submitted']:
    capture=next(s for s in d['state_captures'] if s['state_id']==state)
    indices=capture['snapshot_indices']
    for page in range(math.ceil(len(indices)/8)):
     subset=indices[page*8:page*8+8];cols=min(4,len(subset));rows=math.ceil(len(subset)/cols)
     width=300 if case=='P1' else 248;height=round(width*(600/(390 if case=='P1' else 248)))
     sheet=Image.new('RGB',(cols*(width+12)+12,rows*(height+48)+12),'#dddddd');draw=ImageDraw.Draw(sheet)
     sources=[]
     for j,index in enumerate(subset):
      snap=d['snapshots'][index];path=base/snap['screenshot'];img=Image.open(path).convert('RGB')
      crop=None
      if platform=='ios':
       v=snap['viewport'];scale=img.width/snap['app_frame']['width'];crop=tuple(round(n*scale) for n in [v['x'],v['y'],v['x']+v['width'],v['y']+v['height']]);img=img.crop(crop)
      img=img.resize((width,height))
      x=12+(j%cols)*(width+12);y=12+(j//cols)*(height+48)
      draw.text((x,y),f'{case} {platform} {state} snapshot {index}',fill='black')
      draw.text((x,y+14),snap.get('name','')[:40],fill='black');sheet.paste(img,(x,y+36))
      sources.append({'snapshot_index':index,'state':state,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop_pixels':crop})
     target=o/f'{case}-{platform}-{state}-{page+1}.png';sheet.save(target)
     entries.append({'path':str(target),'case':case,'platform':platform,'state':state,'sources':sources})
 (o/'contact-manifest.json').write_text(json.dumps(entries,indent=2)+'\n')
 record.update({'returncode':0,'sheets':len(entries),'originals':sum(len(e['sources']) for e in entries)})
 print(json.dumps(record))
except Exception:
 record.update({'returncode':1,'error':traceback.format_exc()});print(record['error']);raise
finally:
 record['finishedAtUnix']=time.time();(o/'contact-command.json').write_text(json.dumps(record,indent=2)+'\n')
