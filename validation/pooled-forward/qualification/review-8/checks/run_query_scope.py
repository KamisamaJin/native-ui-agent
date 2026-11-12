import sys,argparse,copy,shutil
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import native_checks,coverage_domain,scroll_coverage
base=ROOT/'work'/a.arm/'query';base.mkdir(parents=True);rows=[];config,domainplan,lock=setup_config(base/'admission',arm);value=coverage_domain.prepare(config,domainplan,lock)
oldarm='candidate-v13.6'if a.arm.startswith('candidate')else'baseline-v12.6-common-3';old=ROOT.parent/'review-7/work'/oldarm/'delta/ABI-A01-approved-runtime-shape-positive'
def record(name,ok,detail):
 row={'id':name,'status':'P'if ok else'F','arm':a.arm,'evidence_class':'HOST evaluator/files/PNG with SIMULATED native query/source/runtime metadata; zero SDK','detail':detail};rows.append(row);save(base/(name+'-result.json'),row)
 if not ok:
  with(ROOT/'first-failures'/(a.arm+'--'+name+'.json')).open('x')as f:json.dump(row,f,indent=2)
 print(a.arm+' '+name+': '+row['status'],flush=True)
def ios(folder,local=False):
 o=load(old/'observation.json');s=load(old/'state.json');n=attach_packet(folder/'packet',config,domainplan,value,arm,old/'packet/native')
 for snap in o['snapshots']:
  for node in snap['nodes']:
   node['index']+=1;node['parent_index']=node['parent_index']+1 if node['parent_index']>=0 else 0
  snap['nodes'].insert(0,{'index':0,'parent_index':-1,'identifier':'','role_raw':2,'role':'Application','frame':copy.deepcopy(snap['app_frame']),'intersects_viewport':True,'fully_within_viewport':True})
  snap['performance']={'native_query_mode':'single_public_snapshot'}
 if local:
  binding=copy.deepcopy(o['state_captures'][0]['binding']);o['state_captures']=[];s['coverage']='targets';o['steps']=[{'state_id':'start','after':0,'immediate_after':0,'binding_after':binding,'observation_set':{'state_id':'start','after_action':0,'binding':binding,'binding_after_observation':binding,'binding_stable':True,'snapshot_indices':[0]}}]
 save(folder/'QUERY-ABI.json',{'source_observation':str(old/'observation.json'),'source_sha256':sha(old/'observation.json'),'authorship':'Independent synthetic full-tree/query ABI: public Swift traversal root index0/role2,parent-1; original IDs shifted and actual parent links updated; native_query_mode single_public_snapshot. No actual native evidence.','native_runs':0,'original_PNGs_unchanged':True})
 return o,s,n
def android(folder,local=False):
 binding={'pid':881908,'instance':'SIMULATED-compose-query','fixture_index':0,'input_sha256':canonical({'fixture':'review8-native-semantics'}),'event_revision':0};w,h=390,600;n=folder/'native';n.mkdir();Image.new('RGBA',(w,h),(14,71,93,255)).save(n/'frame.png')
 def node(id,parent,identifier,x,y,width,height,clickable=False):return {'node_id':id,'parent_id':parent,'identifier':identifier,'label':identifier,'native_text':identifier,'role':'Button'if clickable else'','clickable':clickable,'enabled':True,'selected':False,'intersects_viewport':True,'fully_visible':True,'native_geometry':{'version':1,'provider':'compose_semantics_int_size','coordinate_unit':'px','density':1.0,'position_px':[x,y],'size_px':[width,height]},'unclipped_bounds_dp':[x,y,x+width,y+height],'bounds_dp':[x,y,x+width,y+height],'touch_bounds_dp':[x,y,x+width,y+height]}
 nodes=[node(0,-1,'',0,0,w,h),node(1,0,'query-target',20,20,30,40,True)];snap={'index':0,'state_id':'start','name':'native-frame','screenshot':'frame.png','binding':copy.deepcopy(binding),'binding_after_capture':copy.deepcopy(binding),'capture_consistent':True,'native_viewport_px':{'width':w,'height':h,'density':1.0},'logical_viewport_dp':{'width':w,'height':h},'screenshot_pixels':{'width':w,'height':h},'scroll_offset_dp':0,'scroll_max_dp':0,'viewport_height_dp':h,'runtime':copy.deepcopy(binding),'nodes':nodes};s={'id':'start','input_index':0,'after_action':0,'coverage':'targets'if local else'full_content'};o={'schema_version':2,'coverage_protocol':1,'evidence_class':'SIMULATED','snapshots':[snap],'state_captures':[{'state_id':'start','after_action':0,'binding':copy.deepcopy(binding),'snapshot_indices':[0],'top_reached':True,'bottom_reached':True,'stable_binding':True}],'status':'passed'}
 if local:
  o['state_captures']=[];o['steps']=[{'state_id':'start','after':0,'immediate_after':0,'binding_after':binding,'observation_set':{'state_id':'start','after_action':0,'binding':binding,'binding_after_observation':binding,'binding_stable':True,'snapshot_indices':[0]}}]
 save(folder/'QUERY-ABI.json',{'authorship':'Independent SIMULATED Compose raw unmerged semantics ABI from public NativeObserverTest.kt capture: full node_id/parent_id tree, native viewport and integer-size geometry','native_runs':0})
 return o,s,n
