import pathlib,json,hashlib,sys,math
from PIL import Image,ImageDraw
R=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=R/'judgments/d0/two/T2'
sys.path.insert(0,str(R/'candidate-v8/scripts'));import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
index={}; hashes={}; coverage={}
for p in sorted((R/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=str(p.relative_to(R/'evaluation-inputs/d0/T2'));i=json.loads((p/'inputs.json').read_text());o=json.loads((R/i['observation']).read_text());pl=json.loads((p/'plan.json').read_text())
 for n in ['inputs','plan','catalog','automatic','environment-check']:
  f=p/(n+'.json');hashes[str(f.relative_to(R))]=sha(f);json.loads(f.read_text())
 # All explicitly supplied originals, including source capsule files, are hashed without interpretation of unrelated files.
 for rel,expected in i['original_files'].items():
  f=R/rel
  if f.is_file():hashes[rel]=sha(f)
 hashes[i['observation']]=sha(R/i['observation'])
 index[key]=[];coverage[key]={}
 for sn,s in enumerate(o['snapshots']):index[key].append({'snapshot_index':sn,'state':s.get('state_id'),'path':str(pathlib.Path(i['root'])/s['screenshot']),'sha256':sha(R/i['root']/s['screenshot']),'binding':s.get('binding'),'capture_consistent':s.get('capture_consistent')})
 for st in pl['states']:
  frames,complete,reason,cap=native_checks.bound_state_evidence(o,st)
  coverage[key][st['id']]={'indices':[n for n,s in frames],'complete':complete,'reason':reason,'capture':cap}
  if not frames:continue
  parts=[];scale=1.5
  for n,s in frames:
   raw=Image.open(R/i['root']/s['screenshot']).convert('RGB')
   if i['platform']=='ios':
    vp=s['viewport'];ns=s['screenshot_pixels']['width']/s['app_frame']['width'];left=round(vp['x']*ns);top=round(vp['y']*ns);wide=round(vp['width']*ns);h=round(vp['height']*ns);off=vp['y']-s['runtime']['content_frame']['y'];height=s['runtime']['content_frame']['height'];logicalw=vp['width']
    crop=raw.crop((left,top,left+wide,top+h))
   else:
    logicalw=s['logical_viewport_dp']['width'];off=s['scroll_offset_dp'];height=s['scroll_max_dp']+s['viewport_height_dp'];crop=raw
   crop=crop.resize((round(logicalw*scale),round(600*scale)))
   parts.append((off,n,crop))
  w=parts[0][2].width;strip=Image.new('RGB',(w,math.ceil(height*scale)),(255,0,255));d=ImageDraw.Draw(strip)
  for off,n,crop in parts:strip.paste(crop,(0,round(off*scale)))
  ch=1125;cols=math.ceil(strip.height/ch);sheet=Image.new('RGB',((w+12)*cols,1180),'#dddddd');sd=ImageDraw.Draw(sheet)
  for c in range(cols):
   sheet.paste(strip.crop((0,c*ch,w,min((c+1)*ch,strip.height))),(c*(w+12),55));sd.text((c*(w+12)+4,25),f'{key} / {st["id"]}\ncontent y={c*750}..{min((c+1)*750,round(height,1))}',fill='black')
  target=OUT/'contact-sheets'/key/(st['id']+'.png');target.parent.mkdir(parents=True,exist_ok=True);sheet.save(target)
  coverage[key][st['id']]['contact_sheet']=str(target.relative_to(OUT));coverage[key][st['id']]['composition']='Original viewport crops, native offset placement at 1.5 image px/logical unit; overlapping pixels overwritten by later coherent frame. Columns are consecutive 750 logical units. All originals retained at referenced paths.'
(OUT/'input-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n');(OUT/'original-index.json').write_text(json.dumps(index,indent=2)+'\n');(OUT/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
print('Created',sum(len(c) for c in coverage.values()),'state contact sheets;',sum(len(v) for v in index.values()),'original PNG references;',len(hashes),'input hashes.')
