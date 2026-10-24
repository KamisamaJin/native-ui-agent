import sys,json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=ROOT/'judgments/d0/one/T1'
sys.path.insert(0,str(ROOT/'candidate-v9/scripts'))
import native_checks
manifest=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  inp=ROOT/'evaluation-inputs/d0/T1/initial'/platform/case
  inputs=json.loads((inp/'inputs.json').read_text());plan=json.loads((inp/'plan.json').read_text());obs=json.loads((ROOT/inputs['observation']).read_text());raw=ROOT/inputs['raw']
  for state in plan['states']:
   found,complete,reason,capture=native_checks.bound_state_evidence(obs,state)
   unique={}
   for idx,snap in found:
    p=raw/snap['screenshot'];h=hashlib.sha256(p.read_bytes()).hexdigest();unique.setdefault(h,[]).append((idx,snap,p))
   rows=[]
   for h,items in unique.items():
    idx,s,p=items[0];im=Image.open(p).convert('RGB')
    if platform=='ios':
     a=s['app_frame'];v=s['viewport'];sx=im.width/a['width'];sy=im.height/a['height'];box=(round((v['x']-a['x'])*sx),round((v['y']-a['y'])*sy),round((v['x']+v['width']-a['x'])*sx),round((v['y']+v['height']-a['y'])*sy)); im=im.crop(box)
    else:box=(0,0,im.width,im.height)
    # One native unit -> one pixel in catalog. Original high-resolution files remain authoritative.
    im=im.resize((400 if case=='P1' else 280,600))
    rows.append((im,f'{platform}/{case} {state["id"]} idx '+','.join(str(i[0]) for i in items)))
    manifest.append({'platform':platform,'case':case,'state':state['id'],'indices':[i[0] for i in items],'original':str(p.relative_to(ROOT)),'sha256':h,'crop_original_px':box,'display_native_units':[im.width,im.height],'complete':complete,'binding':capture.get('binding')})
   for page in range(math.ceil(len(rows)/4)):
    chunk=rows[page*4:(page+1)*4];w=max(im.width for im,label in chunk);sheet=Image.new('RGB',(w*len(chunk),638),'#e0e0e0');d=ImageDraw.Draw(sheet)
    for j,(im,label) in enumerate(chunk):sheet.paste(im,(j*w,38));d.text((j*w+3,4),label,fill='black')
    dest=OUT/'sheets'/f'{platform}-{case}-{state["id"]}-{page}.png';dest.parent.mkdir(parents=True,exist_ok=True);sheet.save(dest)
  print(platform,case,'states',[(s['id'],[i for i,_ in native_checks.bound_state_evidence(obs,s)[0]])for s in plan['states']])
(OUT/'image-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# independent reference sheets
for case in ['P1','P2']:
 paths=sorted((ROOT/'design/T1/public/references'/case).glob('*.png'))
 for page in range(math.ceil(len(paths)/3)):
  chunk=paths[page*3:(page+1)*3];ims=[]
  for p in chunk:
   im=Image.open(p).convert('RGB');im.thumbnail((400,1500));ims.append((p,im))
  sheet=Image.new('RGB',(400*len(ims),max(im.height for p,im in ims)+30),'#e0e0e0');d=ImageDraw.Draw(sheet)
  for j,(p,im)in enumerate(ims):sheet.paste(im,(j*400,30));d.text((j*400+3,4),str(p.relative_to(ROOT)),fill='black')
  sheet.save(OUT/'sheets'/f'reference-{case}-{page}.png')
