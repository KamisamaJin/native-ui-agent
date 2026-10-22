import pathlib,json,hashlib,sys,math,collections
from PIL import Image,ImageDraw,ImageFont
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward'); OUT=B/'judgments/final/one/T3'
sys.dont_write_bytecode=True
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
records={};hashes={};sheets=[]
for ip in sorted((B/'evaluation-inputs/final/T3').glob('*/*/*/inputs.json')):
 key=str(ip.parent.relative_to(B/'evaluation-inputs/final/T3')); inp=json.loads(ip.read_text()); obsfile=B/inp['observation']; obs=json.loads(obsfile.read_text()); plan=json.loads((ip.parent/'plan.json').read_text());cat=json.loads((ip.parent/'catalog.json').read_text());auto=json.loads((ip.parent/'automatic.json').read_text());env=json.loads((ip.parent/'environment-check.json').read_text()); root=B/inp['root']
 for fp in ip.parent.glob('*.json'):hashes[str(fp.relative_to(B))]=sha(fp)
 hashes[inp['observation']]=sha(obsfile)
 states={}; allpanels=[]
 for s in plan['states']:
  found,complete,reason,cap=native_checks.bound_state_evidence(obs,s)
  frames=[]
  if inp['platform']=='ios':
   width=round(found[0][1]['viewport']['width']); height=math.ceil(max(x['runtime']['content_frame']['height'] for _,x in found))
  else:width=round(found[0][1]['logical_viewport_dp']['width']);height=math.ceil(max(x['scroll_max_dp']+x['viewport_height_dp'] for _,x in found))
  strip=Image.new('RGB',(width,height),(255,0,255));sm=[]
  for idx,snap in sorted(found,key=lambda x:(x[1].get('scroll_offset_dp',x[1].get('viewport',{}).get('y',0)-x[1].get('runtime',{}).get('content_frame',{}).get('y',0)))):
   fp=root/snap['screenshot']; hashes[str(fp.relative_to(B))]=sha(fp); im=Image.open(fp).convert('RGB')
   if inp['platform']=='ios':
    vp=snap['viewport']; app=snap['app_frame'];sx=im.width/app['width'];sy=im.height/app['height'];box=[round(vp['x']*sx),round(vp['y']*sy),round((vp['x']+vp['width'])*sx),round((vp['y']+vp['height'])*sy)]; offset=vp['y']-snap['runtime']['content_frame']['y']
   else:box=[0,0,im.width,im.height];offset=snap['scroll_offset_dp']
   crop=im.crop(box).resize((width,600),Image.Resampling.LANCZOS)
   strip.paste(crop,(0,round(offset)));sm.append({'index':idx,'screenshot':str(fp.relative_to(B)),'sha256':sha(fp),'offset':offset,'viewport_original_crop':box})
  panels=[]
  for n,y in enumerate(range(0,height,850)):
   h=min(900,height-y); cn=Image.new('RGB',(width,940),'#eeeeee');cn.paste(strip.crop((0,y,width,y+h)),(0,40));draw=ImageDraw.Draw(cn); inds=[f['index'] for f in sm if f['offset']<y+900 and f['offset']+600>y];label=f'{key} {s["id"]}\ny={y} idx={inds}'
   draw.multiline_text((2,2),label,font=font,fill='black');panels.append({'image':cn,'y':y,'indices':inds})
  states[s['id']]={'indices':[i for i,_ in found],'complete':complete,'reason':reason,'binding':cap.get('binding') if cap else None,'height':height,'frames':sm,'panels':[]}
  # One or more sheets per entire state; no cross-state evidence is merged.
  for n in range(0,len(panels),5):
   group=panels[n:n+5]; sheet=Image.new('RGB',(sum(p['image'].width+8 for p in group),940),'#dddddd');x=0
   for panel in group:sheet.paste(panel['image'],(x,0));x+=panel['image'].width+8
   path=OUT/'contacts'/key/f'{s["id"]}-{n//5:02}.png';path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)
   info={'path':str(path.relative_to(OUT)),'state':s['id'],'panels':[{'y':z['y'],'indices':z['indices']} for z in group]};states[s['id']]['panels'].append(info);sheets.append(info)
 records[key]={'inputs':{k:v for k,v in inp.items() if k!='original_files'},'states':states,'automatic_counts':auto['counts'],'automatic_F':auto['failed_assertion_ids'],'environment_status':env['status'],'environment_frame_statuses':dict(collections.Counter(z['status'] for z in env.get('frames',[]))),'qualitative_rows':[{k:r[k] for k in ('id','review_id','proposition')} for r in cat['rows'] if r['method']=='visual']}
 for sn in obs['snapshots']:
  fp=root/sn['screenshot'];hashes[str(fp.relative_to(B))]=sha(fp)
 for rel,expected in inp['original_files'].items():
  # original sources, approved design and common corpora only; exclude submit seal/license outside capsule.
  if rel.startswith(('design-v2/T3/',inp['root']+'/',inp['source_capsule']+'/')):
   fp=B/rel
   if fp.is_file():hashes[rel]=sha(fp)
(OUT/'evidence-index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'input-hashes.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
print('cases',len(records),'sheets',len(sheets),'hashed files',len(hashes))
for key,rec in records.items(): print(key,[(s,r['complete'],r['height']) for s,r in rec['states'].items()])
