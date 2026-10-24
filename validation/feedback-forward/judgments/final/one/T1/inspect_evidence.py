import sys,json,pathlib,hashlib,math
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=ROOT/'judgments/final/one/T1'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'candidate-v9/scripts'))
import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[];overview=[]
for p in sorted((ROOT/'evaluation-inputs/final/T1').glob('*/*/*')):
 src,pt,case=p.parts[-3:];dst=OUT/src/pt/case;dst.mkdir(parents=True,exist_ok=True)
 ds={n:json.loads((p/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']}
 inp=ds['inputs'];obs=json.loads((ROOT/inp['observation']).read_text());raw=ROOT/inp['raw'];record={'source':src,'platform':pt,'case':case,'input_files':{n:sha(p/(n+'.json')) for n in ds},'observation_sha_actual':sha(ROOT/inp['observation']),'observation_sha_declared':inp['observation_sha256'],'environment':ds['environment-check']['status'],'automatic_counts':ds['automatic']['counts'],'automatic_unassessed_nonvisual':[{'id':r['id'],'reason':r['reason']} for r in ds['automatic']['assertions'] if r['status']=='unassessed' and r['id'] not in {x['id'] for x in ds['catalog']['rows'] if x['method']=='visual'}],'states':{},'steps':obs['steps']}
 for state in ds['plan']['states']:
  found,complete,reason,cap=native_checks.bound_state_evidence(obs,state);records=[];tiles=[]
  for idx,s in found:
   ip=raw/s['screenshot'];im=Image.open(ip).convert('RGB')
   if pt=='ios':
    v=s['viewport'];factor=im.width/s['app_frame']['width'];im=im.crop(tuple(round(v[k]*factor) for k in ['x','y'])+tuple(round((v[k]+v[sz])*factor) for k,sz in [('x','width'),('y','height')]))
    offset=s['viewport']['y']-s['runtime']['content_frame']['y'];logicalwidth=v['width'];height=s['runtime']['content_frame']['height']
   else:offset=s['scroll_offset_dp'];logicalwidth=s['logical_viewport_dp']['width'];height=s['scroll_max_dp']+s['viewport_height_dp']
   records.append({'index':idx,'path':str(ip),'sha256':sha(ip),'offset':offset,'binding':s['binding'],'screenshot_pixels':s['screenshot_pixels']})
   scale=1.25 if logicalwidth<=300 else 1.0
   im=im.resize((round(logicalwidth*scale),round(600*scale)))
   tiles.append((offset,im,idx))
  if tiles:
   scale=1.25 if logicalwidth<=300 else 1.0
   h=max(round(height*scale),max(round(a*scale)+im.height for a,im,_ in tiles));canvas=Image.new('RGB',(tiles[0][1].width+70,h),(240,240,240));draw=ImageDraw.Draw(canvas)
   # Each original full viewport is pasted in increasing offset. The provenance map retains every index.
   for offset,im,idx in sorted(tiles):
    y=round(offset*scale);canvas.paste(im,(70,y));draw.text((2,y+3),f'idx {idx}\ny {offset:.0f}',fill=(0,0,0))
   canvas.save(dst/(state['id']+'.png'))
  record['states'][state['id']]={'eligible_indices':[idx for idx,_ in found],'complete':complete,'reason':reason,'capture':cap,'originals':records}
 (dst/'inspection.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');overview.append({k:v for k,v in record.items() if k not in ['steps','states']})
 # Side by side groups retain readable state widths.
 for name,states in [('closed',['overview','requested-closed','replaced','held-choice']),('long',['permitted','requested']),('targets',['opened','cleared','restored'])]:
  images=[(sid,Image.open(dst/(sid+'.png'))) for sid in states if (dst/(sid+'.png')).exists()]
  canvas=Image.new('RGB',(sum(im.width for _,im in images),max(im.height for _,im in images)+60),(220,220,220));d=ImageDraw.Draw(canvas);x=0
  for sid,im in images:d.text((x+5,8),f'{src}/{pt}/{case} {sid}',fill=(0,0,0));canvas.paste(im,(x,60));x+=im.width
  canvas.save(dst/(name+'-catalog.png'))
(OUT/'runtime-inventory.json').write_text(json.dumps(overview,indent=2)+'\n')
# Independent reference catalog, full images, no native substitution.
for case,scope in [('P1','public'),('P2','public'),('H1','private')]:
 states=['overview','opened','permitted','cleared','restored','requested','requested-closed','replaced','held-choice'];ims=[]
 for sid in states:
  p=ROOT/f'design/T1/{scope}/references/{case}/{sid}.png'
  if p.exists():
   im=Image.open(p).convert('RGB');im.thumbnail((400,5000));ims.append((sid,im));manifest.append({'path':str(p),'sha256':sha(p),'size':Image.open(p).size})
 for start in [0,3,6]:
  group=ims[start:start+3]
  if group:
   cv=Image.new('RGB',(sum(im.width for _,im in group),max(im.height for _,im in group)+40),'#ddd');d=ImageDraw.Draw(cv);x=0
   for sid,im in group:d.text((x+5,5),case+' '+sid,fill='black');cv.paste(im,(x,40));x+=im.width
   cv.save(OUT/f'reference-{case}-{start}.png')
(OUT/'reference-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('generated',len(overview),'case catalogs; reference images',len(manifest))
