"""Paired raw-only state reconstruction. No main runtime grades or evidence used."""
import json,pathlib,hashlib,math,copy
from PIL import Image,ImageDraw
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
EVAL=HERE.parent
CTX=json.loads((EVAL/'contexts-D0.json').read_text())['contexts']
PLAN=json.loads((EVAL/'expanded-D0.json').read_text())['assessments']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def finite(v):return isinstance(v,(int,float)) and math.isfinite(v)
def data(sub,pl,case):
 p=ROOT/'validation/tool-forward/paired-evidence/d0'/('ios' if pl=='apple' else pl)/case
 assert (p/'capture.json').is_file() and (p/'portable-sha256.json').is_file()
 return p,load(p/'observation.json'),load(p/'capture.json'),load(p/'fixtures.json'),load(p/'manifest.json')
def after(st,pl):return st['snapshot'] if pl=='android' else st['after']
def delivered(st,pl):return st.get('type',st.get('action',{}).get('type'))=='tap' and (st.get('outcome')=='tapped' if pl=='apple' else st.get('execution')=='observed' and st.get('enabled') is True and st.get('matches')==1)
def modelof(fx,index):return ([fx['initial']]+fx.get('updates',[]))[index].get('model',([fx['initial']]+fx.get('updates',[]))[index])
def rawbind(s,pl):
 if pl=='android':return dict(s['binding'])
 rt=s['runtime'];return dict(fixture_index=rt['fixture_index'],instance=rt['instance'],pid=rt['pid'],callbackCount=len(s.get('callbacks',[])),callbackBufferSHA256=hashlib.sha256(json.dumps(s.get('callbacks',[]),sort_keys=True,separators=(',',':')).encode()).hexdigest())
def heading_frame(s,model):
 ns=[n for n in s['nodes'] if n.get('label')==model['heading'] and n.get('role_raw')==48 and all(finite(n.get('frame',{}).get(k)) for k in ['x','y','width','height'])]
 return ns[0]['frame'] if len(ns)==1 else None
def state_data(sub,pl,cid):
 cx=CTX[cid];p,o,cap,fx,m=data(sub,pl,cx['caseId']);pr=next(x for x in cap['action_protocol'] if x['checkpoint']==cx['stateId']);ci=pr['capture_action_index'];ti=pr['trigger_action_index'];anchor=after(o['steps'][ci],pl)
 barriers={0,len(o['snapshots'])}
 for st in o['steps']:
  if delivered(st,pl) or st.get('type',st.get('action',{}).get('type'))=='apply_next_fixture':barriers.add(after(st,pl))
 barriers=sorted(barriers);lo=max(x for x in barriers if x<=anchor);hi=min(x for x in barriers if x>anchor)
 binding=rawbind(o['snapshots'][anchor],pl)
 inds=[i for i in range(lo,hi) if rawbind(o['snapshots'][i],pl)==binding]
 assert anchor in inds
 # Full states may use actual scroll/reveal frames from the same no-delivery,
 # no-replacement, same input/callback epoch; focused pixel assertions use anchor only.
 pixinds=inds if cx['fullVisualCheckpoint'] else [anchor]
 model=modelof(fx,pr['input_index']);assert binding['fixture_index']==pr['input_index']
 snaps=[]
 for i in inds:
  s=copy.deepcopy(o['snapshots'][i]);s['binding']=rawbind(s,pl);s['_raw_index']=i
  if pl=='apple':
   hf=heading_frame(s,model);s['_heading_frame']=hf
  snaps.append(s)
 if pl=='apple':
  # Relative scroll displacement from the same actual heading leaf, not a source
  # layout constant or synthesized content-frame instrumentation.
  origin=next((s['_heading_frame']['y'] for s in snaps if s['_heading_frame']),None)
  for s in snaps:s['_relative_offset']=origin-s['_heading_frame']['y'] if origin is not None and s['_heading_frame'] else None
 wanted={pathlib.Path(k).name:v for k,v in load(ROOT/'validation/tool-forward/implementations/d0'/sub/'manifest.json')['files'].items()};actual={pathlib.Path(k).name:v for k,v in m['source_hashes'].items()};sm={k:actual.get(k)==v for k,v in wanted.items() if k.endswith('.kt' if pl=='android' else '.swift')}
 return dict(path=p,observation=o,capture=cap,fixtures=fx,manifest=m,context=cx,protocol=pr,captureStep=o['steps'][ci],triggerStep=o['steps'][ti] if ti is not None else None,stateCapture=None,indices=inds,snapshots=snaps,pixelIndices=pixinds,anchorIndex=anchor,epoch=dict(startInclusive=lo,endExclusive=hi,binding=binding,basis='Actual replacement/delivered-activation boundaries plus fixture index and complete callback buffer/revision; no current-collector runtime borrowed.'),fixtureEquals=model==cx['model'],sourceMatch=sm)
