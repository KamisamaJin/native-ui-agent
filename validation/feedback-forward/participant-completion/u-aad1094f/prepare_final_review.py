import sys,json,pathlib,math,time
from PIL import Image,ImageDraw
r=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
w=r/'cache/u-aad1094f'
sys.path.insert(0,str(r/'baseline-v8/scripts'))
import native_checks
out=w/'agent-output/final-self'
out.mkdir(exist_ok=True)
(out/'phase.json').write_text(json.dumps({'startedAtUnix':time.time(),'completedAtUnix':None,'limits':[]},indent=2))
for pl in ['ios','android']:
 for case in ['P1','P2']:
  base=r/f'corpora/u-aad1094f/final-public/{pl}/{case}/native'
  p=base/'observation.json'
  if not p.is_file():continue
  obs=json.loads(p.read_text());plan=json.loads((r/f'design/T1/public/compiled/{case}/{pl}/plan.json').read_text());dst=out/pl/case;dst.mkdir(parents=True,exist_ok=True);index={}
  for state in plan['states']:
   found,complete,why,capture=native_checks.bound_state_evidence(obs,state);indices=[i for i,_ in found];index[state['id']]={'indices':indices,'complete':complete,'why':why}
   for part in range(math.ceil(len(indices)/12)):
    chosen=indices[part*12:(part+1)*12];tiles=[]
    for i in chosen:
     s=obs['snapshots'][i];im=Image.open(base/s['screenshot']).convert('RGB')
     if pl=='ios':
      vp=s['viewport'];af=s['app_frame'];sx=im.width/af['width'];sy=im.height/af['height'];im=im.crop((round(vp['x']*sx),round(vp['y']*sy),round((vp['x']+vp['width'])*sx),round((vp['y']+vp['height'])*sy)))
     # Retain the complete original viewport at a legible native-like size.
     im.thumbnail((360,630));tiles.append((i,im))
    tw=365;th=660;sheet=Image.new('RGB',(tw*4,th*math.ceil(len(tiles)/4)),'#ddd');draw=ImageDraw.Draw(sheet)
    for j,(i,im) in enumerate(tiles):x=j%4*tw;y=j//4*th;sheet.paste(im,(x,y+25));draw.text((x+3,y+5),f'{pl}/{case} {state["id"]} #{i}',fill='black')
    sheet.save(dst/f'{state["id"]}-{part}.jpg')
  (dst/'evidence-index.json').write_text(json.dumps(index,indent=2))
  print(pl,case,[(k,len(v['indices'])) for k,v in index.items()])
