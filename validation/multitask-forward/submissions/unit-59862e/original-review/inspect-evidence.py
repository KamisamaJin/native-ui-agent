import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
w=Path(__file__).resolve().parents[2];out=w/'agent-output/review';base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
seal=json.loads((w/'agent-output/plans-seal.json').read_text())
checks=[]
for file in seal['sources']+seal['plansActionsAndScripts']:
 p=w/file['path'];actual=hashlib.sha256(p.read_bytes()).hexdigest();checks.append({'path':str(p),'expectedSHA256':file['sha256'],'actualSHA256':actual,'identical':file['sha256']==actual})
(out/'immutability-before.json').write_text(json.dumps(checks,indent=2)+'\n')
index=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  root=base/'own-corpora/unit-59862e/d0'/platform/case
  o=json.loads((root/'observation.json').read_text())
  r=json.loads((base/'submissions/unit-59862e/own-checks/d0'/case/platform/'report.json').read_text())
  print(case,platform,r['counts'],'F',r['failed_assertion_ids'])
  for a in r['assertions']:
   if a['status']=='failed':print(a['id'],[v.get('value',v) for v in a['actual']],a.get('snapshot_indices'))
  for state in ['loaded','reasoned','advanced','classified','submitted','replaced']:
   capture=next(x for x in o['state_captures'] if x['state_id']==state)
   snaps=[o['snapshots'][i] for i in capture['snapshot_indices']]
   frames=[]
   for i,s in zip(capture['snapshot_indices'],snaps):
    img=Image.open(root/s['screenshot']).convert('RGB')
    if platform=='ios':
     vp=s['viewport']; scale=s['screenshot_pixels']['width']/s['app_frame']['width']
     img=img.crop(tuple(round(v*scale) for v in [vp['x'],vp['y'],vp['x']+vp['width'],vp['y']+vp['height']]))
     offset=vp['y']-s['runtime']['content_frame']['y']; width=round(vp['width']); height=round(vp['height'])
    else:
     offset=s['scroll_offset_dp'];width=round(s['logical_viewport_dp']['width']);height=600
    img=img.resize((width,height))
    frames.append((i,img,round(offset),root/s['screenshot']))
   height=max(offset+img.height for _,img,offset,_ in frames)
   merged=Image.new('RGB',(frames[0][1].width,height),'#808080')
   for _,img,offset,_ in frames:merged.paste(img,(0,offset))
   dest=out/f'{platform}-{case}-{state}.png';merged.save(dest)
   index.append({'case':case,'platform':platform,'state':state,'path':str(dest),'original_snapshot_indices':capture['snapshot_indices'],'complete':capture['complete'],'originals':[{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for _,_,_,path in frames]})
(out/'image-index.json').write_text(json.dumps(index,indent=2)+'\n')
print('immutability',all(x['identical'] for x in checks),'images',len(index))
