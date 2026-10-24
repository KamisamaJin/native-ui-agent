from pathlib import Path
import json,hashlib,sys,time
from PIL import Image,ImageDraw
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=BASE/'judgments/d0/one/T2'
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE/'candidate-v9/scripts'))
import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'createdAtUnix':time.time(),'method':'Original PNG native-viewport crops, resized only for labelled contact sheets. Original paths, image bytes SHA, state/index, and exact crop retained. No source edits or SDK actions.','cases':{}}
for p in sorted((BASE/'evaluation-inputs/d0/T2').glob('*/*/*')):
 inp=json.loads((p/'inputs.json').read_text());raw=BASE/inp['raw'];obs=json.loads((BASE/inp['observation']).read_text());plan=json.loads((p/'plan.json').read_text());plat,case=p.parts[-2:];casekey=f'{plat}/{case}';entry={'observation':inp['observation'],'observation_sha256':sha(BASE/inp['observation']),'input_sha_matches':sha(BASE/inp['observation'])==inp['observation_sha256'],'states':{},'metadata_sha256':{n:sha(p/n) for n in ['inputs.json','plan.json','catalog.json','automatic.json','environment-check.json']}}
 for st in plan['states']:
  found,complete,reason,capture=native_checks.bound_state_evidence(obs,st);frames=[];sheet=Image.new('RGB',(4*410,((len(found)+3)//4)*645),'#c8c8c8');dr=ImageDraw.Draw(sheet)
  for pos,(i,s) in enumerate(found):
   imagepath=raw/s['screenshot'];im=Image.open(imagepath).convert('RGB');crop=(0,0,im.width,im.height)
   if plat=='ios':
    vp=s['viewport'];scale=im.width/s['app_frame']['width'];crop=tuple(round(v*scale) for v in [vp['x'],vp['y'],vp['x']+vp['width'],vp['y']+vp['height']]);im=im.crop(crop)
   h=600;w=round(im.width*h/im.height);im=im.resize((w,h),Image.Resampling.LANCZOS);x=(pos%4)*410;y=(pos//4)*645;sheet.paste(im,(x,y+40));dr.text((x+4,y+3),f'{plat}/{case} {st["id"]} index {i}',fill='black');dr.text((x+4,y+18),f'{imagepath.name[:43]}',fill='black');frames.append({'index':i,'original_path':str(imagepath),'sha256':sha(imagepath),'crop_pixels':crop,'binding':s['binding'],'screenshot':s['screenshot']})
  dest=OUT/'sheets'/plat/case/f'{st["id"]}.png';dest.parent.mkdir(parents=True,exist_ok=True);sheet.save(dest)
  entry['states'][st['id']]={'indices':[i for i,_ in found],'complete':complete,'coverage_reason':reason,'sheet':str(dest.relative_to(OUT)),'frames':frames}
 manifest['cases'][casekey]=entry
(OUT/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Created 40 state sheets and manifest; image count',sum(len(s['frames']) for c in manifest['cases'].values() for s in c['states'].values()))
