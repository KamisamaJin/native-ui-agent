from pathlib import Path
import copy,hashlib,json,random,struct,zlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ENCODING={'version':1,'representation':'ieee754-binary64','coordinate_space':'logical_screen_points','provider':'XCUIElementSnapshot.frame_and_native_CGRect','mapping':'app_frame_to_original_screenshot_pixels'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n');return p
def rect(x,y,w,h):return {'x':x,'y':y,'width':w,'height':h}
def png16(p,w,h,triples):
 def chunk(typ,data):return struct.pack('>I',len(data))+typ+data+struct.pack('>I',zlib.crc32(typ+data)&0xffffffff)
 data=b''.join(b'\0'+b''.join(struct.pack('>HHH',*triples[y*w+x])for x in range(w))for y in range(h))
 p.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,16,2,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b''))
def fixture(folder,joint=False):
 folder.mkdir(parents=True,exist_ok=False);(folder/'images').mkdir();w=64;h=116 if joint else176;offsets=[0,10,20]if joint else[0,40,80];heights=[96,106,116]if joint else[144,160,176];seed=819107 if joint else819106
 rng=random.Random(seed);world=Image.new('RGBA',(w,h));world.putdata([(rng.randrange(256),rng.randrange(256),rng.randrange(256),255)for _ in range(w*h)])
 points=[('leaf-a','A',30.2,10),('leaf-b','B',40.3,10),('leaf-c','C',100,2),('leaf-d','D',103,2)]if joint else[('leaf-a','A',50,10),('leaf-b','B',72,10),('leaf-c','C',102,10),('leaf-d','D',124,10)]
 world.save(folder/'oracle-world.png');binding={'pid':880617,'instance':'SIMULATED-independent-review6-'+str(seed),'fixture_index':0,'input_sha256':canonical({'fixture':'review6-independent-closed-world','seed':seed}),'event_revision':0};snaps=[]
 for i,(off,estimate)in enumerate(zip(offsets,heights)):
  name='frame-'+str(i)+'.png';world.crop((0,off,w,off+96)).save(folder/'images'/name)
  nodes=[{'index':0,'parent_index':None,'identifier':'__observer.scroll','label':'','role_raw':49,'frame':rect(0,0,64,96),'fully_within_viewport':True,'intersects_viewport':True}]
  for j,(identifier,label,yy,hh)in enumerate(points,1):
   if joint and i==2 and j in{1,2}:yy={1:31,2:40}[j]
   y=yy-off;fully=0<=y and y+hh<=96
   nodes.append({'index':j,'parent_index':0,'identifier':identifier,'label':label,'value':None,'role_raw':48,'enabled':True,'selected':False,'frame':rect(2,y,14,hh),'fully_within_viewport':fully,'intersects_viewport':y<96 and y+hh>0})
  terminal_y=h-3 if joint else170;terminal_h=1 if joint else4;y=terminal_y-off
  nodes.append({'index':5,'parent_index':0,'identifier':'__observer.bottom','label':'End','role_raw':48,'frame':rect(0,y,64,terminal_h),'fully_within_viewport':0<=y and y+terminal_h<=96,'intersects_viewport':y<96 and y+terminal_h>0})
  boundary={'identifier':'__observer.bottom','queried':True,'match_count':1,'hittable':True,'method':'XCUIElement.isHittable','binding':copy.deepcopy(binding),'frame':copy.deepcopy(nodes[-1]['frame'])}
  snaps.append({'index':i,'name':'scroll-'+str(i),'state_id':'strip','screenshot':name,'binding':copy.deepcopy(binding),'binding_after_capture':copy.deepcopy(binding),'capture_consistent':True,'geometry_encoding':copy.deepcopy(ENCODING),'app_frame':rect(0,0,64,96),'viewport':rect(0,0,64,96),'screenshot_pixels':{'width':64,'height':96},'runtime':{'content_frame':rect(0,-off,64,estimate),'actual_environment':{'theme':'light','direction':'ltr','dynamic_type':'large'}},'nodes':nodes,'bottom_sentinel_visible':i==2,'bottom_boundary':boundary})
 o={'schema_version':2,'coverage_protocol':2,'evidence_class':'SIMULATED','measurement_kind':'synthetic lossless binary64 native metadata, HOST PNGs; no native execution','snapshots':snaps,'state_captures':[{'state_id':'strip','after_action':0,'binding':copy.deepcopy(binding),'snapshot_indices':[0,1,2],'top_reached':True,'bottom_reached':True,'stable_binding':True,'stable_height':False,'complete':False}],'status':'passed'}
 s={'id':'strip','input_index':0,'after_action':0,'coverage':'full_content'}
 save(folder/'ORACLE.json',{'native_runs':0,'seed':seed,'closed_state_premise':True,'hidden_async_offaxis_supported':False,'world_size':[w,h],'offsets':offsets,'points':points,'encoding':'8-bit original RGBA','joint_assignment_adversary':joint})
 return o,s
