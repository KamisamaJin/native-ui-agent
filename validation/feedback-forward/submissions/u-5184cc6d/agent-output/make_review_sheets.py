import json,pathlib,sys
from PIL import Image,ImageDraw
base=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
o=json.loads((base/'observation.json').read_text());states=['overview','opened','permitted','cleared','restored','requested','requested-closed','replaced','held-choice','competing-gates'];chosen=[(i,s) for i,s in enumerate(o['snapshots']) if s.get('state_id') in states]
for start in range(0,len(chosen),12):
 group=chosen[start:start+12];w,h=300,665;sheet=Image.new('RGB',(4*w,((len(group)+3)//4)*h),'#cccccc');d=ImageDraw.Draw(sheet)
 for j,(i,s) in enumerate(group):
  im=Image.open(base/s['screenshot']).convert('RGB')
  if 'app_frame' in s and 'viewport' in s:
   v=s['viewport'];scale=im.width/s['app_frame']['width'];im=im.crop(tuple(round(x*scale) for x in (v['x'],v['y'],v['x']+v['width'],v['y']+v['height'])))
  im.thumbnail((w,h-25));x=j%4*w;y=j//4*h;sheet.paste(im,(x,y+25));d.text((x+3,y+3),f'{i}: {s["state_id"]}',fill='black')
 sheet.save(out/f'frames-{start:03}.jpg',quality=92)
(out/'manifest.json').write_text(json.dumps({'observation':str(base/'observation.json'),'frames':[{'index':i,'state':s['state_id'],'path':str(base/s['screenshot'])} for i,s in chosen]},indent=2))
print(len(chosen), 'frames', len(list(out.glob('frames-*.jpg'))),'sheets')
