import sys
sys.dont_write_bytecode=True
from pathlib import Path
import sys,json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
O=B/'judgments/final/one/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
from native_checks import bound_state_evidence
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'inputs':{},'cases':{}}
for d in sorted((B/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(d.parts[-3:]);i=json.loads((d/'inputs.json').read_text());p=json.loads((d/'plan.json').read_text());c=json.loads((d/'catalog.json').read_text());a=json.loads((d/'automatic.json').read_text());e=json.loads((d/'environment-check.json').read_text());r=B/i['root'];obs=json.loads((B/i['observation']).read_text())
 for n in ['inputs','plan','catalog','automatic','environment-check']:
  f=d/(n+'.json');manifest['inputs'][str(f.relative_to(B))]=sha(f)
 for path,h in i['original_files'].items():
  actual=sha(B/path)
  manifest['inputs'][path]={'expected':h,'actual':actual,'matches':h==actual}
 info={'root':str(r),'observation_sha256':sha(B/i['observation']),'environment':e['status'],'automatic_counts':a['counts'],'automatic_F': [x for x in a['assertions'] if x['status']=='failed'],'states':{},'snapshots':[]}
 for j,s in enumerate(obs['snapshots']):
  f=r/s['screenshot'];info['snapshots'].append({'index':j,'state':s.get('state_id'),'path':str(f),'sha256':sha(f),'dimensions':list(Image.open(f).size)})
 out=O/key;out.mkdir(parents=True,exist_ok=True)
 for st in p['states']:
  found,complete,reason,cap=bound_state_evidence(obs,st)
  info['states'][st['id']]={'snapshot_indices':[j for j,s in found],'complete':complete,'reason':reason,'capture':cap}
  # Make directly sourced viewport contact sheets, never reflow/alter text.
  tiles=[]
  for j,s in found:
   im=Image.open(r/s['screenshot']).convert('RGB')
   if i['platform']=='ios':
    vp=s['viewport'];app=s['app_frame'];scale=im.width/app['width'];im=im.crop(tuple(round(v*scale) for v in [vp['x'],vp['y'],vp['x']+vp['width'],vp['y']+vp['height']]))
   w=390 if i['platform']=='android' else round(s['viewport']['width'])
   h=round(im.height*w/im.width);im=im.resize((w,h),Image.Resampling.LANCZOS)
   tile=Image.new('RGB',(400,h+42),'#ededed');tile.paste(im,((400-w)//2,42));dr=ImageDraw.Draw(tile);dr.text((5,3),key,fill='black');dr.text((5,19),f"{st['id']} / original index {j}",fill='black');tiles.append(tile)
  for page in range(math.ceil(len(tiles)/12)):
   ts=tiles[page*12:(page+1)*12];h=max([t.height for t in ts] or [640]);sheet=Image.new('RGB',(400*min(4,len(ts)),h*math.ceil(len(ts)/4)),'#c4c4c4')
   for n,t in enumerate(ts):sheet.paste(t,(n%4*400,n//4*h))
   sheet.save(out/f"contact-{st['id']}-{page}.png")
 manifest['cases'][key]=info
(O/'input-hashes-and-state-coverage.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('cases',len(manifest['cases']),'snapshots',sum(len(x['snapshots']) for x in manifest['cases'].values()),'sheets',len(list(O.glob('*/*/*/contact-*.png'))))
print('hash mismatches',sum(v.get('matches') is False for v in manifest['inputs'].values() if isinstance(v,dict)))
for k,c in manifest['cases'].items():print(k,[(s,len(x['snapshot_indices']),x['complete']) for s,x in c['states'].items()])
