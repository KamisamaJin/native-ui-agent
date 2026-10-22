from pathlib import Path
from PIL import Image
import json,math,hashlib,time
O=Path(__file__).resolve().parent
C=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/own-corpora/unit-99c640/d0')
D=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public')
policy=json.loads((D/'policy.json').read_text());reference=json.loads((D/'reference.json').read_text())
results=[];start=time.time()
for platform in ['ios','android']:
 for case in ['P1','P2']:
  base=C/platform/case;obs=json.loads((base/'observation.json').read_text())
  for state in ['baseline','selected','expanded','blocked','replaced','reselected','submitted']:
   cap=next(c for c in obs['state_captures'] if c['state_id']==state)
   for atom in policy['atoms']:
    if atom['method']!='native_pixels':continue
    rule=atom['rule_id'];target={'component-canvas-color':'canvas','notice-surface-color':'notice','primary-surface-color':'submit'}[rule]
    expected=(reference['cases'][case]['states'][state]['primaryColor'] if target=='submit' else reference['cases'][case]['colors'][target])
    value=expected['value'];rgba=tuple(int(value[i:i+2],16) for i in [3,5,7])+tuple([int(value[1:3],16)])
    samples=[]
    for index in cap['snapshot_indices']:
     s=obs['snapshots'][index];nodes=[n for n in s['nodes'] if n.get('identifier')=='workshop.'+target]
     if len(nodes)!=1:continue
     n=nodes[0];sp=atom['sampling'];p=base/s['screenshot']
     if sp['visibility']=='fully_visible' and not n.get('fully_visible',n.get('fully_within_viewport',False)):continue
     im=Image.open(p).convert('RGBA')
     if platform=='ios':
      f=n['frame'];sc=im.width/s['app_frame']['width'];box=[f['x']*sc,f['y']*sc,(f['x']+f['width'])*sc,(f['y']+f['height'])*sc]
      v=s['viewport'];visible=[v['x']*sc,v['y']*sc,(v['x']+v['width'])*sc,(v['y']+v['height'])*sc]
     else:box=n['image_bounds_px'];visible=[0,0,im.width,im.height]
     r=sp['region'];bw=box[2]-box[0];bh=box[3]-box[1]
     q=[max(box[0]+r[0]*bw,visible[0],0),max(box[1]+r[1]*bh,visible[1],0),min(box[0]+r[2]*bw,visible[2],im.width),min(box[1]+r[3]*bh,visible[3],im.height)]
     q=[math.ceil(q[0]),math.ceil(q[1]),math.floor(q[2]),math.floor(q[3])]
     if q[2]<=q[0] or q[3]<=q[1]:continue
     pixels=list(im.crop(tuple(q)).getdata());count=len(pixels)
     if count<sp['minimum_pixels']:continue
     support=sum(px==rgba for px in pixels)/count
     samples.append({'snapshot_index':index,'image':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sample_box_px':q,'pixel_count':count,'support':support,'satisfies_policy':support>=sp['minimum_support']})
    results.append({'platform':platform,'case':case,'state':state,'requirement_id':rule,'expected':value,'unit':expected['unit'],'status':'passed' if samples and all(s['satisfies_policy'] for s in samples) else 'unassessed','samples':samples,'policy':atom,'reason':'Original semantic boxes projected to original image, exact RGBA policy strip only; no re-render or tolerance edits.'})
(O/'pixel-review.json').write_text(json.dumps({'startedAtUnix':start,'finishedAtUnix':time.time(),'results':results},indent=2)+'\n')
print('color policy review',len(results),'checks', {s:sum(r['status']==s for r in results) for s in ['passed','unassessed']})
for r in results:
 if r['status']!='passed':print(r['case'],r['platform'],r['state'],r['requirement_id'],[(s['snapshot_index'],s['support']) for s in r['samples']])
