import pathlib,json,math,sys
from PIL import Image,ImageDraw
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/two/T1';M=json.loads((O/'inspection-records.json').read_text());records={}
for key,rec in M.items():
 obs=json.loads((B/rec['inputs']['observation']).read_text());root=B/rec['inputs']['root'];platform=rec['inputs']['platform'];records[key]={}
 for state,srec in rec['states'].items():
  found=[(n,obs['snapshots'][n]) for n in srec['indices']];parts=[]
  for n,s in found:
   im=Image.open(root/s['screenshot']).convert('RGB')
   if platform=='ios':
    v=s['viewport'];af=s['app_frame'];sx=im.width/af['width'];sy=im.height/af['height'];box=(v['x']*sx,v['y']*sy,(v['x']+v['width'])*sx,(v['y']+v['height'])*sy);crop=im.crop(tuple(round(z)for z in box));offset=v['y']-s['runtime']['content_frame']['y'];width=v['width'];height=v['height']
   else:
    crop=im;offset=s['scroll_offset_dp'];width=s['logical_viewport_dp']['width'];height=s['logical_viewport_dp']['height']
   parts.append((offset,n,crop,width,height))
  if not parts:continue
  scale=1.25;width=parts[0][3];maximum=max(p[0]+p[4]for p in parts);canvas=Image.new('RGB',(round(width*scale),math.ceil(maximum*scale)),'#ff00ff');spans=[];end=-1
  for offset,n,crop,w,h in sorted(parts):
   # Continuous scroll reconstruction uses native content offset; originals retained, no inferred missing span.
   image=crop.resize((round(w*scale),round(h*scale)))
   start=max(offset,end);finish=offset+h
   if finish<=end:continue
   cut=max(0,round((start-offset)*scale));canvas.paste(image.crop((0,cut,image.width,image.height)),(0,round(start*scale)))
   spans.append({'index':n,'from_native':start,'to_native':finish,'source':str(root/obs['snapshots'][n]['screenshot'])});end=finish
  stripheight=750;tiles=[]
  for pos in range(0,canvas.height,stripheight):tiles.append((pos,canvas.crop((0,pos,canvas.width,min(pos+stripheight,canvas.height)))))
  pages=[]
  for page,start in enumerate(range(0,len(tiles),6)):
   group=tiles[start:start+6];cw=canvas.width+10;out=Image.new('RGB',(cw*3,810*min(2,math.ceil(len(group)/3))),'#ddd');d=ImageDraw.Draw(out)
   for j,(pos,tile)in enumerate(group):
    x=j%3*cw;y=j//3*810;inds=[r['index']for r in spans if r['to_native']>pos/scale and r['from_native']<(pos+tile.height)/scale];d.text((x+2,y+2),key+'\n'+state+f' y={pos/scale:g}\nindices='+','.join(map(str,inds)),fill='black');out.paste(tile,(x,y+58))
   dest=O/'coverage-strips'/key/f'{state}-{page+1:02d}.png';dest.parent.mkdir(parents=True,exist_ok=True);out.save(dest);pages.append(str(dest.relative_to(O)))
  records[key][state]={'complete':srec['complete'],'spans':spans,'pages':pages}
 print(key,{k:len(v['pages'])for k,v in records[key].items()})
(O/'coverage-strips.json').write_text(json.dumps(records,indent=2)+'\n')
