from pathlib import Path
import json,hashlib,copy,shutil,random,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n');return p
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

CASES=[
 ('positive-drifting-closed-strip',True,True),('legacy-stable-height-no-root',False,True),
 ('missing-original-root',False,False),('missing-original-image',False,False),('path-traversal',False,False),('symlink-outside-root',False,False),('image-extent-header-mismatch',False,False),
 ('missing-process-identity',False,False),('binding-after-capture-drift',False,False),('stale-input-snapshot',False,False),('wrong-approved-input-index',True,False),('nonconsecutive-frame-link',False,False),
 ('rgb-changed',False,False),('alpha-changed',False,False),('rightmost-pixel-changed',False,False),('nonoverlap-static-region-changed',True,True),('forged-proof-header-with-bad-pixels',False,False),
 ('one-anchor-per-link',False,False),('anchors-not-vertically-distinct',False,False),('repeated-labels',False,False),('repeated-identifiers',False,False),('offscreen-duplicate-same-lineage',False,False),('offscreen-duplicate-different-container',False,False),
 ('container-roles-without-exposed-children',False,False),('real-container-with-child-nodes',False,False),('shared-leaf-trait-changed',False,False),('shared-leaf-reflow',False,False),('fractional-pixel-shift',False,False),('viewport-mapping-changed',False,False),
 ('gap-between-viewports',False,False),('terminal-extent-not-reached',False,False),('terminal-visible-flag-false',False,False),('duplicate-terminal-sentinel',False,False),('terminal-frame-outside-with-true-header',False,False),('actual-top-not-reached',False,False),
 ('capture-reports-binding-drift',True,False),('offaxis-content-width-unobserved',True,False),('header-proof-without-originals',False,False)]

def original_fixture(target):
 target.mkdir(parents=True,exist_ok=False);images=target/'images';images.mkdir();w,h=64,176;rng=random.Random(587031);world=Image.new('RGBA',(w,h));world.putdata([(rng.randrange(256),rng.randrange(256),rng.randrange(256),255)for _ in range(w*h)]);draw=ImageDraw.Draw(world)
 positions=[('leaf-a','A',50),('leaf-b','B',72),('leaf-c','C',102),('leaf-d','D',124)]
 for identifier,label,y in positions:draw.rectangle((2,y,15,y+9),fill=(255,255,255,255));draw.text((3,y),label,fill=(0,0,0,255))
 draw.rectangle((0,170,63,173),fill=(180,20,210,255));world.save(target/'oracle-world.png')
 binding={'pid':870123,'instance':'SIMULATED-closed-strip','fixture_index':0,'input_sha256':canonical({'fixture':'closed-four-leaf-static-world'}),'event_revision':0};snaps=[]
 for i,(off,estimate)in enumerate([(0,144),(40,160),(80,176)]):
  filename='frame-'+str(i)+'.png';world.crop((0,off,64,off+96)).save(images/filename)
  nodes=[{'index':0,'parent_index':None,'identifier':'__observer.scroll','label':'','role_raw':49,'frame':{'x':0,'y':0,'width':64,'height':96},'fully_within_viewport':True,'intersects_viewport':True}]
  for j,(identifier,label,y)in enumerate(positions,1):
   yy=y-off;fully=yy>=0 and yy+10<=96
   nodes.append({'index':j,'parent_index':0,'identifier':identifier,'label':label,'value':None,'role_raw':48,'enabled':True,'selected':False,'frame':{'x':2,'y':yy,'width':14,'height':10},'fully_within_viewport':fully,'intersects_viewport':yy<96 and yy+10>0})
  yy=170-off;nodes.append({'index':5,'parent_index':0,'identifier':'__observer.bottom','label':'End','role_raw':48,'frame':{'x':0,'y':yy,'width':64,'height':4},'fully_within_viewport':yy>=0 and yy+4<=96,'intersects_viewport':yy<96 and yy+4>0})
  snaps.append({'index':i,'name':'scroll-'+str(i),'state_id':'strip','screenshot':filename,'screenshot_attachment':filename,'binding':copy.deepcopy(binding),'binding_after_capture':copy.deepcopy(binding),'capture_consistent':True,'app_frame':{'x':0,'y':0,'width':64,'height':96},'viewport':{'x':0,'y':0,'width':64,'height':96},'screenshot_pixels':{'width':64,'height':96},'runtime':{'content_frame':{'x':0,'y':-off,'width':64,'height':estimate},'actual_environment':{'theme':'light','direction':'ltr','dynamic_type':'large'}},'nodes':nodes,'bottom_sentinel_visible':i==2})
 capture={'state_id':'strip','after_action':0,'binding':copy.deepcopy(binding),'snapshot_indices':[0,1,2],'top_reached':True,'bottom_reached':True,'stable_binding':True,'stable_height':False,'complete':False}
 observation={'schema_version':2,'coverage_protocol':2,'evidence_class':'SIMULATED','measurement_kind':'XCUI-SIMULATED native metadata','snapshots':snaps,'state_captures':[capture],'coverage':{'bottom_reached':True,'missing_identifiers':[]},'status':'passed'}
 state={'id':'strip','input_index':0,'after_action':0,'coverage':'full_content'};save(target/'observation.json',observation);save(target/'state.json',state);save(target/'ORACLE.json',{'evidence_class':'SIMULATED closed-world fixture','closed_state_premise':True,'no_async_or_hidden_or_offaxis_content':True,'world_width':64,'terminal_height':176,'offsets':[0,40,80],'estimated_heights':[144,160,176],'expected_links':[{'before':0,'after':1,'world_interval':[40,96]},{'before':1,'after':2,'world_interval':[80,136]}],'leaf_world_positions':positions,'files':{p.name:sha(p)for p in images.iterdir()}})
 return observation,state

