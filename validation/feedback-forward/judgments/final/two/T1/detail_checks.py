import sys,json,hashlib,math
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/final/two/T1';sys.path.insert(0,str(B/'candidate-v9/scripts'));import native_checks
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12);mapping={}
for alias in ['source-a','source-b']:
 for plat in ['ios','android']:
  tiles=[];records=[]
  for case in ['P1','P2','H1']:
   p=B/f'evaluation-inputs/final/T1/{alias}/{plat}/{case}';i=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());obs=json.loads((B/i['observation']).read_text())
   for st in plan['states']:
    candidates=[]
    for idx,s in native_checks.bound_state_evidence(obs,st)[0]:
     r=native_checks.resolve(s,{'identifier':'transfer.primary'},plat);n=r.get('control',{})
     if n.get('fully_within_viewport',n.get('fully_visible',False)): candidates.append((idx,s,n))
    if not candidates:continue
    idx,s,n=candidates[0];im=Image.open(B/i['raw']/s['screenshot']).convert('RGB')
    if plat=='ios':
     scale=im.width/s['app_frame']['width'];f=n['frame'];box=[f['x'],f['y'],f['x']+f['width'],f['y']+f['height']]
    else:scale=im.width/s['logical_viewport_dp']['width'];box=n['unclipped_bounds_dp']
    px=[round(x*scale) for x in box];margin=round(4*scale);crop=im.crop((px[0]-margin,px[1]-margin,px[2]+margin,px[3]+margin));w=330;h=round(crop.height*w/crop.width);crop=crop.resize((w,h));tile=Image.new('RGB',(358,130),'#EEEEEE');tile.paste(crop,(4,34));ImageDraw.Draw(tile).text((4,4),f'{case}/{st["id"]} #{idx}',font=font,fill='black');dr=ImageDraw.Draw(tile);fac=w/(px[2]-px[0]+2*margin);dr.rectangle((4+margin*fac,34+margin*fac,4+(px[2]-px[0]+margin)*fac,34+(px[3]-px[1]+margin)*fac),outline='#FF00FF',width=1);tiles.append(tile);records.append({'case':case,'state':st['id'],'index':idx,'control_box':box,'original':str(B/i['raw']/s['screenshot'])})
  sheet=Image.new('RGB',(1074,130*9),'#AAAAAA')
  for j,t in enumerate(tiles):sheet.paste(t,((j%3)*358,(j//3)*130))
  sheet.save(O/f'primary-boundaries-{alias}-{plat}.png');mapping[f'{alias}/{plat}']=records
(O/'primary-boundary-manifest.json').write_text(json.dumps(mapping,indent=2)+'\n')
# Reference slices avoid shrinking an entire long image to a tiny strip.
for case,scope in [('P1','public'),('P2','public'),('H1','private')]:
 p=B/f'design/T1/{scope}/references/{case}/permitted.png';im=Image.open(p).convert('RGB');w=330;im=im.resize((w,round(im.height*w/im.width)));tiles=[]
 for top in range(0,im.height,650):
  crop=im.crop((0,top,w,min(top+650,im.height)));t=Image.new('RGB',(338,680),'#EEEEEE');t.paste(crop,(4,30));ImageDraw.Draw(t).text((4,4),f'{case}/permitted ref slice {top}',font=font,fill='black');tiles.append(t)
 sh=Image.new('RGB',(338*len(tiles),680),'#AAAAAA')
 for j,t in enumerate(tiles):sh.paste(t,(j*338,0))
 sh.save(O/f'reference-detail-{case}.png')