def target(o,platform):return 'anchor-a'if platform=='ios'else'query-target'
def evaluate(name,platform,local,prop,expected,wanted,mutator=None,wanted_complete=None):
 folder=base/name;folder.mkdir();o,s,n=(ios if platform=='ios'else android)(folder,local);selector={'identifier':target(o,platform)}
 if mutator:mutator(o,s,n,selector)
 plan={'version':1,'states':[s],'required_assertion_ids':['quantifier'],'assertions':[{'id':'quantifier','state':'start','kind':'control','target':selector,'property':prop,'expected':expected}]};report=native_checks.evaluate(plan,o,platform,root=n);save(folder/'observation.json',o);save(folder/'state.json',s);save(folder/'plan.json',plan);save(folder/'evaluated.json',report);actual=report['assertions'][0]['status'];complete=report['states']['start']['complete'];qc=[native_checks.native_query_complete(snap,selector,platform)for snap in o['snapshots']]
 record(name,actual==wanted and(wanted_complete is None or complete==wanted_complete),{'platform':platform,'scope':s['coverage'],'expected_status':wanted,'actual_status':actual,'complete':complete,'native_query_complete_per_snapshot':qc,'assertion':report['assertions'][0],'state_reason':report['states']['start']['reason']})
def no_tree(o,s,n,t):
 for snap in o['snapshots']:
  found=[node for node in snap['nodes']if node.get('identifier')==t['identifier']];snap['nodes']=found[:1];snap.pop('performance',None)
def explicit(o,s,n,t,resolution='no_native_control',count=1):
 for snap in o['snapshots']:
  nodes=[node for node in snap['nodes']if node.get('identifier')==t['identifier']];semantic=copy.deepcopy(nodes[0])if nodes else{};snap['control_groups']=[{'selector':copy.deepcopy(t),'match_count':count,'resolution':resolution,**({'semantic':semantic}if semantic else{})}]
def missing(o,s,n,t):
 for snap in o['snapshots']:snap['nodes']=[node for node in snap['nodes']if node.get('identifier')!=t['identifier']]
def duplicate(o,s,n,t,same_id=False):
 for snap in o['snapshots']:
  found=[node for node in snap['nodes']if node.get('identifier')==t['identifier']]
  if found:
   second=copy.deepcopy(found[0]);key='index'if'index'in second else'node_id'
   if not same_id:
    second[key]=max(node[key]for node in snap['nodes'])+1
    if'frame'in second:second['frame']['x']+=50
    else:second['native_geometry']['position_px'][0]+=50
   snap['nodes'].append(second)
def mixed(o,s,n,t):o['snapshots'][0]['binding_after_capture']['event_revision']=99
def incomplete(o,s,n,t):
 if'__observer.bottom'in [node.get('identifier')for node in o['snapshots'][-1]['nodes']]:o['snapshots'][-1]['bottom_boundary']['hittable']=False
 else:o['state_captures'][0]['bottom_reached']=False
def cycle(o,s,n,t):
 for snap in o['snapshots']:
  if'index'in snap['nodes'][0]:
   start=max(node['index']for node in snap['nodes'])+1;snap['nodes'] += [{'index':start,'parent_index':start+1,'identifier':'','role_raw':1},{'index':start+1,'parent_index':start,'identifier':'','role_raw':1}]
  else:
   x=copy.deepcopy(snap['nodes'][0]);y=copy.deepcopy(x);x.update(node_id=8,parent_id=9);y.update(node_id=9,parent_id=8);snap['nodes'] += [x,y]
def android_minimal(o,s,n,t):
 for snap in o['snapshots']:snap['nodes']=[{'node_id':1,'parent_id':-1,'identifier':t['identifier'],'intersects_viewport':True,'native_geometry':{'provider':'compose_semantics_int_size'}}]

for platform in['ios','android']:
 prefix=platform+'-'
 evaluate(prefix+'full-native-query-positive',platform,False,'unique',True,'passed',wanted_complete=True)
 evaluate(prefix+'target-native-query-positive',platform,True,'unique',True,'passed',wanted_complete=False)
 evaluate(prefix+'unproven-singleton',platform,True,'unique',True,'unassessed',no_tree,False)
 evaluate(prefix+'incomplete-full-unique',platform,False,'unique',True,'unassessed',incomplete,False)
 evaluate(prefix+'incomplete-full-presence',platform,False,'present',True,'passed',incomplete,False)
 evaluate(prefix+'complete-no-matches-absence',platform,False,'present',False,'passed',missing,True)
 evaluate(prefix+'incomplete-no-matches-absence',platform,False,'present',False,'unassessed',lambda o,s,n,t:(missing(o,s,n,t),incomplete(o,s,n,t)),False)
 evaluate(prefix+'distinct-native-duplicate',platform,True,'unique',True,'failed',duplicate,False)
 evaluate(prefix+'same-entity-duplicate-record',platform,True,'unique',True,'unassessed',lambda o,s,n,t:duplicate(o,s,n,t,True),False)
 evaluate(prefix+'mixed-epoch',platform,True,'present',True,'unassessed',mixed,False)
 evaluate(prefix+'cycle-not-complete-native-query',platform,True,'unique',True,'unassessed',cycle,False)
evaluate('ios-explicit-native-query', 'ios',True,'unique',True,'passed',lambda o,s,n,t:(no_tree(o,s,n,t),explicit(o,s,n,t)),False)
evaluate('ios-unsupported-query-resolution','ios',True,'unique',True,'unassessed',lambda o,s,n,t:(no_tree(o,s,n,t),explicit(o,s,n,t,'singleton_only_not_enumerated')),False)
evaluate('ios-query-header-missing-conflicts-with-native-tree','ios',False,'present',False,'unassessed',lambda o,s,n,t:explicit(o,s,n,t,'missing',0),True)
evaluate('android-provider-string-is-not-query-proof','android',True,'unique',True,'unassessed',android_minimal,False)
save(ROOT/'raw'/(a.arm+'-query-scope-results.json'),rows)
