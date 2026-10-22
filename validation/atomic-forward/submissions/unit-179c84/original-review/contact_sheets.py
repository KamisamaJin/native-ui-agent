import json,pathlib,math
from PIL import Image,ImageDraw
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/own-corpora/unit-179c84/d0')
out=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-179c84/agent-output/review')
manifest=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  obs=json.loads((root/platform/case/'observation.json').read_text())
  for state in ['baseline','expanded','submitted']:
   sc=next(x for x in obs['state_captures'] if x['state_id']==state)
   ids=sc['snapshot_indices'];tw=260 if case=='P1' else 200;th=round(600/(390 if case=='P1' else 248)*tw);cols=min(6,len(ids));rows=math.ceil(len(ids)/cols)
   sheet=Image.new('RGB',(cols*tw,rows*(th+26)), '#eeeeee');draw=ImageDraw.Draw(sheet)
   for n,idx in enumerate(ids):
    snap=obs['snapshots'][idx];p=root/platform/case/snap['screenshot'];im=Image.open(p).convert('RGB')
    if platform=='ios':
     v=snap['viewport'];sx=im.width/snap['app_frame']['width'];sy=im.height/snap['app_frame']['height'];im=im.crop((round(v['x']*sx),round(v['y']*sy),round((v['x']+v['width'])*sx),round((v['y']+v['height'])*sy)))
    im=im.resize((tw,th));x=(n%cols)*tw;y=(n//cols)*(th+26);sheet.paste(im,(x,y+26));draw.text((x+4,y+4),f'{platform} {case} {state} #{idx}',fill='black')
   dest=out/f'{platform}-{case}-{state}.png';sheet.save(dest)
   manifest.append({'sheet':str(dest),'platform':platform,'case':case,'state':state,'complete':sc['complete'],'original_indices':ids,'original_paths':[str(root/platform/case/obs['snapshots'][i]['screenshot']) for i in ids]})
(out/'contact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('\n'.join(x['sheet'] for x in manifest))
