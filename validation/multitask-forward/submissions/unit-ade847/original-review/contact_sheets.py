from PIL import Image, ImageOps, ImageDraw
import json,pathlib,hashlib
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
out=pathlib.Path(__file__).resolve().parent
records=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  corpus=root/'own-corpora/unit-ade847/d0'/platform/case
  observation=json.load(open(corpus/'observation.json'))
  for state in ['loaded','leveled','previewed','muted','submitted','replaced']:
   capture=next(s for s in observation['state_captures'] if s['state_id']==state)
   indices=capture['snapshot_indices']
   if state not in ['loaded','replaced']:
    step=next(s for s in observation['steps'] if s.get('state_id')==state)
    indices=step.get('observation_set',{}).get('snapshot_indices',[]) or indices[:2]
   tiles=[]; sources=[]
   for i in indices:
    snap=observation['snapshots'][i]
    path=corpus/snap['screenshot']
    im=Image.open(path).convert('RGB'); im.thumbnail((320,700))
    tile=Image.new('RGB',(340,740),'#ddd');tile.paste(im,((340-im.width)//2,32))
    ImageDraw.Draw(tile).text((5,5),f'{case} {platform} {state} index {i}',fill='black')
    tiles.append(tile); sources.append({'index':i,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
   cols=min(3,len(tiles));rows=(len(tiles)+cols-1)//cols
   sheet=Image.new('RGB',(cols*340,rows*740),'white')
   for i,tile in enumerate(tiles):sheet.paste(tile,((i%cols)*340,(i//cols)*740))
   target=out/f'{case}-{platform}-{state}.png';sheet.save(target)
   records.append({'case':case,'platform':platform,'state':state,'path':str(target),'sources':sources})
(out/'contact-sheet-index.json').write_text(json.dumps(records,indent=2))
print('Created',len(records),'contact sheets')
