import pathlib,json,sys,hashlib,math
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
O=B/'judgments/d0/one/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
coverage={};hashes={};sheets=[]
for case in sorted((B/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=str(case.relative_to(B/'evaluation-inputs/d0/T2')); source,platform,cn=key.split('/')
 docs={n:json.loads((case/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']}
 for p in case.glob('*.json'):hashes[str(p.relative_to(B))]=sha(p)
 inputs=docs['inputs'];root=B/inputs['root'];obs=json.loads((B/inputs['observation']).read_text())
 hashes[inputs['observation']]=sha(B/inputs['observation'])
 assert hashes[inputs['observation']]==inputs['observation_sha256']
 for rel,expected in inputs['original_files'].items():
  p=B/rel
  if rel.startswith(('design-v2/T2/','common-corpora/T2/')) or rel.startswith(inputs['source_capsule']+'/'):
   hashes[rel]=sha(p)
   assert hashes[rel]==expected,(rel,hashes[rel],expected)
 coverage[key]={'automatic_counts':docs['automatic']['counts'],'environment':docs['environment-check']['status'],'states':{}}
 for state in docs['plan']['states']:
  found,complete,why,capture=native_checks.bound_state_evidence(obs,state)
  records=[];crops=[];height=0;scale=2
  for i,s in found:
   p=root/s['screenshot'];im=Image.open(p).convert('RGB');hashes[str(p.relative_to(B))]=sha(p)
   if platform=='ios':
    vp=s['viewport'];cf=s['runtime']['content_frame'];sc=s['runtime']['screen_scale'];x,y,w,h=vp['x'],vp['y'],vp['width'],vp['height'];offset=y-cf['y'];ch=cf['height'];rect=(x*sc,y*sc,(x+w)*sc,(y+h)*sc)
   else:
    w=s['logical_viewport_dp']['width'];h=s['logical_viewport_dp']['height'];offset=s['scroll_offset_dp'];ch=s['scroll_max_dp']+h;rect=(0,0,im.width,im.height)
   # Original viewport crop, no resynthesis; logical scale gives consistent comparison.
   crop=im.crop(tuple(round(z) for z in rect)).resize((round(w*scale),round(h*scale)),Image.Resampling.LANCZOS)
   crops.append((i,offset,crop));height=max(height,ch)
   records.append({'index':i,'screenshot':str(p.relative_to(B)),'sha256':sha(p),'offset':offset,'viewport_native':[w,h],'original_pixel_crop':rect})
  if not crops:
   coverage[key]['states'][state['id']]={'complete':complete,'reason':why,'frames':records};continue
  width=crops[0][2].width;strip=Image.new('RGB',(width,math.ceil(height*scale)),(255,0,255))
  for i,off,crop in crops:strip.paste(crop,(0,round(off*scale)))
  # Split original-derived full strip into readable successive 1300-logical-unit panels.
  panelh=2600;panels=[]
  for start in range(0,strip.height,panelh):
   part=strip.crop((0,start,width,min(strip.height,start+panelh)))
   panel=Image.new('RGB',(width+12,panelh+80),'white');panel.paste(part,(6,70));d=ImageDraw.Draw(panel)
   d.text((6,6),f'{source}/{platform}/{cn}/{state["id"]}',fill='black');d.text((6,24),f'original-derived y={start/2:g}..{min(strip.height,start+panelh)/2:g}',fill='black')
   relevant=[str(i) for i,o,c in crops if o*2<start+panelh and o*2+c.height>start]
   d.text((6,42),'indices '+','.join(relevant),fill='black');panels.append(panel)
  sheet=Image.new('RGB',(sum(x.width for x in panels),panelh+80),'white');at=0
  for p in panels:sheet.paste(p,(at,0));at+=p.width
  out=O/'sheets'/key/(state['id']+'.png');out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out)
  sheets.append(str(out.relative_to(O)))
  coverage[key]['states'][state['id']]={'complete':complete,'reason':why,'binding':capture.get('binding') if capture else None,'frames':records,'sheet':str(out.relative_to(O)),'content_native_height':height}
 save(O/'coverage.json',coverage);save(O/'input-hashes.json',hashes)
save(O/'sheets.json',sheets)
print(json.dumps({k:{s:{'complete':v['complete'],'indices':[x['index'] for x in v['frames']],'height':v['content_native_height']} for s,v in x['states'].items()} for k,x in coverage.items()},indent=2))
