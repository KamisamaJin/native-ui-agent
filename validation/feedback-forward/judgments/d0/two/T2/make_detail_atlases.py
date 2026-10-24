from pathlib import Path
import sys,json,math,hashlib
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/d0/two/T2';sys.path.insert(0,str(B/'candidate-v9/scripts'));import native_checks,native_pixels
manifest=[]
for plat in ['ios','android']:
 for case in ['P1','P2']:
  p=B/'evaluation-inputs/d0/T2/initial'/plat/case;inp=json.loads((p/'inputs.json').read_text());obs=json.loads((B/inp['observation']).read_text());plan=json.loads((p/'plan.json').read_text());atlas=Image.new('RGB',(1100,1500),'#ddd');dr=ImageDraw.Draw(atlas)
  for k,state in enumerate(plan['states']):
   found=native_checks.bound_state_evidence(obs,state)[0]
   for col,target in enumerate(['status','primary']):
    for i,s in found:
     r=native_checks.resolve(s,{'identifier':'audio.'+target},plat);n=r['control' if target=='primary' else 'semantic']
     if not n.get('fully_within_viewport',n.get('fully_visible')):continue
     path=B/inp['raw']/s['screenshot'];im=Image.open(path).convert('RGB');box,_=native_pixels.image_rectangle(s,n,plat,im.size);cropbox=(math.floor(box[0])-4,math.floor(box[1])-4,math.ceil(box[2])+4,math.ceil(box[3])+4);crop=im.crop(cropbox);crop.thumbnail((530,115));x=col*550;y=k*150;dr.text((x+4,y+3),f'{state["id"]}/{target}: original index {i}',fill='black');atlas.paste(crop,(x+4,y+25));manifest.append({'platform':plat,'case':case,'state':state['id'],'target':target,'index':i,'original':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop_px':cropbox,'native_control_or_semantic_box_px':box});break
  atlas.save(O/'inspection'/f'{plat}-{case}-details.png')
(O/'inspection/detail-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
