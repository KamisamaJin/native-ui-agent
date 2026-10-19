#!/usr/bin/env python3
"""Independent raw packet indexer. Only explicitly permitted anonymous native data.

No implementation body reads; no bridge/tool reads. Derived images are lossless
viewport crops pasted at actual parent-scroll positions, with original coordinates.
"""
import json,pathlib,hashlib,sys,math
from PIL import Image,ImageDraw
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[6]
CTX=json.loads((HERE.parent/'contexts-D0.json').read_text())['contexts']
PLAN=json.loads((HERE.parent/'expanded-D0.json').read_text())['assessments']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def data(sub,pl,c):
 p=ROOT/'validation/tool-forward/evidence/d0'/sub/('ios' if pl=='apple' else pl)/c
 if not (p/'capture.json').is_file() or not (p/'portable-sha256.json').is_file():raise FileNotFoundError('Case not published complete: capture + portable hash inventory required')
 return p,load(p/'observation.json'),load(p/'capture.json'),load(p/'fixtures.json'),load(p/'manifest.json')
def state_data(sub,pl,cid):
 cx=CTX[cid];p,o,cap,fx,m=data(sub,pl,cx['caseId'])
 pr=next(x for x in cap['action_protocol'] if x['checkpoint']==cx['stateId'])
 ci=pr['capture_action_index']; ti=pr['trigger_action_index']
 step=o['steps'][ci];trigger=o['steps'][ti] if ti is not None else None
 sc=next((x for x in o.get('state_captures',[]) if x['state_id']==pr['native_state_id']),None)
 if sc:inds=sc['snapshot_indices']
 else:inds=[step['snapshot'] if pl=='android' else step['after']]
 snaps=[o['snapshots'][i] for i in inds]
 models=[fx['initial']]+fx.get('updates',[])
 model=models[pr['input_index']]
 model=model.get('model',model)
 equal=model==cx['model']
 # Root source seal and native manifest are correlated by actual content hashes,
 # without following raw manifest's cache/tool paths.
 seal=load(ROOT/'validation/tool-forward/implementations/d0'/sub/'manifest.json')
 source_hashes=m.get('source_hashes',{})
 wanted={pathlib.Path(k).name:v for k,v in seal['files'].items()}
 actual={pathlib.Path(k).name:v for k,v in source_hashes.items()}
 source_match={k:actual.get(k)==v for k,v in wanted.items() if k.endswith('.kt' if pl=='android' else '.swift')}
 return dict(path=p,observation=o,capture=cap,fixtures=fx,manifest=m,context=cx,protocol=pr,
             captureStep=step,triggerStep=trigger,stateCapture=sc,indices=inds,snapshots=snaps,
             fixtureEquals=equal,sourceMatch=source_match)
def image_info(pl,p,s):
 raw=p/s['screenshot']
 if p.resolve() not in raw.resolve().parents or raw.suffix.lower()!='.png':raise ValueError('Image is outside the permitted case PNG scope')
 im=Image.open(raw).convert('RGB')
 if pl=='android':
  vp=s['logical_viewport_dp'];sx=im.width/vp['width'];sy=im.height/vp['height']
  crop=(0,0,im.width,im.height);off=s['scroll_offset_dp'];height=s['scroll_max_dp']+vp['height']
 else:
  vp=s['viewport'];sx=sy=s['runtime']['screen_scale'];crop=tuple(round(v) for v in [vp['x']*sx,vp['y']*sy,(vp['x']+vp['width'])*sx,(vp['y']+vp['height'])*sy])
  off=vp['y']-s['runtime']['content_frame']['y'];height=s['runtime']['content_frame']['height']
 return raw,im,crop,sx,sy,off,height
def create_images(sub,pl,cid):
 d=state_data(sub,pl,cid); dest=HERE/sub;dest.mkdir(exist_ok=True)
 label=pl+'-'+cid.replace('/','--');index=[];out=None
 for i,s in zip(d['indices'],d['snapshots']):
  raw,im,crop,sx,sy,off,h=image_info(pl,d['path'],s)
  if out is None:out=Image.new('RGB',(crop[2]-crop[0],math.ceil(h*sy)),(255,0,255))
  y=round(off*sy);out.paste(im.crop(crop),(0,y))
  index.append(dict(observation=str(d['path']/'observation.json'),snapshotIndex=i,rawPath=str(raw),sha256=sha(raw),crop=list(crop),pasteY=y,scaleX=sx,scaleY=sy,offset=off))
 if not d['context']['fullVisualCheckpoint']:
  # Focused capture stays a viewport image; do not imply complete card coverage.
  raw,im,crop,sx,sy,off,h=image_info(pl,d['path'],d['snapshots'][-1]);out=im.crop(crop)
 out.save(dest/(label+'-native.png'))
 logical=out.resize((round(out.width/sx),round(out.height/sy)))
 logical.save(dest/(label+'-logical.png'))
 bands=[]
 # Multi-column navigation image, legible logical size. Native pixels remain saved.
 for y in range(0,logical.height,1300):
  end=min(y+1320,logical.height);bands.append((y,logical.crop((0,y,logical.width,end))))
 for start in range(0,len(bands),4):
  subset=bands[start:start+4];page=Image.new('RGB',(logical.width*len(subset),max(im.height for _,im in subset)+30),'#DDDDEE');draw=ImageDraw.Draw(page)
  for j,(y,im) in enumerate(subset):page.paste(im,(j*logical.width,30));draw.text((j*logical.width+4,6),f'{label} y={y}',fill='black')
  name=label+f'-bands-{start//4}.png';page.save(dest/name)
 write(dest/(label+'-image-index.json'),dict(state=cid,platform=pl,fullVisual=d['context']['fullVisualCheckpoint'],sourceMatch=d['sourceMatch'],fixtureEquals=d['fixtureEquals'],sources=index))
 return dict(label=label,pages=math.ceil(len(bands)/4),logicalSize=logical.size,fixtureEquals=d['fixtureEquals'],sourceMatch=d['sourceMatch'])
if __name__=='__main__':
 sub=sys.argv[1];mode=sys.argv[2] if len(sys.argv)>2 else 'full'
 results=[]
 for pl in ['android','apple']:
  for cid,cx in CTX.items():
   if mode=='full' and not cx['fullVisualCheckpoint']:continue
   try:results.append(create_images(sub,pl,cid))
   except FileNotFoundError:results.append(dict(label=pl+'-'+cid,status='pending'))
 write(HERE/sub/(mode+'-image-inventory.json'),results)
 print(json.dumps(results,indent=2))