def make_case(name,folder,pristine):
 shutil.copytree(pristine,folder);o=json.loads((folder/'observation.json').read_text());s=json.loads((folder/'state.json').read_text());root=folder/'images';found_indices=[0,1,2]
 def all_bindings(change):
  change(o['state_captures'][0]['binding'])
  for snap in o['snapshots']:change(snap['binding']);change(snap['binding_after_capture'])
 def pix(i,x,y,channel):
  p=root/('frame-'+str(i)+'.png');im=Image.open(p).convert('RGBA');v=list(im.getpixel((x,y)));v[channel]=(v[channel]+1)%256;im.putpixel((x,y),tuple(v));im.save(p)
 if name=='legacy-stable-height-no-root':
  for snap in o['snapshots']:snap['runtime']['content_frame']['height']=176
  root=None
 elif name in {'missing-original-root','header-proof-without-originals'}:root=None
 elif name=='missing-original-image':(root/'frame-1.png').unlink()
 elif name in {'path-traversal','symlink-outside-root'}:
  outside=folder/'outside.png';shutil.copyfile(root/'frame-1.png',outside)
  if name=='path-traversal':o['snapshots'][1]['screenshot']='../outside.png'
  else:
   (root/'frame-1.png').unlink();(root/'frame-1.png').symlink_to(outside)
 elif name=='image-extent-header-mismatch':o['snapshots'][1]['screenshot_pixels']['width']=65
 elif name=='missing-process-identity':all_bindings(lambda b:b.pop('pid',None))
 elif name=='binding-after-capture-drift':o['snapshots'][1]['binding_after_capture']['event_revision']=1
 elif name=='stale-input-snapshot':o['snapshots'][1]['binding']['input_sha256']='1'*64;o['snapshots'][1]['binding_after_capture']['input_sha256']='1'*64
 elif name=='wrong-approved-input-index':s['input_index']=1
 elif name=='nonconsecutive-frame-link':found_indices=[0,2];o['state_captures'][0]['snapshot_indices']=[0,2]
 elif name in {'rgb-changed','forged-proof-header-with-bad-pixels'}:pix(1,4,4,0)
 elif name=='alpha-changed':pix(1,4,4,3)
 elif name=='rightmost-pixel-changed':pix(1,63,4,1)
 elif name=='nonoverlap-static-region-changed':pix(0,4,4,0)
 elif name=='one-anchor-per-link':
  for snap in o['snapshots']:snap['nodes']=[n for n in snap['nodes']if n.get('identifier')not in {'leaf-b','leaf-d'}]
 elif name=='anchors-not-vertically-distinct':
  for snap in o['snapshots']:
   snap['nodes'][2]['frame']['y']=snap['nodes'][1]['frame']['y'];snap['nodes'][4]['frame']['y']=snap['nodes'][3]['frame']['y']
 elif name in {'repeated-labels','repeated-identifiers'}:
  for snap in o['snapshots']:
   for n in snap['nodes'][1:5]:
    if name=='repeated-labels':n['identifier']='';n['label']='Repeated'
    else:n['identifier']='duplicate'
 elif name in {'offscreen-duplicate-same-lineage','offscreen-duplicate-different-container'}:
  for snap in o['snapshots']:
   dup=copy.deepcopy(snap['nodes'][1]);dup.update(index=81,fully_within_viewport=False,intersects_viewport=False);dup['frame']['y']=500
   if name.endswith('different-container'):
    snap['nodes'].append({'index':80,'parent_index':0,'identifier':'branch-container','label':'Group','role_raw':1,'frame':{'x':0,'y':500,'width':64,'height':20},'fully_within_viewport':False});dup['parent_index']=80
   snap['nodes'].append(dup)
 elif name=='container-roles-without-exposed-children':
  for snap in o['snapshots']:
   for n in snap['nodes'][1:5]:n.update(role_raw=49,role='scrollView',has_children=True)
 elif name=='real-container-with-child-nodes':
  for snap in o['snapshots']:
   for n in copy.deepcopy(snap['nodes'][1:5]):snap['nodes'].append({'index':100+n['index'],'parent_index':n['index'],'identifier':'','label':'','role_raw':48,'frame':n['frame'],'fully_within_viewport':n['fully_within_viewport']})
 elif name=='shared-leaf-trait-changed':o['snapshots'][1]['nodes'][1]['enabled']=False
 elif name=='shared-leaf-reflow':o['snapshots'][1]['nodes'][1]['frame']['width']+=1
 elif name=='fractional-pixel-shift':
  snap=o['snapshots'][1];snap['runtime']['content_frame']['y']-=.5
  for n in snap['nodes'][1:]:n['frame']['y']-=.5
 elif name=='viewport-mapping-changed':o['snapshots'][1]['viewport']['width']=63
 elif name=='gap-between-viewports':
  for i,snap in enumerate(o['snapshots']):snap['runtime']['content_frame'].update(y=-100*i,height=296)
  o['snapshots'][0]['runtime']['content_frame']['height']=250
 elif name=='terminal-extent-not-reached':o['snapshots'][2]['runtime']['content_frame']['height']=200
 elif name=='terminal-visible-flag-false':o['snapshots'][2]['bottom_sentinel_visible']=False
 elif name=='duplicate-terminal-sentinel':dup=copy.deepcopy(o['snapshots'][2]['nodes'][5]);dup['index']=90;o['snapshots'][2]['nodes'].append(dup)
 elif name=='terminal-frame-outside-with-true-header':o['snapshots'][2]['nodes'][5]['frame']['y']=500
 elif name=='actual-top-not-reached':o['snapshots'][0]['runtime']['content_frame']['y']=-1
 elif name=='capture-reports-binding-drift':o['state_captures'][0]['stable_binding']=False
 elif name=='offaxis-content-width-unobserved':
  for snap in o['snapshots']:snap['runtime']['content_frame']['width']=128
  o['closed_state_premise']=False;o['scope_limitation']='Native content extends beyond observed vertical viewport width; full component is unobserved.'
 if name in {'forged-proof-header-with-bad-pixels','header-proof-without-originals'}:
  o['state_captures'][0].update(complete=True,coverage_proof={'complete':True,'reason':'FORGED header says complete','links':[{'sha256':'0'*64}]})
 save(folder/'observation.json',o);save(folder/'state.json',s)
 return o,s,root,[(i,o['snapshots'][i])for i in found_indices]
