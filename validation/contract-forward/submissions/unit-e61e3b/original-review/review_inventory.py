from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
o=b/'cache/unit-e61e3b/agent-output'
roots=[('ios','P1',b/'own-corpora/unit-e61e3b/d0/ios/P1'),('ios','P2',b/'own-retries/unit-e61e3b/d0/ios/P2'),('android','P1',b/'own-corpora/unit-e61e3b/d0/android/P1'),('android','P2',b/'own-corpora/unit-e61e3b/d0/android/P2')]
inventory=[]
for p,c,d in roots:
 j=json.loads((d/'observation.json').read_text()); m=json.loads((d/'manifest.json').read_text())
 print(p,c,'status',j.get('status'),m.get('status'),'issues',j.get('issues'), 'configuration',j.get('configuration'))
 print('runtime',j.get('original_runtime'))
 print('captures',[{k:s.get(k) for k in ['state_id','after_action','snapshot_indices','complete']} for s in j['state_captures']])
 print('steps',[{'i':i,'state':s.get('state_id'),'outcome':s.get('outcome'),'before':s.get('before'),'after':s.get('after'),'immediate':s.get('immediate_after'),'dispatch':{k:s.get('dispatch',{}).get(k) for k in ['attempted','succeeded','method','enabled']},'callbacks':s.get('callback_delta'),'targets':len(s.get('observation_set',{}).get('targets',[]))} for i,s in enumerate(j['steps'])])
 shots=[]
 for cap in j['state_captures']:
  if cap['state_id']=='browse': shots+=cap['snapshot_indices']
 for state in json.loads((b/f'submissions/unit-e61e3b/initial-agent-output/plans/{c}/{p}/plan.json').read_text())['states']:
  if state['id']=='browse':continue
  step=j['steps'][state['after_action']]
  indices=step.get('observation_set',{}).get('snapshot_indices',[])
  if not indices:indices=[step.get('immediate_after',step.get('after'))]
  # Keep every captured post-action location, not just one potentially partial target.
  shots+=indices
 shots=list(dict.fromkeys(i for i in shots if isinstance(i,int)))
 for page,start in enumerate(range(0,len(shots),8)):
  group=shots[start:start+8]; thumbw=240; thumbh=540
  sheet=Image.new('RGB',(thumbw*4,thumbh*2),'#dddddd');draw=ImageDraw.Draw(sheet)
  for k,i in enumerate(group):
   s=j['snapshots'][i];im=Image.open(d/s['screenshot']).convert('RGB');im.thumbnail((236,510))
   x=(k%4)*thumbw;y=(k//4)*thumbh
   draw.text((x+4,y+3),f'{p} {c} #{i} {s.get("state_id",s.get("name",""))[:20]}',fill='black')
   sheet.paste(im,(x+2,y+25))
  dest=o/f'review-{p}-{c}-{page}.jpg';sheet.save(dest,quality=95)
  print('SHEET',dest,group)
 item={'platform':p,'case':c,'root':str(d),'contact_snapshot_indices':shots,'snapshots':[]}
 for i,s in enumerate(j['snapshots']):
  n=next((n for n in s.get('nodes',[]) if n.get('identifier')=='enroll.reserve'),None)
  if n:
   fact={k:n.get(k) for k in ['frame','bounds_dp','unclipped_bounds_dp','touch_bounds_dp','fully_visible','fully_within_viewport','intersects_viewport','image_bounds_px']}
  else:fact=None
  item['snapshots'].append({'index':i,'screenshot':str(d/s['screenshot']),'binding':s.get('binding'),'reserve':fact,'viewport':s.get('viewport_frame',s.get('logical_viewport_dp'))})
 inventory.append(item)
(o/'review-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
paths=[]
for p,c,d in roots:
 paths += [x for x in d.rglob('*') if x.is_file() and x.suffix in {'.json','.png','.log'}]
paths += [b/'cache/unit-e61e3b/alerttoast/Sources/AlertToast/WorkshopEnrollmentCard.swift',b/'cache/unit-e61e3b/reply/Reply/app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt']
paths += [x for x in (b/'submissions/unit-e61e3b/initial-agent-output/plans').rglob('*') if x.is_file()]
paths += [x for x in (b/'submissions/unit-e61e3b/own-checks/d0').rglob('*') if x.is_file()]
(o/'review-before-hashes.json').write_text(json.dumps({str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},indent=2)+'\n')