CASES=[
 ('positive-independent-encoded-strip',True),('binary64-residual-unique-registration',True),
 ('terminal-outside-true-header',False),('global-offscreen-id-other-lineage',False),('container-role-leaves',False),('content-offaxis',False),
 ('missing-native-encoding',False),('unsupported-native-encoding',False),('boolean-coordinate',False),('native-anchor-outside-with-true-header',False),
 ('boundary-missing',False),('boundary-count-two',False),('boundary-not-hittable',False),('boundary-wrong-method',False),('boundary-stale-binding',False),('boundary-unrooted-sentinel',False),('boundary-frame-disagrees',False),
 ('original-rgb-bit-change',False),('original-alpha-bit-change',False),('rightmost-original-bit-change',False),('missing-image',False),('original-path-traversal',False),('original-symlink-escape',False),
 ('mixed-rgb-rgba',False),('mixed-gamma-encoding',False),('sixteen-bit-rgb-lowbit-mismatch',False),('joint-final-witness-inconsistency',False),
 ('common-leaf-trait-change',False),('global-repeated-leaf-incompatible',False),('raw-witness-overlap',False),('raster-witness-overlap',False),('leaf-order-swapped',False),
 ('nonconsecutive-frames',False),('source-pixel-forged-header',False),('missing-original-root',False),('unstable-binding-header-direct-only',True),('root-frame-disjoint-advisory',False)]
