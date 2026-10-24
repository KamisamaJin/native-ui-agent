import sys
sys.dont_write_bytecode=True
import json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=R/'judgments/d0/one/T1'
m=json.loads((O/'image-manifest.json').read_text());extra=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  inp=json.loads((R/'evaluation-inputs/d0/T1/initial'/platform/case/'inputs.json').read_text());obs=json.loads((R/inp['observation']).read_text());known={x['sha256']for x in m if x['platform']==platform and x['case']==case};images=[]
  for idx,s in enumerate(obs['snapshots']):
   p=R/inp['raw']/s['screenshot'];h=hashlib.sha256(p.read_bytes()).hexdigest();item={'platform':platform,'case':case,'index':idx,'state':s.get('state_id'),'original':str(p.relative_to(R)),'sha256':h,'identical_to_reviewed_state_image':h in known}
   extra.append(item)
   if h in known:continue
   known.add(h);im=Image.open(p).convert('RGB')
   if platform=='ios':
    a=s['app_frame'];v=s['viewport'];sx=im.width/a['width'];sy=im.height/a['height'];im=im.crop((round((v['x']-a['x'])*sx),round((v['y']-a['y'])*sy),round((v['x']+v['width']-a['x'])*sx),round((v['y']+v['height']-a['y'])*sy)))
   im=im.resize((400 if case=='P1'else 280,600));images.append((im,f'{platform}/{case} {s.get("state_id")} idx {idx}'))
  for page in range(math.ceil(len(images)/4)):
   chunk=images[page*4:(page+1)*4];w=max(i.width for i,l in chunk);sheet=Image.new('RGB',(w*len(chunk),638),'#e0e0e0');d=ImageDraw.Draw(sheet)
   for j,(im,label)in enumerate(chunk):sheet.paste(im,(j*w,38));d.text((j*w+3,4),label,fill='black')
   sheet.save(O/'sheets'/f'extra-{platform}-{case}-{page}.png')
  print(platform,case,'additional unique images',len(images))
(O/'all-snapshot-images.json').write_text(json.dumps(extra,indent=2)+'\n')
