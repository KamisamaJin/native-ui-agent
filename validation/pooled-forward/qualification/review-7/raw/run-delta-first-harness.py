import sys,argparse,copy,shutil,itertools,struct,zlib,contextlib,io
sys.dont_write_bytecode=True
from domain_support import *
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import scroll_coverage,native_checks,coverage_domain,execution_plan,acceptance
base=ROOT/'work'/a.arm/'delta';base.mkdir();rows=[];config,domainplan,lock=setup_config(base/'admission',arm);value=coverage_domain.prepare(config,domainplan,lock)
previous=ROOT.parent/'review-6';oldarm='candidate-v13.5'if a.arm.startswith('candidate')else'baseline-v12.6-common-2';oldrun='admitted-runtime-retry-1'if a.arm.startswith('candidate')else'admitted-runtime';old=previous/'work'/oldarm/oldrun
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST validator/PNG/solver with SIMULATED native ABI/compile data; zero SDK','detail':detail};rows.append(row);save(base/(id+'-result.json'),row)
 if not passed:
  failure=ROOT/'first-failures'/(a.arm+'--'+id+'.json')
  with failure.open('x')as stream:json.dump(row,stream,indent=2)
 print(a.arm+' '+id+': '+row['status'],flush=True)
def observe(folder,case='A01-approved-runtime-shape-positive',abi=True):
 src=old/case;o=load(src/'observation.json');s=load(old/'A01-approved-runtime-shape-positive/state.json');n=attach_packet(folder/'packet',config,domainplan,value,arm,src/'packet/native')
 if abi:
  changes=[]
  for snap in o['snapshots']:
   for node in snap['nodes']:
    if node['parent_index']is None:node['parent_index']=-1
   vp=copy.deepcopy(snap['viewport']);scale=snap['screenshot_pixels']['width']/snap['app_frame']['width']
   snap['runtime'].update(offered_width=390,viewport_height=600,viewport=vp,theme='light',direction='ltr',dynamic_type='large',screen_scale=scale)
   snap['runtime']['actual_environment'].update(display_scale=scale)
   changes.append({'index':snap['index'],'root_parent_index':-1,'runtime_added':['offered_width','viewport_height','viewport','theme','direction','dynamic_type','screen_scale','actual_environment.display_scale']})
  save(folder/'ABI-SIDECAR.json',{'original_observation':str(src/'observation.json'),'original_sha256':sha(src/'observation.json'),'original_PNG_bytes_copied_unchanged':True,'authorship':'Independent review7 synthetic ABI metadata from current public Swift fields, not actual SDK output','changes':changes,'source_ABI':['assets/ios-observer/ObserverApp.swift:runtime','assets/ios-observer/ObserverTests.swift:capture AX parent_index array'],'native_runs':0})
 return o,s,n
def basic_plan(s,target='absent-target',prop='present',expected=False):return {'version':1,'states':[s],'required_assertion_ids':['delta'],'assertions':[{'id':'delta','state':s['id'],'kind':'control','target':{'identifier':target},'property':prop,'expected':expected}]}
def assess(folder,o,s,n,expected_full,expected_status=None,target='absent-target',prop='present',expected=False):
 save(folder/'observation.json',o);save(folder/'state.json',s);plan=basic_plan(s,target,prop,expected);report=native_checks.evaluate(plan,o,'ios',root=n);proof=scroll_coverage.certify([(i,o['snapshots'][i])for i in o['state_captures'][0]['snapshot_indices']],o['state_captures'][0]['binding'],n);save(folder/'evaluated.json',report);save(folder/'certificate.json',proof);actual_full=report['states'][s['id']]['complete'];actual_status=report['assertions'][0]['status'];passed=actual_full==expected_full and(expected_status is None or actual_status==expected_status)
 return passed,{'expected_full':expected_full,'actual_full':actual_full,'expected_status':expected_status,'actual_status':actual_status,'state_reason':report['states'][s['id']]['reason'],'certificate_complete':proof['complete'],'certificate_reason':proof['reason'],'joint_witness_assignment':proof.get('joint_witness_assignment'),'assertion':report['assertions'][0]}

# Re-read original packets under new immutable modules; no bytes are changed.
for case in['A01-approved-runtime-shape-positive','A07-raster16-lowbit-admitted-host','A08-joint-witness-admitted-host','A09-forged-runtime-shape','A11-late-presence','A12-late-unique','A13-seen-late-contradicts-absence','A14-real-duplicate-then-one']:
 src=old/case;o=load(src/'observation.json');s=load(old/'A01-approved-runtime-shape-positive/state.json');ev=native_checks.bound_state_evidence(o,s,src/'packet/native');record('R-'+case,not ev[1],{'original_observation_sha256':sha(src/'observation.json'),'reason':ev[2],'full':ev[1],'original_bytes_untouched':True,'interpretation':'Legacy packets omit new ABI metadata; rejection is not a valid-positive or fix-success credit.'})

