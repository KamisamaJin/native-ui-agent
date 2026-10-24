import json,pathlib,sys,math
from PIL import Image,ImageDraw
base=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
for platform in ['ios','android']:
 for case in ['P1','P2']:
  p=base/platform/case/'native/observation.json'
  if not p.exists():continue
  o=json.load(open(p));groups={}
  for st in o['state_captures']:
   if st['state_id'] in ['overview','permitted','requested','requested-closed','replaced']:groups[st['state_id']]=st['snapshot_indices']
  for state in ['opened','cleared','restored','held-choice','competing-gates']:
   st=next((st for st in o['state_captures'] if st['state_id']==state),None)
   if st:groups[state]=st['snapshot_indices'];continue
   step=next((st for st in o['steps'] if st.get('state_id')==state),{})
   groups[state]=step.get('observation_set',{}).get('snapshot_indices',[])
   if not groups[state] and isinstance(step.get('immediate_after'),int):groups[state]=[step['immediate_after']]
  (dest/f'{platform}-{case}-indices.json').write_text(json.dumps(groups,indent=2))
  ids=[]
  for state,idxs in groups.items():ids +=[(state,idx) for idx in idxs]
  # Each original image remains fully visible in its labeled thumbnail. Exact source files remain authoritative.
  for page,start in enumerate(range(0,len(ids),12)):
   part=ids[start:start+12]; w=300;h=675;cols=4;sheet=Image.new('RGB',(cols*w,math.ceil(len(part)/cols)*h),'#ddd');draw=ImageDraw.Draw(sheet)
   for n,(state,idx) in enumerate(part):
    s=o['snapshots'][idx];q=pathlib.Path(s['screenshot']);q=q if q.is_absolute() else p.parent/q
    im=Image.open(q).convert('RGB');im.thumbnail((w,h-25));x=(n%cols)*w;y=(n//cols)*h;sheet.paste(im,(x,y+25));draw.text((x,y),f'{idx} {state}',fill='black')
   target=dest/f'{platform}-{case}-{page}.jpg';sheet.save(target,quality=94);print(target.resolve())
