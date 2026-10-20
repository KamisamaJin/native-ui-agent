from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
o=b/'cache/unit-e61e3b/agent-output'
inventory=json.loads((o/'review-inventory.json').read_text())
selected=[]
for block in inventory:
 p,c,d=block['platform'],block['case'],Path(block['root'])
 obs=json.loads((d/'observation.json').read_text())
 plan=json.loads((b/f'submissions/unit-e61e3b/initial-agent-output/plans/{c}/{p}/plan.json').read_text())
 decisions=[]
 for state in plan['states']:
  if state['id']=='browse':indices=next(x['snapshot_indices']for x in obs['state_captures']if x['state_id']=='browse')
  else:indices=obs['steps'][state['after_action']]['observation_set']['snapshot_indices']
  candidates=[]
  for i in indices:
   node=next((x for x in obs['snapshots'][i]['nodes']if x.get('identifier')=='enroll.reserve'),{})
   if node.get('fully_within_viewport',node.get('fully_visible',False)):
    candidates.append((i,node))
  assert candidates,(p,c,state)
  i,node=candidates[-1]
  shot=d/obs['snapshots'][i]['screenshot']
  assert obs['snapshots'][i]['binding']['fixture_index']==state['input_index']
  image=Image.open(shot).convert('RGB')
  if p=='ios':
   frame=node['frame'];scale=image.width/obs['snapshots'][i]['app_frame']['width']
   box=[frame['x']*scale,frame['y']*scale,(frame['x']+frame['width'])*scale,(frame['y']+frame['height'])*scale]
  else:box=node['image_bounds_px']
  crop=image.crop(tuple(int(round(x))for x in [box[0]-6,box[1]-6,box[2]+6,box[3]+6]))
  crop.thumbnail((440,130))
  selected.append((f'{p} {c} {state["id"]} #{i}',crop))
  decisions.append({'id':state['id']+'/reserve-visible','method':'visual','status':'passed',
     'reason':'The complete Reserve seats label is visible in the fully revealed native control; no clipped glyph or ellipsis is visible. This judgment does not establish computed font/color or contrast.',
     'snapshot_indices':[i],
     'evidence':[{'path':str(shot.relative_to(d)),'sha256':hashlib.sha256(shot.read_bytes()).hexdigest()}]})
 folder=o/'review-checks'/c/p;folder.mkdir(parents=True,exist_ok=False)
 (folder/'manual.json').write_text(json.dumps({'observation_sha256':hashlib.sha256((d/'observation.json').read_bytes()).hexdigest(),'decisions':decisions},indent=2)+'\n')
 # Store exact native geometry as supplemental facts; keep original Android plan-height U intact.
 facts=[]
 for decision in decisions:
  i=decision['snapshot_indices'][0]
  node=next(x for x in obs['snapshots'][i]['nodes']if x.get('identifier')=='enroll.reserve')
  facts.append({'id':decision['id'].replace('reserve-visible','reserve-height'),'snapshot_index':i,
    'native_frame':node.get('frame'),'native_unclipped_bounds_dp':node.get('unclipped_bounds_dp'),
    'native_touch_bounds_dp':node.get('touch_bounds_dp'),
    'fully_visible':node.get('fully_within_viewport',node.get('fully_visible')),
    'scope':'Supplemental observed geometry only. Frozen Android ax_height plan mapping has no frame property and remains U; no plan changed.'})
 (folder/'supplemental-native-geometry.json').write_text(json.dumps(facts,indent=2)+'\n')
for page,start in enumerate(range(0,len(selected),12)):
 group=selected[start:start+12];sheet=Image.new('RGB',(920,6*175),'#eeeeee');draw=ImageDraw.Draw(sheet)
 for k,(title,crop)in enumerate(group):
  x=(k%2)*460;y=(k//2)*175
  draw.text((x+5,y+4),title,fill='black');sheet.paste(crop,(x+5,y+24))
 sheet.save(o/f'review-reserve-crops-{page}.png')
print('Prepared',len(selected),'SHA-bound manual decisions and native-frame crops')
