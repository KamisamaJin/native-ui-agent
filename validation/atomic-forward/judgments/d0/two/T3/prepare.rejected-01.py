import sys
sys.dont_write_bytecode=True
import json,pathlib,hashlib,math
from PIL import Image,ImageDraw,ImageFont
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
O=B/'judgments/d0/two/T3'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
allhash={};cases={};sheetindex=[]
font=ImageFont.truetype('/System/Library/Fonts/Monaco.ttf',12)
for p in sorted((B/'evaluation-inputs/d0/T3').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T3'));src,plat,case=key.split('/')
 data={n:json.loads((p/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']}
 inp=data['inputs'];root=B/inp['root'];obs=json.loads((B/inp['observation']).read_text())
 for q in p.glob('*.json'):allhash[str(q.relative_to(B))]=sha(q)
 for q in [B/inp['observation'],*(root/s['screenshot'] for s in obs['snapshots'])]:allhash[str(q.relative_to(B))]=sha(q)
 states={};groups={}
 for st in data['plan']['states']:
  found,complete,reason,cap=native_checks.bound_state_evidence(obs,st)
  states[st['id']]={'indices':[i for i,s in found],'complete':complete,'reason':reason,'capture':cap}
  for i,s in found:
   im=Image.open(root/s['screenshot']).convert('RGB');crop=None
   if plat=='ios':
    v=s['viewport'];app=s['app_frame'];sx=im.width/app['width'];sy=im.height/app['height'];crop=[round(v['x']*sx),round(v['y']*sy),round((v['x']+v['width'])*sx),round((v['y']+v['height'])*sy)];im=im.crop(crop)
   h=hashlib.sha256(im.tobytes()).hexdigest()
   if h not in groups:groups[h]={'image':im,'refs':[],'crop':crop}
   groups[h]['refs'].append({'state':st['id'],'index':i,'path':str((root/s['screenshot']).relative_to(B)),'sha256':sha(root/s['screenshot'])})
 tiles=list(groups.values());made=[]
 for n in range(0,len(tiles),8):
  subset=tiles[n:n+8];cw=400;ch=710;sheet=Image.new('RGB',(cw*4,ch*math.ceil(len(subset)/4)),(235,235,235));draw=ImageDraw.Draw(sheet)
  for j,g in enumerate(subset):
   x=(j%4)*cw;y=(j//4)*ch
   refs=g['refs'];label=f'{src}/{plat}/{case}\n'+', '.join(f"{r[\'state\']}:{r[\'index\']}"for r in refs)
   # labels wrap without changing identity; exact mapping also in index
   lines=[]
   for line in label.split('\n'):
    while len(line)>49:lines.append(line[:49]);line=line[49:]
    lines.append(line)
   draw.multiline_text((x+4,y+3),'\n'.join(lines[:6]),font=font,fill=(0,0,0),spacing=2)
   im=g['image'];im=im.resize((min(390,round(im.width*650/im.height)),650));sheet.paste(im,(x+(cw-im.width)//2,y+60))
  out=O/'contact-sheets'/key/f'{n//8:02d}.png';out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out);made.append(str(out.relative_to(O)))
  sheetindex.append({'sheet':str(out.relative_to(O)),'tiles':[{'refs':g['refs'],'crop_px':g['crop']}for g in subset]})
 cases[key]={'inputs':{k:v for k,v in inp.items()if k!='original_files'},'states':states,'failed':[{k:v for k,v in a.items()if k not in ['actual']}for a in data['automatic']['assertions']if a['status']=='failed'],'original_snapshots':len(obs['snapshots']),'selected_snapshot_count':sum(len(s['indices'])for s in states.values()),'unique_selected_viewport_pixels':len(tiles),'sheets':made,'environment_status':data['environment-check']['status']}
 print(key,len(tiles),'unique viewports;',len(made),'sheets')
(O/'evidence-index.json').write_text(json.dumps(cases,indent=2)+'\n')
(O/'contact-sheets/index.json').write_text(json.dumps(sheetindex,indent=2)+'\n')
(O/'input-hashes.json').write_text(json.dumps(allhash,indent=2)+'\n')
with (O/'commands.log').open('a')as f:f.write('Preparation: read all 5 required JSONs for all 8 cases; hash all input JSONs and original snapshot PNGs; frozen native_checks.bound_state_evidence per selected state; construct original viewport contact sheets without altering originals. See prepare.py. Prior exploratory commands: find input files; compact metadata; frozen evaluator documentation and source inspection; approved BRIEF/API/policy/reference read; original sample/reference PNG views. Two earlier broad JSON print attempts were truncated; replaced by scoped extraction; no judgment based on truncated data.\n')
