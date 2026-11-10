import sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/cache/study/arms/B');stage=sys.argv[1];out=b/'work'/f'{stage}-review';out.mkdir(exist_ok=True)
states=['draft','replacement','quantityChanged','ready','sent','revised','readyRevised','sentRevised'];manifest={}
for pl in ['ios','android']:
 root=b/'runs'/stage/pl/'cycle/capture/native';o=json.loads((root/'observation.json').read_text());manifest[pl]={}
 for sc in o['state_captures']:
  if sc['state_id'] not in states:continue
  inds=sc['snapshot_indices'];page=Image.new('RGB',(1560,1248),'#d0d0d0');d=ImageDraw.Draw(page);records=[]
  for n,i in enumerate(inds):
   s=o['snapshots'][i];p=root/s['screenshot'];im=Image.open(p).convert('RGB')
   if pl=='ios':
    v=s['viewport'];a=s['app_frame'];sx=im.width/a['width'];sy=im.height/a['height'];im=im.crop((round(v['x']*sx),round(v['y']*sy),round((v['x']+v['width'])*sx),round((v['y']+v['height'])*sy)))
   im=im.resize((390,600));x=(n%4)*390;y=(n//4)*624;page.paste(im,(x,y+24));d.text((x+4,y+5),f'{stage} {pl} {sc["state_id"]} #{i}',fill='black');records.append({'snapshot_index':i,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  dst=out/f'{pl}-{sc["state_id"]}.png';page.save(dst);manifest[pl][sc['state_id']]={'sheet':str(dst),'original_frames':records}
(out/'frame-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(out)
