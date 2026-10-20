import hashlib,json,pathlib,math
from PIL import Image,ImageDraw
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/own-corpora/unit-df4422/d0')
out=pathlib.Path(__file__).parent
manifest=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  p=b/platform/case;o=json.loads((p/'observation.json').read_text())
  for st in o['state_captures']:
   if st['state_id'] not in ['loaded','chosen','details','optioned','submitted','replaced']: continue
   thumbs=[];sources=[]
   for idx in st['snapshot_indices']:
    s=o['snapshots'][idx];src=p/s['screenshot'];im=Image.open(src).convert('RGB')
    if platform=='ios':
     v=s['viewport'];scale=im.width/s['app_frame']['width'];im=im.crop(tuple(round(x*scale) for x in [v['x'],v['y'],v['x']+v['width'],v['y']+v['height']]))
     width=round(v['width'])
    else: width=round(s['logical_viewport_dp']['width'])
    im=im.resize((width,600))
    thumbs.append(im);sources.append({'index':idx,'path':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
   width=thumbs[0].width;cols=min(3,len(thumbs));rows=math.ceil(len(thumbs)/cols)
   sheet=Image.new('RGB',(cols*width,rows*628),(230,230,230));d=ImageDraw.Draw(sheet)
   for j,(im,src) in enumerate(zip(thumbs,sources)):
    x=(j%cols)*width;y=(j//cols)*628;sheet.paste(im,(x,y+28));d.text((x+4,y+4),f'{case} {platform} {st["state_id"]} / {src["index"]}',fill=(0,0,0))
   dest=out/f'{case}-{platform}-{st["state_id"]}.png';sheet.save(dest)
   manifest.append({'case':case,'platform':platform,'state':st['state_id'],'contactSheet':str(dest.resolve()),'original_sources':sources})
(out/'contact-sheets.json').write_text(json.dumps(manifest,indent=2))
print('Created',len(manifest),'contact sheets from original PNGs; source indices and SHA256 retained.')
