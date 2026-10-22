import pathlib,json,sys,hashlib,math
from PIL import Image,ImageDraw,ImageFont
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
O=B/'judgments/d0/one/T1';sys.path.insert(0,str(B/'candidate-v8/scripts'));import native_checks
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
hashes={};manifest={};coverage={};bindings={}
def record(p):
 hashes[str(p.relative_to(B))]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in sorted((B/'evaluation-inputs/d0/T1').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T1'));I={n:json.loads((p/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']}
 for n in I:record(p/(n+'.json'))
 inp=I['inputs'];root=B/inp['root'];obs_path=B/inp['observation'];record(obs_path);obs=json.loads(obs_path.read_text())
 assert hashes[inp['observation']]==inp['observation_sha256']
 manifest[key]={'input_declared_original_files':inp['original_files']}
 coverage[key]={};bindings[key]={'steps':obs['steps'],'states':{},'runtime':obs['snapshots'][0].get('runtime')}
 for sn in obs['snapshots']:
  record(root/sn['screenshot'])
 for state in I['plan']['states']:
  found,complete,reason,capture=native_checks.bound_state_evidence(obs,state)
  coverage[key][state['id']]={'indices':[i for i,s in found],'complete':complete,'reason':reason,'binding':capture.get('binding') if capture else None}
  bindings[key]['states'][state['id']]={'capture':capture,'targets':{}}
  for idx,s in found:
   for node in s['nodes']:
    tag=node.get('identifier',node.get('tag',''))
    if tag.startswith('workshop.'):
     bindings[key]['states'][state['id']]['targets'].setdefault(tag,[]).append({'snapshot_index':idx,**node})
  if not found:continue
  strips=[];segments=[]
  # Preserve every original viewport in a contact sheet as well as a non-blended reading strip.
  for idx,s in found:
   im=Image.open(root/s['screenshot']).convert('RGB')
   if inp['platform']=='ios':
    vp=s['viewport'];scale=im.width/s['app_frame']['width'];box=tuple(round(v*scale) for v in [vp['x'],vp['y'],vp['x']+vp['width'],vp['y']+vp['height']]); crop=im.crop(box);w=round(vp['width']);h=round(vp['height']);offset=vp['y']-s['runtime']['content_frame']['y']
   else:
    w=round(s['logical_viewport_dp']['width']);h=round(s['viewport_height_dp']);crop=im;offset=s['scroll_offset_dp']
   crop=crop.resize((w,h),Image.Resampling.LANCZOS)
   strips.append((idx,offset,crop))
  height=round(max(off+im.height for _,off,im in strips)); width=strips[0][2].width
  stitch=Image.new('RGB',(width,height),'#b7b7b7');last=0
  for idx,off,im in strips:
   y=round(off);cut=max(0,last-y)
   if cut<im.height:
    stitch.paste(im.crop((0,cut,im.width,im.height)),(0,y+cut));segments.append({'index':idx,'offset':off,'source_native_y':[cut,im.height],'strip_y':[y+cut,y+im.height]});last=y+im.height
  fold=1100;columns=math.ceil(height/fold);panel_w=width+12
  board=Image.new('RGB',(panel_w*columns,fold+70),'#d1d1d1');d=ImageDraw.Draw(board)
  for c in range(columns):
   start=c*fold;end=min(height,start+fold);label=key+' '+state['id']+'\ny='+str(start)+'..'+str(end)+'\nidx '+','.join(str(x['index']) for x in segments if x['strip_y'][0]<end and x['strip_y'][1]>start)
   d.multiline_text((c*panel_w+3,3),label,fill='black',font=font,spacing=2)
   board.paste(stitch.crop((0,start,width,end)),(c*panel_w,65))
  dest=O/'sheets'/key/(state['id']+'.png');dest.parent.mkdir(parents=True,exist_ok=True);board.save(dest)
  coverage[key][state['id']]['sheet']=str(dest.relative_to(O));coverage[key][state['id']]['sheet_segments']=segments
for capsule in ['unit-99c640','unit-b44248']:
 for name in ['alerttoast/Sources/AlertToast/WorkshopSlotPlanner.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/WorkshopSlotPlanner.kt']:
  record(B/'submissions'/capsule/'d0/source'/name)
for p in (B/'design-v2/T1/public').glob('*'):
 if p.is_file():record(p)
for case in ['P1','P2']:
 for p in (B/'design-v2/T1/public/cases'/case).glob('*'):
  if p.is_file():record(p)
for p in (B/'candidate-v8/scripts').glob('*.py'):record(p)
for p in (B/'candidate-v8/references').glob('*.md'):record(p)
for name,obj in [('input-hashes.json',hashes),('declared-input-hashes.json',manifest),('coverage.json',coverage),('bindings.json',bindings)]:
 (O/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
print('Prepared',len(list((O/'sheets').rglob('*.png'))),'state sheets; hashed',len(hashes),'approved input artifacts')