def image_info(pl,p,s):
 raw=p/s['screenshot'];assert p.resolve() in raw.resolve().parents and raw.suffix.lower()=='.png';im=Image.open(raw).convert('RGB')
 if pl=='android':
  vp=s['logical_viewport_dp'];sx=im.width/vp['width'];sy=im.height/vp['height'];crop=(0,0,im.width,im.height);off=s['scroll_offset_dp'];h=s['scroll_max_dp']+vp['height']
 else:
  vp=s['viewport'];sx=sy=s['runtime']['screen_scale'];crop=tuple(round(v) for v in [vp['x']*sx,vp['y']*sy,(vp['x']+vp['width'])*sx,(vp['y']+vp['height'])*sy]);off=s.get('_relative_offset');h=None
 return raw,im,crop,sx,sy,off,h

def create_images(sub,pl,cid):
 d=state_data(sub,pl,cid);dest=HERE/sub;dest.mkdir(exist_ok=True);label=pl+'-'+cid.replace('/','--');selected=[(i,s) for i,s in zip(d['indices'],d['snapshots']) if i in d['pixelIndices']]
 infos=[(i,s,*image_info(pl,d['path'],s)) for i,s in selected]
 # Navigation-only relative canvas; all gaps remain explicit magenta. Absolute
 # card top/bottom/readability must be independently read from actual PNGs.
 offsets=[x[-2] for x in infos if x[-2] is not None];base=min(offsets) if offsets else 0
 if pl=='android':height=max(x[-1] for x in infos)
 else:height=max((x[-2]-base+600 for x in infos if x[-2] is not None),default=600)
 sx=infos[0][5];sy=infos[0][6];w=infos[0][4][2]-infos[0][4][0];canvas=Image.new('RGB',(w,math.ceil(height*sy)),(255,0,255));index=[]
 for i,s,raw,im,crop,sx,sy,off,h in infos:
  if off is None:continue
  y=round((off if pl=='android' else off-base)*sy);canvas.paste(im.crop(crop),(0,y));index.append(dict(snapshotIndex=i,rawPath=str(raw),sha256=sha(raw),crop=crop,relativePasteY=y,relativeScrollOffset=off,scaleX=sx,scaleY=sy))
 canvas.save(dest/(label+'-native.png'));logical=canvas.resize((round(canvas.width/sx),round(canvas.height/sy)));logical.save(dest/(label+'-logical.png'));bands=[]
 for y in range(0,logical.height,1300):bands.append((y,logical.crop((0,y,logical.width,min(y+1320,logical.height)))))
 for start in range(0,len(bands),4):
  subset=bands[start:start+4];page=Image.new('RGB',(logical.width*len(subset),max(im.height for _,im in subset)+30),'#DDDDEE');draw=ImageDraw.Draw(page)
  for j,(y,im) in enumerate(subset):page.paste(im,(j*logical.width,30));draw.text((j*logical.width+3,4),label+' relativeY='+str(y),fill='black')
  page.save(dest/(label+'-bands-'+str(start//4)+'.png'))
 write(dest/(label+'-image-index.json'),dict(contextId=cid,platform=pl,anchorIndex=d['anchorIndex'],epoch=d['epoch'],pixelIndices=d['pixelIndices'],fixtureEquals=d['fixtureEquals'],sourceMatch=d['sourceMatch'],scope='Relative navigation only. Actual raw references are primary. Magenta is uncaptured area, not product pixels.',sources=index))
 return dict(contextId=cid,platform=pl,pages=math.ceil(len(bands)/4),logicalSize=logical.size,indices=d['pixelIndices'])
