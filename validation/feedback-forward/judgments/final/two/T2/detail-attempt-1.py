import sys
sys.dont_write_bytecode=True
import json,pathlib,hashlib,math
from PIL import Image,ImageDraw
BASE=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');OUT=BASE/'judgments/final/two/T2'
sys.path.insert(0,str(BASE/'candidate-v9/scripts'));import native_checks,native_pixels
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
refs={}
for case,scope in [('P1','public'),('P2','public'),('H1','private')]:
 items=[]
 for p in sorted((BASE/f'design/T2/{scope}/references/{case}').glob('*.png')):
  im=Image.open(p).convert('RGB');tile=Image.new('RGB',(400,600),'white');im=im.resize((400,round(im.height*400/im.width)),Image.Resampling.LANCZOS)
  if im.height>600:tile.paste(im.crop((0,0,400,400)),(0,0));tile.paste(im.crop((0,im.height-180,400,im.height)),(0,420));ImageDraw.Draw(tile).text((10,403),'[middle omitted; full permitted viewed]',fill='red')
  else:tile.paste(im,(0,0))
  items.append((p,tile))
 pages=[]
 for pg in range(math.ceil(len(items)/8)):
  sh=Image.new('RGB',(1600,1264),'#eeeeee');d=ImageDraw.Draw(sh)
  for k,(p,im) in enumerate(items[pg*8:(pg+1)*8]):x=k%4*400;y=k//4*632;d.text((x+3,y+3),f'{case} {p.name}',fill='black');sh.paste(im,(x,y+32))
  dest=OUT/f'references-{case}-{pg+1}.png';sh.save(dest);pages.append(str(dest.relative_to(OUT)))
 refs[case]={'originals':[{'path':str(p.relative_to(BASE)),'sha256':sha(p)} for p,_ in items],'sheets':pages,'limit':'Top and bottom contact-sheet crops; full permitted original also inspected for complete shared chapter copy.'}
(OUT/'reference-manifest.json').write_text(json.dumps(refs,indent=2)+'\n')
receipts={};cells=[]
for p in sorted((BASE/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(p.parts[-3:]);i=json.loads((p/'inputs.json').read_text());o=json.loads((BASE/i['observation']).read_text());plan=json.loads((p/'plan.json').read_text());platform=i['platform'];states={}
 for state in plan['states']:
  ev=native_checks.bound_state_evidence(o,state)[0];facts={};bounds={}
  for name in ['title','subtitle','status','disclosure','choice','primary','canvas','surface']:
   found=[]
   for j,s in ev:
    r=native_checks.resolve(s,{'identifier':'audio.'+name},platform);n=r['semantic']
    if n.get('intersects_viewport'):
     found.append({'index':j,'facts':r['facts'],'frame':n.get('frame',n.get('unclipped_bounds_dp')),'fully_visible':n.get('fully_within_viewport',n.get('fully_visible'))})
   facts[name]=found
  states[state['id']]={'binding':ev[0][1]['binding'] if ev else None,'facts':facts}
  cell=Image.new('RGB',(400,220),'#eeeeee');d=ImageDraw.Draw(cell);d.text((5,5),key+' '+state['id'],fill='black')
  for k,name in enumerate(['status','primary']):
   for j,s in ev:
    r=native_checks.resolve(s,{'identifier':'audio.'+name},platform);n=r['semantic']
    if not n.get('fully_within_viewport',n.get('fully_visible',False)):continue
    im=Image.open(BASE/i['raw']/s['screenshot']).convert('RGB');rect=native_pixels.image_rectangle(s,n,platform,im.size)
    if not rect:continue
    l,t,rr,bb=rect;crop=im.crop((max(0,int(l)-4),max(0,int(t)-4),min(im.width,math.ceil(rr)+4),min(im.height,math.ceil(bb)+4)));h=round(crop.height*360/crop.width);crop=crop.resize((360,h),Image.Resampling.LANCZOS);cell.paste(crop,(20,35+k*90));d.text((5,20+k*90),f'{name} idx{j}; crop includes native boundary',fill='black');bounds[name]={'snapshot_index':j,'image_rectangle':rect};break
  cells.append(cell);states[state['id']]['paint_boundary_crops']=bounds
 receipts[key]={'states':states,'steps':[{k:v for k,v in s.items() if k in ['action','type','selector','outcome','callback_delta','dispatch','binding_after','same_process','before','after','snapshot','immediate_after','caller_update']}for s in o['steps']]}
for pg in range(math.ceil(len(cells)/12)):
 sh=Image.new('RGB',(1600,660),'#eeeeee')
 for k,im in enumerate(cells[pg*12:(pg+1)*12]):sh.paste(im,(k%4*400,k//4*220))
 sh.save(OUT/f'boundaries-{pg+1:02}.png')
(OUT/'native-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
print('reference and boundary sheets generated')
