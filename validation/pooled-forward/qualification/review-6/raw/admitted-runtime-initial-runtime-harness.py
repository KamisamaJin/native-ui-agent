import sys,argparse,copy,shutil
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import coverage_domain,native_checks,execution_plan,acceptance,locator_diagnostics
base=ROOT/'work'/a.arm/'admitted-runtime';base.mkdir();rows=[]
config,domainplan,lock=setup_config(base/'admission',arm);value=coverage_domain.prepare(config,domainplan,lock)
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST original PNG/validator with SIMULATED390x600 native and compile metadata; zero SDK','detail':detail};rows.append(row);save(base/(id+'-result.json'),row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--admitted-runtime--'+id+'.json'),row)
 print(a.arm+' '+id+': '+row['status'],flush=True)
def generated(folder,joint=False,sixteen=False):
 folder.mkdir();images=folder/'images';images.mkdir();w=390;h=728 if joint else 1100;offsets=[0,64,128]if joint else[0,250,500];estimates=[600,664,728]if joint else[900,1000,1100]
 world=Image.new('RGBA',(w,h));world.putdata([((x*17)%256,y%256,((y//256)*53+x%17)%256,255)for y in range(h)for x in range(w)]);world.save(folder/'ORIGINAL-world.png')
 points=[('anchor-a',200.2,10),('anchor-b',210.3,10),('anchor-c',620,2),('anchor-d',623,2)]if joint else[('anchor-a',300,60),('anchor-b',450,60),('anchor-c',650,60),('anchor-d',800,60)]
 binding={'pid':884621,'instance':'SIMULATED-admitted-runtime','fixture_index':0,'event_revision':0,'input_sha256':canonical(load(config['fixtures'])['initial'])};snapshots=[]
 all16=[tuple(c*257 for c in rgb[:3])for rgb in world.getdata()]if sixteen else None
 for i,off in enumerate(offsets):
  filename='frame-'+str(i)+'.png'
  if sixteen:
   pixels=list(all16[off*w:(off+600)*w])
   if i==1:
    index=4*w+4;v=pixels[index];pixels[index]=(v[0]^1,v[1],v[2])
   png16(images/filename,w,600,pixels)
  else:world.crop((0,off,w,off+600)).save(images/filename)
  nodes=[{'index':0,'parent_index':None,'identifier':'__observer.scroll','role_raw':49,'frame':rect(0,0,390,600),'fully_within_viewport':True,'intersects_viewport':True}]
  for j,(identifier,y,height)in enumerate(points,1):
   if joint and i==2 and j in{1,2}:y={1:201,2:210}[j]
   y-=off;nodes.append({'index':j,'parent_index':0,'identifier':identifier,'label':identifier,'role_raw':48,'enabled':True,'selected':False,'frame':rect(20,y,30,height),'fully_within_viewport':0<=y and y+height<=600,'intersects_viewport':y<600 and y+height>0})
  yy=h-3-off;nodes.append({'index':5,'parent_index':0,'identifier':'__observer.bottom','label':'End','role_raw':48,'frame':rect(0,yy,w,1),'fully_within_viewport':0<=yy and yy+1<=600,'intersects_viewport':yy<600 and yy+1>0})
  snapshots.append({'index':i,'name':'scroll-'+str(i),'state_id':'start','screenshot':filename,'binding':copy.deepcopy(binding),'binding_after_capture':copy.deepcopy(binding),'capture_consistent':True,'geometry_encoding':copy.deepcopy(ENCODING),'app_frame':rect(0,0,w,600),'viewport':rect(0,0,w,600),'screenshot_pixels':{'width':w,'height':600},'runtime':{'content_frame':rect(0,-off,w,estimates[i]),'actual_environment':{'theme':'light','direction':'ltr','dynamic_type':'large'}},'nodes':nodes,'bottom_sentinel_visible':i==2,'bottom_boundary':{'queried':True,'match_count':1,'hittable':True,'method':'XCUIElement.isHittable','binding':copy.deepcopy(binding),'identifier':'__observer.bottom','frame':copy.deepcopy(nodes[-1]['frame'])}})
 o={'schema_version':2,'coverage_protocol':2,'evidence_class':'SIMULATED','snapshots':snapshots,'state_captures':[{'state_id':'start','after_action':0,'snapshot_indices':[0,1,2],'binding':copy.deepcopy(binding),'stable_binding':True,'top_reached':True,'bottom_reached':True,'complete':False}],'status':'passed'};s={'id':'start','input_index':0,'after_action':0,'coverage':'full_content'}
 save(folder/'ORACLE.json',{'evidence_class':'Independent synthetic390x600 logical/frame/originalPNG','original_png_size':[390,600],'full_world_height':h,'offsets':offsets,'no_hidden_async_offaxis':True,'native_runs':0,'joint_global_witness_adversary':joint,'PNG16_lowbit_adversary':sixteen})
 return o,s,images

cases=[('A01-approved-runtime-shape-positive','positive',True),('A02-terminal-rectangle-outside','terminal',False),('A03-global-offscreen-duplicate','duplicate-id',False),('A04-container-role-only','container',False),('A05-content-offaxis','offaxis',False),('A06-unstable-capture','unstable',False),('A07-raster16-lowbit-admitted-host','sixteen',False),('A08-joint-witness-admitted-host','joint',False),('A09-forged-runtime-shape','wrong-shape',False)]
positive=None
for id,mode,expected_full in cases:
 folder=base/id;folder.mkdir();o,s,images=generated(folder/'source',joint=mode=='joint',sixteen=mode=='sixteen')
 if mode=='terminal':o['snapshots'][-1]['nodes'][-1]['frame']['y']=5000
 if mode=='duplicate-id':
  for snap in o['snapshots']:
   dup=copy.deepcopy(snap['nodes'][1]);dup.update(index=81,parent_index=None,fully_within_viewport=False);dup['frame']['y']=5000;snap['nodes'].append(dup)
 if mode=='container':
  for snap in o['snapshots']:
   for n in snap['nodes'][1:5]:n.update(role_raw=49,has_children=True)
 if mode=='offaxis':
  for snap in o['snapshots']:snap['runtime']['content_frame']['width']=780
 if mode=='unstable':o['state_captures'][0]['stable_binding']=False
 if mode=='wrong-shape':
  # Preserve a coherent axis-aligned native map but contradict the390x600 approval.
  for snap in o['snapshots']:
   for field in['app_frame','viewport']:
    snap[field]['width']=195;snap[field]['height']=300
   for n in snap['nodes']:
    for k in n['frame']:n['frame'][k]/=2
   for k in snap['runtime']['content_frame']:snap['runtime']['content_frame'][k]/=2
   for k in snap['bottom_boundary']['frame']:snap['bottom_boundary']['frame'][k]/=2
 n=attach_packet(folder/'packet',config,domainplan,value,arm,images);save(folder/'observation.json',o);save(folder/'state.json',s)
 ev=native_checks.bound_state_evidence(o,s,n);absence_plan={'version':1,'states':[s],'required_assertion_ids':['absence'],'assertions':[{'id':'absence','state':'start','kind':'control','target':{'identifier':'absent-target'},'property':'present','expected':False}]};report=native_checks.evaluate(absence_plan,o,'ios',root=n);env=acceptance.environment(o,load(config['environment']),'ios');save(folder/'evaluated.json',report);save(folder/'environment.json',env)
 record(id,ev[1]==expected_full and(expected_full or report['assertions'][0]['status']!='passed'),{'expected_full_content':expected_full,'actual_full_content':ev[1],'reason':ev[2],'absence_status':report['assertions'][0]['status'],'environment_status':env['status'],'domain_binding':coverage_domain.verify_packet(n)})
 if mode=='positive':positive=(o,s,n)

o,s,n=positive
diagplan={'design_contract':{'platform':'ios'},'states':[s],'assertions':[{'id':'root','state':'start','kind':'control','target':{'identifier':'absent-target'},'property':'present','expected':True}]};diagreport={'rows':[{'id':'root','status':'failed'}]};empty=locator_diagnostics.diagnose(diagplan,diagreport,o,[],root=n);scan=locator_diagnostics.diagnose(diagplan,diagreport,o,config['source_roots'],root=n)
record('A10-root-propagation-production-scan',empty['items'][0]['full_content_complete']and scan['items'][0]['full_content_complete'],{'empty':empty,'production':scan})

for id,mode,prop,expected,wanted in[
 ('A11-late-presence','late','present',True,'passed'),('A12-late-unique','late','unique',True,'passed'),('A13-seen-late-contradicts-absence','late','present',False,'failed'),('A14-real-duplicate-then-one','duplicate','unique',True,'failed'),('A15-absent-all','absent','present',False,'passed'),('A16-mixed-epoch','mixed','present',True,'unassessed')]:
 folder=base/id;folder.mkdir();oo=copy.deepcopy(o);root=attach_packet(folder/'packet',config,domainplan,value,arm,base/'A01-approved-runtime-shape-positive/source/images')
 if mode in{'late','mixed'}:oo['snapshots'][-1]['nodes'].append({'index':70,'parent_index':0,'identifier':'semantic-target','label':'late','role_raw':48,'frame':rect(80,510,20,20),'fully_within_viewport':True,'intersects_viewport':True})
 if mode=='duplicate':
  for i,snap in enumerate(oo['snapshots']):
   snap['nodes'].append({'index':70,'parent_index':0,'identifier':'semantic-target','label':'present','role_raw':48,'frame':rect(80,40,20,20),'fully_within_viewport':True,'intersects_viewport':True})
   if i==0:snap['nodes'].append({'index':71,'parent_index':0,'identifier':'semantic-target','label':'second','role_raw':48,'frame':rect(120,80,20,20),'fully_within_viewport':True,'intersects_viewport':True})
 if mode=='mixed':oo['snapshots'][1]['binding']['event_revision']=99
 plan={'version':1,'states':[s],'required_assertion_ids':['quantifier'],'assertions':[{'id':'quantifier','state':'start','kind':'control','target':{'identifier':'semantic-target'},'property':prop,'expected':expected}]};report=native_checks.evaluate(plan,oo,'ios',root=root);save(folder/'observation.json',oo);save(folder/'evaluated.json',report);actual=report['assertions'][0]['status']
 record(id,actual==wanted,{'expected_status':wanted,'actual_status':actual,'state_complete':report['states']['start']['complete'],'assertion':report['assertions'][0]})

folder=base/'A17-coverage-is-not-native-geometry-equality';folder.mkdir();oo=copy.deepcopy(o)
for snap in oo['snapshots']:snap['nodes'][1]['frame']['width']=30.000000000000007
root=attach_packet(folder/'packet',config,domainplan,value,arm,base/'A01-approved-runtime-shape-positive/source/images');plan={'version':1,'states':[s],'required_assertion_ids':['raw-width'],'assertions':[{'id':'raw-width','state':'start','kind':'geometry','target':{'identifier':'anchor-a'},'property':'width','basis':'semantic','expected':30,'op':'eq'}]};report=native_checks.evaluate(plan,oo,'ios',root=root);save(folder/'observation.json',oo);save(folder/'evaluated.json',report)
record('A17-coverage-is-not-native-geometry-equality',report['states']['start']['complete']and report['assertions'][0]['status']=='failed',{'report':report,'raw_width':30.000000000000007,'strict_expected':30})
save(ROOT/'raw'/(a.arm+'-admitted-runtime-results.json'),rows)
