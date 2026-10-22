import json,pathlib,hashlib,math
from PIL import Image,ImageDraw,ImageFont
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
out=root/'judgments/d0/two/T1'
e=json.loads((out/'state-evidence.json').read_text())
manifest={};hashes={};font=ImageFont.truetype('/System/Library/Fonts/Monaco.ttf',11)
for key,case in e.items():
 inp=json.loads((root/'evaluation-inputs/d0/T1'/key/'inputs.json').read_text());base=root/inp['root'];obs=json.loads((root/inp['observation']).read_text());platform=inp['platform']
 for file in (root/'evaluation-inputs/d0/T1'/key).glob('*.json'):hashes[str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
 for p,h in inp['original_files'].items():
  p=root/p
  if p.is_file():hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 dest=out/key/'visuals';dest.mkdir(parents=True,exist_ok=True)
 for state,info in case['states'].items():
  entries=[]
  for idx in info['indices']:
   snap=obs['snapshots'][idx];im=Image.open(base/snap['screenshot']).convert('RGB')
   if platform=='ios':
    vp=snap['viewport'];content=snap['runtime']['content_frame'];scale=snap['runtime']['actual_environment']['display_scale'];x,y,w,h=[vp[k] for k in ['x','y','width','height']];offset=vp['y']-content['y'];total=content['height']
    crop=im.crop((round(x*scale),round(y*scale),round((x+w)*scale),round((y+h)*scale)))
   else:
    w=snap['logical_viewport_dp']['width'];h=snap['viewport_height_dp'];offset=snap['scroll_offset_dp'];total=snap['scroll_max_dp']+h;crop=im
   entries.append((idx,offset,total,crop.resize((round(w),round(h)),Image.Resampling.LANCZOS)))
  if not entries:continue
  w=entries[0][3].width;total=math.ceil(max(v[2] for v in entries));strip=Image.new('RGB',(w,total),'#ff00ff');end=0
  for idx,offset,_,crop in sorted(entries,key=lambda x:x[1]):
   y=round(offset);start=max(0,end-y);take=min(crop.height,total-y)
   if take>start:strip.paste(crop.crop((0,start,w,take)),(0,y+start));end=max(end,y+take)
  panelh=1700;cols=math.ceil(total/panelh);labelh=64;sheet=Image.new('RGB',((w+10)*cols,panelh+labelh),'#ddd');draw=ImageDraw.Draw(sheet)
  for col in range(cols):
   draw.text(((w+10)*col+3,3),key+' '+state,fill='black',font=font)
   draw.text(((w+10)*col+3,18),'native y '+str(col*panelh),fill='black',font=font)
   ids=[idx for idx,o,_,c in entries if o<((col+1)*panelh) and o+c.height>col*panelh]
   draw.text(((w+10)*col+3,33),'indices '+','.join(map(str,ids[:8])),fill='black',font=font)
   if len(ids)>8:draw.text(((w+10)*col+3,46),','.join(map(str,ids[8:])),fill='black',font=font)
   sheet.paste(strip.crop((0,col*panelh,w,min(total,(col+1)*panelh))),((w+10)*col,labelh))
  path=dest/(state+'-content.png');sheet.save(path)
  manifest[str(path.relative_to(out))]={'case':key,'state':state,'indices':info['indices'],'native_content_height':total,'complete':info['complete'],'construction':'Original viewport PNG pixels cropped using native viewport, resampled to native units and assembled by original scroll offsets. Overlap is deduplicated; original images unchanged.','originals':[{'index':idx,'path':str(base/obs['snapshots'][idx]['screenshot']),'sha256':hashlib.sha256((base/obs['snapshots'][idx]['screenshot']).read_bytes()).hexdigest()} for idx in info['indices']]}
(out/'visual-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'input-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('Created',len(manifest),'whole-state original-PNG contact sheets; hashed',len(hashes),'inputs')
