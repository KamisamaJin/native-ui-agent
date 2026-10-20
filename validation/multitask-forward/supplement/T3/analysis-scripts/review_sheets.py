from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'supplement/T3';index=[];seen={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for stage in ['D0','FINAL']:
 batch=json.loads((R/f'evaluation-inputs/{stage}/T3/batch.json').read_text())
 for ent in batch['corpora']:
  alias=ent['anonymousID']
  for case in batch['cases']:
   op=R/ent['captures']/'android'/case/'observation.json';obs=json.loads(op.read_text())
   for state in ['loaded','reasoned','advanced','classified','submitted','replaced']:
    cap=next(x for x in obs['state_captures'] if x['state_id']==state);ids=cap['snapshot_indices'];ev=[{'snapshot_index':i,'path':str((op.parent/obs['snapshots'][i]['screenshot']).relative_to(R)),'sha256':sha(op.parent/obs['snapshots'][i]['screenshot'])} for i in ids];sig=tuple(x['sha256'] for x in ev);key=f'{stage}/{alias}/{case}/android/review-{state}.png';rec={'sheet':key,'stage':stage,'alias':alias,'case':case,'state':state,'snapshot_indices':ids,'complete':cap['complete'],'evidence':ev,'observation':{'path':str(op.relative_to(R)),'sha256':sha(op)}}
    if sig in seen:rec['pixel_identical_to_reviewed_sheet']=seen[sig]
    else:
     seen[sig]=key;tiles=[]
     for i in ids:
      s=obs['snapshots'][i];im=Image.open(op.parent/s['screenshot']).convert('RGB');vp=s['logical_viewport_dp'];im=im.resize((round(vp['width']),round(vp['height'])));tile=Image.new('RGB',(im.width,im.height+26),'#eee');tile.paste(im,(0,26));ImageDraw.Draw(tile).text((4,4),f'{stage} {alias} {case} {state} #{i}',fill='black');tiles.append(tile)
     w=max(t.width for t in tiles);h=max(t.height for t in tiles);cols=min(4,len(tiles));sheet=Image.new('RGB',(cols*w,math.ceil(len(tiles)/cols)*h),'#ddd')
     for j,t in enumerate(tiles):sheet.paste(t,((j%cols)*w,(j//cols)*h))
     dest=O/key;sheet.save(dest)
    index.append(rec)
(O/'android-visual-index.json').write_text(json.dumps(index,indent=2)+'\n');print('state groups',len(index),'unique image sequences',len(seen));print('unique sheets',[x['sheet'] for x in index if 'pixel_identical_to_reviewed_sheet' not in x])
