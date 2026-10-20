import pathlib,json,hashlib
from PIL import Image,ImageDraw
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
w=pathlib.Path(__file__).resolve().parents[2]; out=w/'agent-output/review'
summary={}; images=[]; expected=['loaded','leveled','previewed','muted','submitted','replaced']
for platform in ['ios','android']:
 for case in ['P1','P2']:
  run=root/'own-corpora/unit-6f8d35/d0'/platform/case
  obs=json.load(open(run/'observation.json'))
  report=json.load(open(root/'submissions/unit-6f8d35/own-checks/d0'/case/platform/'report.json'))
  key=platform+'-'+case
  summary[key]={'counts':report['counts'],'failures':[{k:a.get(k) for k in ['id','state','requirement_id','expected','unit','actual','snapshot_indices','reason']} for a in report['machine_findings']],'states':[{k:s.get(k) for k in ['state_id','snapshot_indices','complete','top_reached','bottom_reached','stable_binding','binding','max_gap']} for s in obs['state_captures'] if s['state_id'] in expected],'steps':[{'index':i,'state_id':s.get('state_id',s.get('action',{}).get('state_id')),'outcome':s.get('outcome'),'dispatch':s.get('dispatch'),'callback_delta':s.get('callback_delta')} for i,s in enumerate(obs['steps'])]}
  for state in expected:
   capture=next(s for s in obs['state_captures'] if s['state_id']==state)
   indices=capture['snapshot_indices']
   if state not in ['loaded','replaced']:indices=indices[:3]
   for offset in range(0,len(indices),3):
    chunk=indices[offset:offset+3]; tiles=[]; metadata=[]
    for idx in chunk:
     snap=obs['snapshots'][idx]
     raw=snap.get('screenshot',snap.get('image'))
     if not raw:
      choices=sorted(run.glob(f'{idx:03d}-*.png')); raw=choices[0].name if choices else None
     if not raw:raise ValueError((key,state,idx,list(snap)))
     p=pathlib.Path(raw);p=p if p.is_absolute() else run/p
     if not p.is_file():p=run/p.name
     img=Image.open(p).convert('RGB'); targetw=360; targeth=round(img.height*targetw/img.width)
     tile=Image.new('RGB',(targetw,targeth+44),'#DDDDDD');tile.paste(img.resize((targetw,targeth)),(0,44))
     ImageDraw.Draw(tile).text((6,6),f'{platform} {case} {state} index {idx}',fill='black')
     tiles.append(tile);metadata.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'snapshot_index':idx})
    canvas=Image.new('RGB',(len(tiles)*360,max(t.height for t in tiles)),'#DDDDDD')
    for j,t in enumerate(tiles):canvas.paste(t,(j*360,0))
    p=out/f'{key}-{state}-{offset//3}.png';canvas.save(p)
    images.append({'sheet':str(p),'platform':platform,'case':case,'state':state,'originals':metadata})
(out/'original-summary.json').write_text(json.dumps(summary,indent=2))
(out/'contact-sheet-index.json').write_text(json.dumps(images,indent=2))
for k,v in summary.items():
 print(k,v['counts'],'failures',[(f['id'],f['expected']) for f in v['failures']])
 print('steps',[(s['index'],s['state_id'],s['outcome'],(s.get('dispatch') or {}).get('succeeded'),s['callback_delta']) for s in v['steps']])
 print('coverage',[(s['state_id'],s['complete'],s['snapshot_indices']) for s in v['states']])
print('sheets',len(images))