for case,expected_full,expected_status,target,prop,expected in[
 ('A01-approved-runtime-shape-positive',True,'passed','absent-target','present',False),
 ('A07-raster16-lowbit-admitted-host',False,'unassessed','absent-target','present',False),
 ('A08-joint-witness-admitted-host',False,'unassessed','absent-target','present',False),
 ('A09-forged-runtime-shape',False,'unassessed','absent-target','present',False),
 ('A11-late-presence',True,'passed','semantic-target','present',True),('A12-late-unique',True,'passed','semantic-target','unique',True),
 ('A13-seen-late-contradicts-absence',True,'failed','semantic-target','present',False),('A14-real-duplicate-then-one',True,'failed','semantic-target','unique',True),
 ('A15-absent-all',True,'passed','semantic-target','present',False),('A16-mixed-epoch',False,'unassessed','semantic-target','present',True)]:
 folder=base/('ABI-'+case);folder.mkdir();o,s,n=observe(folder,case);ok,detail=assess(folder,o,s,n,expected_full,expected_status,target,prop,expected);record('ABI-'+case,ok,detail)

def png_header(path,depth=None,color=None):
 raw=path.read_bytes();body=bytearray(raw[16:29]);
 if depth is not None:body[8]=depth
 if color is not None:body[9]=color
 path.write_bytes(raw[:16]+bytes(body)+struct.pack('>I',zlib.crc32(b'IHDR'+bytes(body))&0xffffffff)+raw[33:])
def negative(folder,name,o,s,n):
 if name=='pixel-alpha-one-bit':
  p=n/'frame-1.png';im=Image.open(p).convert('RGBA');v=list(im.getpixel((4,4)));v[3]^=1;im.putpixel((4,4),tuple(v));im.save(p)
 elif name=='pixel-rgb-one-bit':
  p=n/'frame-1.png';im=Image.open(p).convert('RGBA');v=list(im.getpixel((389,4)));v[0]^=1;im.putpixel((389,4),tuple(v));im.save(p)
 elif name=='png-bitdepth1':png_header(n/'frame-1.png',depth=1)
 elif name=='png-palette':png_header(n/'frame-1.png',color=3)
 elif name=='png-grayscale':png_header(n/'frame-1.png',color=0)
 elif name=='png-header-dim-forgery':
  p=n/'frame-1.png';raw=p.read_bytes();body=bytearray(raw[16:29]);body[:4]=struct.pack('>I',391);p.write_bytes(raw[:16]+body+struct.pack('>I',zlib.crc32(b'IHDR'+body)&0xffffffff)+raw[33:])
 elif name=='png-truncated':p=n/'frame-1.png';p.write_bytes(p.read_bytes()[:31])
 elif name=='png-two-frame-APNG':
  p=n/'frame-1.png';im=Image.open(p).convert('RGBA');second=im.copy();second.putpixel((0,0),(1,2,3,4));im.save(p,save_all=True,append_images=[second],duration=100,loop=0)
 elif name=='runtime-offered-width':o['snapshots'][1]['runtime']['offered_width']=389
 elif name=='runtime-viewport-metadata':o['snapshots'][1]['runtime']['viewport']['height']=599
 elif name=='runtime-screen-scale':o['snapshots'][1]['runtime']['screen_scale']=2
 elif name=='runtime-display-scale':o['snapshots'][1]['runtime']['actual_environment']['display_scale']=2
 elif name=='runtime-theme':o['snapshots'][1]['runtime']['theme']='dark'
 elif name=='runtime-type':o['snapshots'][1]['runtime']['actual_environment']['dynamic_type']='small'
 elif name=='runtime-direction':o['snapshots'][1]['runtime']['direction']='rtl'
 elif name=='runtime-dimension-bool':o['snapshots'][1]['runtime']['offered_width']=True
 elif name=='encoding-version-bool':o['snapshots'][1]['geometry_encoding']['version']=True
 elif name=='boundary-count-bool':o['snapshots'][-1]['bottom_boundary']['match_count']=True
 elif name=='node-index-bool':o['snapshots'][0]['nodes'][0]['index']=False
 elif name=='node-parent-index-bool':o['snapshots'][0]['nodes'][1]['parent_index']=False
 elif name=='capture-index-bool':o['state_captures'][0]['snapshot_indices'][0]=False
 elif name=='root-parent-null':o['snapshots'][0]['nodes'][0]['parent_index']=None
 elif name=='binding-instance-number':
  o['state_captures'][0]['binding']['instance']=123
  for snap in o['snapshots']:
   snap['binding']['instance']=123;snap['binding_after_capture']['instance']=123;snap['bottom_boundary']['binding']['instance']=123
 elif name=='stable-height-invalid-runtime':
  for snap in o['snapshots']:snap['runtime']['content_frame']['height']=1100;snap['runtime']['offered_width']=389
 elif name=='stable-height-missing-domain-input':
  for snap in o['snapshots']:snap['runtime']['content_frame']['height']=1100
  (n/'coverage-domain-input.json').unlink()
 elif name=='missing-prepared-input':(n.parent/'coverage-domain-prepared.json').unlink()
 elif name=='compiled-host-changed':(n/'compiled-project/ObserverApp.swift').write_text('// different\n')
 elif name=='original-compile-action-missing':(n/'compiled-build.log').write_text('SIMULATED no actual component compile action\n')
 elif name=='original-component-copy-changed':(n/'coverage-domain-component.swift').write_text('// foreign\n')
 else:raise AssertionError(name)
