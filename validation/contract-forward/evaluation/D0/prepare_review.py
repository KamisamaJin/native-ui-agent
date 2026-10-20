from pathlib import Path
import json,sys,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];D=R/'design';O=R/'evaluation/D0';sys.path.insert(0,str(R/'candidate-v6/scripts'));import native_checks as n
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();allrecords=[]
for alias in ['source-a','source-b']:
 for platform in ['ios','android']:
  cards=[]
  for case in ['P1','P2']:
   cap=R/f'common-corpora/{alias}/d0/{platform}/{case}';obs=json.loads((cap/'observation.json').read_text());plan=json.loads((D/f'public/compiled/{case}/{platform}/plan.json').read_text())
   for state in plan['states']:
    found,complete,reason,capture=n.state_evidence(obs,state);chosen=None
    for index,snap in found:
     res=n.resolve(snap,{'identifier':'enroll.reserve'},platform);node=res.get('control',{});semantic=res.get('semantic',{})
     if not node.get('intersects_viewport') or not node.get('fully_within_viewport',node.get('fully_visible',False)):continue
     imagepath=cap/snap['screenshot'];im=Image.open(imagepath).convert('RGB')
     if platform=='ios':
      raw=next((x for x in snap.get('nodes',[]) if x.get('identifier')=='enroll.reserve'),{});f=node.get('image_frame') or semantic.get('image_frame') or raw.get('image_frame')
      if not f:continue
      box=[f['x'],f['y'],f['x']+f['width'],f['y']+f['height']]
     else:box=node.get('image_bounds_px')
     if not box:continue
     box=(max(0,int(box[0])-12),max(0,int(box[1])-12),min(im.width,int(box[2])+13),min(im.height,int(box[3])+13))
     if box[2]<=box[0] or box[3]<=box[1]:continue
     crop=im.crop(box);chosen=dict(alias=alias,case=case,platform=platform,state=state['id'],snapshot=index,image=str(imagepath.relative_to(R)),sha256=sha(imagepath),crop_box=list(box),image_size=list(im.size));break
    if chosen:
     thumb=crop.copy();thumb.thumbnail((520,145));panel=Image.new('RGB',(560,185),'#FFFFFF');dr=ImageDraw.Draw(panel);dr.text((10,5),f"{alias} {case}/{platform}/{state['id']} snap {chosen['snapshot']}",fill='black');panel.paste(thumb,(10,32));cards.append(panel);allrecords.append(chosen)
    else:allrecords.append(dict(alias=alias,case=case,platform=platform,state=state['id'],snapshot=None,reason='No bound fully visible reserve control/image candidate.'))
  sheet=Image.new('RGB',(1120,max(1,185*((len(cards)+1)//2))),'#BBBBBB')
  for i,panel in enumerate(cards):sheet.paste(panel,((i%2)*560,(i//2)*185))
  out=O/alias/'review';out.mkdir(parents=True,exist_ok=True);sheet.save(out/f'{platform}-reserve-contact-sheet-v2.png')
(O/'visual-candidates.json').write_text(json.dumps(allrecords,indent=2)+'\n')
print('Candidates',len(allrecords),'with image',sum(r['snapshot'] is not None for r in allrecords))
