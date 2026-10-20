from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
r=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
out=Path(__file__).parent/'review-artifacts';out.mkdir(exist_ok=True)
records=[]
for platform,case,part in [('ios','P1','own-corpora'),('ios','P2','own-retries'),('android','P1','own-corpora'),('android','P2','own-corpora')]:
 p=r/part/'unit-092e15/d0'/platform/case;d=json.loads((p/'observation.json').read_text())
 plan=json.loads((r/'submissions/unit-092e15/initial-agent-output/plans'/case/platform/'plan.json').read_text())
 def img(index):
  s=d['snapshots'][index];im=Image.open(p/s['screenshot']).convert('RGB')
  if platform=='ios':
   v=s['viewport'];scale=s.get('runtime',{}).get('screen_scale',3)
   im=im.crop((round(v['x']*scale),round(v['y']*scale),round((v['x']+v['width'])*scale),round((v['y']+v['height'])*scale)))
  return im
 def sheet(indices,name,labels=None,cols=4,width=300):
  tiles=[]
  for i in indices:
   im=img(i);im=im.resize((width,round(im.height*width/im.width)))
   tile=Image.new('RGB',(width,im.height+38),'#dddddd');tile.paste(im,(0,38));ImageDraw.Draw(tile).text((6,8),(labels or {}).get(i,f'{platform} {case} snapshot {i}'),fill='black');tiles.append(tile)
  height=max(x.height for x in tiles);result=Image.new('RGB',(cols*width,math.ceil(len(tiles)/cols)*height),'#aaaaaa')
  for n,t in enumerate(tiles): result.paste(t,((n%cols)*width,(n//cols)*height))
  dest=out/f'{platform}-{case}-{name}.png';result.save(dest);return str(dest)
 browse=next(s for s in d['state_captures'] if s['state_id']=='browse')
 full=sheet(browse['snapshot_indices'],'browse',cols=min(4,len(browse['snapshot_indices'])))
 selected=[];labels={}
 for state in plan['states']:
  sid=state['id'];a=state['after_action']
  candidates= browse['snapshot_indices'] if sid=='browse' else d['steps'][a]['observation_set']['snapshot_indices']
  good=[]
  for index in candidates:
   s=d['snapshots'][index]
   if platform=='ios':
    groups=[g for g in s['control_groups'] if g['selector'].get('identifier')=='enroll.reserve']
    visible=any(g.get('control',{}).get('fully_within_viewport',False) for g in groups)
   else:visible=any(n.get('identifier')=='enroll.reserve' and n.get('fully_visible') for n in s['nodes'])
   if visible:good.append(index)
  index=good[0] if good else None
  if index is not None:
   selected.append(index);labels[index]=f'{platform} {case} {sid} [{index}]'
  records.append({'platform':platform,'case':case,'state':sid,'snapshot_index':index,'available_fully_visible_reserve_indices':good,'binding':d['snapshots'][index]['binding'] if index is not None else None,'evidence':{'path':str(p/d['snapshots'][index]['screenshot']),'sha256':hashlib.sha256((p/d['snapshots'][index]['screenshot']).read_bytes()).hexdigest()} if index is not None else None})
 reserve=sheet(selected,'reserve-states',labels=labels,cols=3)
 print(full);print(reserve)
(out/'manual-image-index.json').write_text(json.dumps(records,indent=2)+'\n')