for name in['pixel-alpha-one-bit','pixel-rgb-one-bit','png-bitdepth1','png-palette','png-grayscale','png-header-dim-forgery','png-truncated','png-two-frame-APNG','runtime-offered-width','runtime-viewport-metadata','runtime-screen-scale','runtime-display-scale','runtime-theme','runtime-type','runtime-direction','runtime-dimension-bool','encoding-version-bool','boundary-count-bool','node-index-bool','node-parent-index-bool','capture-index-bool','root-parent-null','binding-instance-number','stable-height-invalid-runtime','stable-height-missing-domain-input','missing-prepared-input','compiled-host-changed','original-compile-action-missing','original-component-copy-changed']:
 folder=base/name;folder.mkdir();o,s,n=observe(folder);negative(folder,name,o,s,n)
 try:ok,detail=assess(folder,o,s,n,False,'unassessed')
 except Exception as e:ok=False;detail={'unhandled_exception':type(e).__name__,'message':str(e),'expected':'closed U/error without full/absence credit'}
 record(name,ok,detail)

# Joint witnesses: later overlap is allowed only if another original pair works.
for name,expected_full in[('joint-retained-nonminimum-choice',True),('joint-alternative-first-link-witness',True),('joint-nonadjacent-identity-conflict',False)]:
 folder=base/name;folder.mkdir();o,s,n=observe(folder,'A08-joint-witness-admitted-host')
 if name=='joint-retained-nonminimum-choice':o['snapshots'][2]['nodes'][2]['frame']['y']=211-128
 if name=='joint-alternative-first-link-witness':
  for i,snap in enumerate(o['snapshots']):snap['nodes'].append({'index':90,'parent_index':0,'identifier':'independent-e','label':'E','role_raw':48,'enabled':True,'selected':False,'frame':rect(80,500-i*64,20,2),'fully_within_viewport':True,'intersects_viewport':True})
 if name=='joint-nonadjacent-identity-conflict':
  o['snapshots'][2]['nodes'][2]['frame']['y']=211-128
  for i in[0,2]:o['snapshots'][i]['nodes'].append({'index':90,'parent_index':0,'identifier':'nonadjacent-e','label':'E','role_raw':48,'enabled':True,'selected':False,'frame':rect(80,500-i*64,20+i,2),'fully_within_viewport':True,'intersects_viewport':True})
 ok,detail=assess(folder,o,s,n,expected_full,'passed'if expected_full else'unassessed');record(name,ok,detail)

# Native equality remains strict despite conservative raster compatibility.
folder=base/'native-raw-width-remains-strict';folder.mkdir();o,s,n=observe(folder)
for snap in o['snapshots']:snap['nodes'][1]['frame']['width']=30.000000000000007
plan=basic_plan(s,'anchor-a','width',30);plan['assertions'][0].update(kind='geometry',basis='semantic',op='eq');report=native_checks.evaluate(plan,o,'ios',root=n);save(folder/'evaluated.json',report);save(folder/'observation.json',o);record('native-raw-width-remains-strict',report['states']['start']['complete']and report['assertions'][0]['status']=='failed',{'report':report})

# Existence can be witnessed in incomplete capture; whole-state uniqueness scope
# remains disputed when full content is requested and unseen content is possible.
for name,expected_status in[('incomplete-presence-positive','passed'),('incomplete-whole-state-uniqueness','unassessed')]:
 folder=base/name;folder.mkdir();o,s,n=observe(folder,'A11-late-presence');o['snapshots'][-1]['bottom_boundary']['hittable']=False
 prop='present'if name.startswith('incomplete-presence')else'unique';ok,detail=assess(folder,o,s,n,False,expected_status,'semantic-target',prop,True);record(name,ok,detail)
save(ROOT/'raw'/(a.arm+'-delta-results.json'),rows)