def make(name,folder):
 o,s=fixture(folder,joint=name=='joint-final-witness-inconsistency');root=folder/'images'
 def pix(index,x,y,ch):
  p=root/('frame-'+str(index)+'.png');im=Image.open(p).convert('RGBA');v=list(im.getpixel((x,y)));v[ch]=(v[ch]+1)%256;im.putpixel((x,y),tuple(v));im.save(p)
 if name=='binary64-residual-unique-registration':
  snap=o['snapshots'][1];off=40.00000000000001;snap['runtime']['content_frame']['y']=-off
  for n in snap['nodes'][1:]:n['frame']['y']-=off-40
 elif name=='terminal-outside-true-header':o['snapshots'][-1]['nodes'][-1]['frame']['y']=500
 elif name=='global-offscreen-id-other-lineage':
  for snap in o['snapshots']:
   dup=copy.deepcopy(snap['nodes'][1]);dup.update(index=81,parent_index=80,fully_within_viewport=False,intersects_viewport=False);dup['frame']['y']=500
   snap['nodes'] += [{'index':80,'parent_index':None,'identifier':'outside-root-container','role_raw':1,'frame':rect(0,500,64,20),'fully_within_viewport':False},dup]
 elif name=='container-role-leaves':
  for snap in o['snapshots']:
   for node in snap['nodes'][1:5]:node.update(role_raw=49,role='scrollView',has_children=True)
 elif name=='content-offaxis':
  for snap in o['snapshots']:snap['runtime']['content_frame']['width']=128
 elif name=='missing-native-encoding':o['snapshots'][1].pop('geometry_encoding')
 elif name=='unsupported-native-encoding':o['snapshots'][1]['geometry_encoding']['representation']='rounded-decimal'
 elif name=='boolean-coordinate':o['snapshots'][1]['nodes'][1]['frame']['x']=True
 elif name=='native-anchor-outside-with-true-header':o['snapshots'][1]['nodes'][1]['frame']['y']=-1
 elif name=='boundary-missing':o['snapshots'][-1].pop('bottom_boundary')
 elif name=='boundary-count-two':o['snapshots'][-1]['bottom_boundary']['match_count']=2
 elif name=='boundary-not-hittable':o['snapshots'][-1]['bottom_boundary']['hittable']=False
 elif name=='boundary-wrong-method':o['snapshots'][-1]['bottom_boundary']['method']='flag-only'
 elif name=='boundary-stale-binding':o['snapshots'][-1]['bottom_boundary']['binding']['event_revision']=1
 elif name=='boundary-unrooted-sentinel':o['snapshots'][-1]['nodes'][-1]['parent_index']=None
 elif name=='boundary-frame-disagrees':o['snapshots'][-1]['bottom_boundary']['frame']['y']-=10
 elif name=='original-rgb-bit-change':pix(1,4,4,0)
 elif name=='original-alpha-bit-change':pix(1,4,4,3)
 elif name=='rightmost-original-bit-change':pix(1,63,4,2)
 elif name=='missing-image':(root/'frame-1.png').unlink()
 elif name in{'original-path-traversal','original-symlink-escape'}:
  (folder/'outside.png').write_bytes((root/'frame-1.png').read_bytes())
  if name=='original-path-traversal':o['snapshots'][1]['screenshot']='../outside.png'
  else:(root/'frame-1.png').unlink();(root/'frame-1.png').symlink_to(folder/'outside.png')
 elif name=='mixed-rgb-rgba':Image.open(root/'frame-1.png').convert('RGB').save(root/'frame-1.png')
 elif name=='mixed-gamma-encoding':
  from PIL.PngImagePlugin import PngInfo
  metadata=PngInfo();metadata.add(b'gAMA',struct.pack('>I',45455));im=Image.open(root/'frame-1.png');im.save(root/'frame-1.png',pnginfo=metadata)
 elif name=='sixteen-bit-rgb-lowbit-mismatch':
  world=Image.open(folder/'oracle-world.png').convert('RGB');pixels=list(world.getdata());all16=[tuple(c*257 for c in rgb)for rgb in pixels]
  for i,off in enumerate([0,40,80]):
   vals=list(all16[off*64:(off+96)*64])
   if i==1:
    idx=4*64+4;r,g,b=vals[idx];vals[idx]=(r^1,g,b)
   png16(root/('frame-'+str(i)+'.png'),64,96,vals)
  save(folder/'RAW16-ORACLE.json',{'IHDR_bit_depth':16,'color_type':2,'overlap_mismatch':{'frame0':[4,44],'frame1':[4,4],'channel':'red','lowbit_xor':1},'expected':'U unsupported original encoding and unequal 16bit pixels; decoder mode conversion cannot prove exact original overlap'})
 elif name=='common-leaf-trait-change':o['snapshots'][1]['nodes'][1]['enabled']=False
 elif name=='global-repeated-leaf-incompatible':o['snapshots'][2]['nodes'][2]['frame']['width']=16
 elif name in{'raw-witness-overlap','raster-witness-overlap'}:
  for snap in o['snapshots']:
   for a,b in[(1,2),(3,4)]:
    snap['nodes'][b]['frame']['y']=snap['nodes'][a]['frame']['y']+9.9
    if name=='raster-witness-overlap':snap['nodes'][a]['frame']['height']=10.2;snap['nodes'][b]['frame']['y']+=.4
 elif name=='leaf-order-swapped':
  a,b=o['snapshots'][1]['nodes'][1:3];a['frame']['y'],b['frame']['y']=b['frame']['y'],a['frame']['y']
 elif name=='nonconsecutive-frames':o['state_captures'][0]['snapshot_indices']=[0,2]
 elif name=='source-pixel-forged-header':pix(1,3,3,0);o['state_captures'][0].update(complete=True,coverage_proof={'complete':True,'reason':'FORGED'})
 elif name=='missing-original-root':root=None
 elif name=='unstable-binding-header-direct-only':o['state_captures'][0]['stable_binding']=False
 elif name=='root-frame-disjoint-advisory':
  for snap in o['snapshots']:snap['nodes'][0]['frame']['y']=500
 save(folder/'observation.json',o);save(folder/'state.json',s)
 return o,s,root,[(i,o['snapshots'][i])for i in o['state_captures'][0]['snapshot_indices']]
