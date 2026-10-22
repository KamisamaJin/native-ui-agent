from pathlib import Path
import json,sys,hashlib,math
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
O=B/'judgments/final/one/T1'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks
from PIL import Image,ImageDraw,ImageFont
records={}; hashes={}; sheets={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for case in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*')):
 key='/'.join(case.parts[-3:]); inp=json.loads((case/'inputs.json').read_text()); plan=json.loads((case/'plan.json').read_text());obs=json.loads((B/inp['observation']).read_text()); platform=inp['platform']
 states={}
 for st in plan['states']:
  found,complete,why,cap=native_checks.bound_state_evidence(obs,st)
  states[st['id']]={'indices':[i for i,s in found],'complete':complete,'reason':why,'binding':cap.get('binding') if cap else None}
  hashes.update({str(case/f):sha(case/f) for f in ['inputs.json','plan.json','catalog.json','automatic.json','environment-check.json']})
 entries=[]; bysha={}
 for ix,s in enumerate(obs['snapshots']):
  p=B/inp['root']/s['screenshot']; digest=sha(p);hashes[str(p)]=digest
  image=Image.open(p).convert('RGB'); size=image.size
  if platform=='ios':
   v=s['viewport'];app=s['app_frame'];xs=size[0]/app['width'];ys=size[1]/app['height'];crop=[round(v['x']*xs),round(v['y']*ys),round((v['x']+v['width'])*xs),round((v['y']+v['height'])*ys)]
  else:crop=[0,0,*size]
  # Exact PNG dedup retains every original index and source hash.
  if digest in bysha:bysha[digest]['indices'].append(ix);continue
  ent={'indices':[ix],'state':s['state_id'],'path':str(p),'sha256':digest,'originalSize':size,'crop':crop}
  bysha[digest]=ent;entries.append(ent)
  hashes[str(B/inp['observation'])]=sha(B/inp['observation'])
 outdir=O/key;outdir.mkdir(parents=True,exist_ok=True)
 sheetpaths=[]
 for page in range(math.ceil(len(entries)/12)):
  batch=entries[page*12:page*12+12];tileW=320;tileH=820
  canvas=Image.new('RGB',(tileW*4,tileH*3),'#e0e0e0');d=ImageDraw.Draw(canvas)
  for k,e in enumerate(batch):
   im=Image.open(e['path']).convert('RGB').crop(e['crop']);im.thumbnail((310,760),Image.Resampling.LANCZOS)
   x=(k%4)*tileW;y=(k//4)*tileH
   label=f"{key}\n{e['state']} idx {','.join(map(str,e['indices']))}"
   d.multiline_text((x+4,y+2),label,fill='black',spacing=1)
   canvas.paste(im,(x+5,y+45))
  p=outdir/f'contact-{page+1:02}.png';canvas.save(p);sheetpaths.append(str(p.relative_to(O)))
 records[key]={'input':{k:v for k,v in inp.items() if k!='original_files'},'states':states,'snapshots':len(obs['snapshots']),'uniqueOriginalPNGs':len(entries),'originals':entries,'contactSheets':sheetpaths}
 print(key,len(obs['snapshots']),len(entries),len(sheetpaths))
(O/'evidence-inventory.json').write_text(json.dumps(records,indent=2)+'\n')
(O/'input-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
