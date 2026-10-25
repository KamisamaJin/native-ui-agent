from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,datetime
B=Path('validation/routed-forward/quality-inputs'); O=Path('validation/routed-forward/quality-panels/panel-two/inspection')
manifest=[]; sheets=[];seen={}
for p in sorted(B.glob('candidate-*/native/*/*/*')):
 c,_,scope,platform,case=p.relative_to(B).parts
 obs=json.loads((p/'native/observation.json').read_text()); idx=json.loads((p/'state-image-index.json').read_text())
 for state,row in idx.items():
  if c=='candidate-d1cbcd54' and platform=='ios' and state not in ['ready','replaced']:continue
  indices=row['indices'];chosen=indices[::2]
  if indices[-1] not in chosen:chosen.append(indices[-1])
  crops=[]
  for i in chosen:
   s=obs['snapshots'][i];f=p/'native'/s['screenshot'];im=Image.open(f).convert('RGB');h=hashlib.sha256(f.read_bytes()).hexdigest()
   if platform=='ios':
    v=s['viewport'];scale=im.width/s['app_frame']['width'];box=tuple(round(x*scale) for x in (v['x'],v['y'],v['x']+v['width'],v['y']+v['height']))
   else:box=(0,0,im.width,im.height)
   entry=dict(candidate=c,scope=scope,platform=platform,case=case,state=state,snapshot_index=i,source_file=str(f),sha256=h,crop_box_px=box,frame=s.get('frame',s.get('index')),viewport=s.get('viewport',s.get('logical_viewport_dp')),scroll=s.get('scroll_offset_dp',s.get('runtime',{}).get('scroll_offset')))
   if h in seen:entry['viewed_original_via']=seen[h];manifest.append(entry);continue
   seen[h]=[c,scope,platform,case,state,i];crop=im.crop(box);crops.append((i,crop,entry));manifest.append(entry)
  for j in range(0,len(crops),3):
   group=crops[j:j+3]; w=max(x[1].width for x in group);hh=max(x[1].height for x in group)
   canvas=Image.new('RGB',(w*len(group),hh+40),'#d8d8d8');d=ImageDraw.Draw(canvas)
   name=f'{c}_{scope}_{platform}_{state}_{j//3}.png'
   for col,(i,crop,en) in enumerate(group):canvas.paste(crop,(w*col,40));d.text((w*col+4,4),f'{c} {scope} {platform} {state} index {i}',fill='black');en['inspection_sheet']=name;en['sheet_position_px']=[w*col,40]
   canvas.save(O/name);sheets.append(name)
(O/'image-map.json').write_text(json.dumps(manifest,indent=2)+'\n');(O/'sheet-list.json').write_text(json.dumps(sheets,indent=2)+'\n')
(O/'started.json').write_text(json.dumps({'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Crops preserve exact original pixels. Source PNG/hash/frame/index/crop boxes in image-map.json. Every second sweep frame plus final frame, retaining overlapping 600-unit viewport coverage. Duplicate original PNG hashes reuse prior inspection only; each proposition assessed independently.'},indent=2)+'\n')
print(len(manifest),'qualified frames',len(sheets),'sheets');print('\n'.join(sheets))
