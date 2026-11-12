from pathlib import Path
import copy, hashlib, json, os, sys, time, zlib, struct, uuid
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT.parents[1]/'candidate-v13.0'
sys.path.insert(0,str(CANDIDATE/'scripts'))
import design_contract as d

def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n');return p

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def png(path, rgb=(60,110,180)):
 def chunk(k,v):return struct.pack('!I',len(v))+k+v+struct.pack('!I',zlib.crc32(k+v)&0xffffffff)
 Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',2,2,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+bytes(rgb)*2)*2))+chunk(b'IEND',b''))

def project(name, *, broken=False, source_duty=False, pool=None):
 base=ROOT/'work'/name;base.mkdir(exist_ok=False)
 roots=[]
 for platform in ['ios','android','shared']:
  p=base/'production'/platform;p.mkdir(parents=True);roots.append(str(p))
  (p/('Component.swift' if platform=='ios' else 'Component.kt' if platform=='android' else 'Shared.txt')).write_text('Broken\n' if broken and platform!='shared' else 'Ready\n')
 # Same basename in different roots deliberately tests resolved namespace identity.
 for p in roots[:2]:(Path(p)/'identity.txt').write_text('same basename; different platform namespace\n')
 for platform in ['ios','android']:
  b=base/platform;b.mkdir();bridge=b/'bridge.txt';bridge.write_text('neutral simulated collector bridge\n')
  fixture={'fixtures':[{'marker':'neutral-fixture-0'}]}
  save(b/'fixtures.json',fixture)
  env={'width':100,'height':100,'direction':'ltr','theme':'light',('dynamic_type' if platform=='ios' else 'font_scale'):('large' if platform=='ios' else 1)}
  save(b/'environment.json',env)
  states=[{'id':'opening','input_index':0,'after_action':0,'coverage':'full_content'},{'id':'second','input_index':0,'after_action':1,'coverage':'full_content'}]
  actions=[{'type':'checkpoint','state_id':s['id']} for s in states]
  facts={'label':{'value':'Ready','unit':'string'},'obligations':[{'id':'visible-neutral-label','clause':'The neutral label is Ready in each declared state.','priority':'must','states':['opening','second'],'risk':'content'}],
   'launch':{'fixtures_sha256':d.digest(fixture),'bridge_sha256':sha(bridge),'scenario':'neutral','platform':platform},
   'capture_validity':{'scope':'deterministic_component_fixture','max_age_seconds':3600,'reset':'fresh_native_fixture','external_state':'all_dependencies_pinned'}}
  if source_duty:facts['responsibilities']=[{'id':'source-duty','clause':'The neutral source retains the Ready marker.','priority':'must','owner':'component','method':'source','subject':'production-label','rule_ids':[]}]
  save(b/'facts.json',facts)
  contract={'version':1,'design_owner':'independent-review-1','approval_reference':'neutral-controller-checks-only; no native or business claim','sources':[{'id':'neutral','path':'facts.json','sha256':sha(b/'facts.json')}],
   'required_rule_ids':['label'],'rules':[{'id':'label','kind':'control','target':'label','property':'label','op':'eq'}],
   'scenarios':{'neutral':{'states':states,'actions':actions,'values':{'label':{s['id']:{p:{'source':'neutral','pointer':'/label'} for p in ['ios','android']} for s in states}}}}}
  save(b/'contract.json',contract);lock=d.seal(b/'contract.json',b);save(b/'lock.json',lock)
  plan,_=d.compile_contract(lock,d.digest(lock),'neutral',platform,{'label':{'identifier':'neutral-label'}},actions);save(b/'plan.json',plan)
  routes={'version':1,'index':{'source':'neutral','pointer':'/obligations'},'routes':{'visible-neutral-label':{'rule_ids':['label'],'reason':'Both declared checkpoints require the sealed label.','regression_obligations':[]}}};save(b/'routes.json',routes)
  native={'simulator':'managed'} if platform=='ios' else {'project':str(base/'android-project')}
  if platform=='android':
   ap=base/'android-project';ap.mkdir();(ap/'build.gradle.kts').write_text('// neutral build option v1\n')
  config={'plan':str(b/'plan.json'),'design_lock':str(b/'lock.json'),'design_sha256':d.digest(lock),'routes':str(b/'routes.json'),'routes_sha256':d.digest(routes),'fixtures':str(b/'fixtures.json'),'bridge':str(bridge),'launch_ref':{'source':'neutral','pointer':'/launch'},
   'source_roots':roots,'platform_source_roots':{'ios':[roots[0]],'android':[roots[1]],'shared':[roots[2]]},'native_options':native,'environment':str(b/'environment.json'),'environment_sha256':d.digest(env),
   'capture_validity_ref':{'source':'neutral','pointer':'/capture_validity'},'resources':{'root':str(base/'scratch'/platform),'min_free_bytes':0,'sample_seconds':0.1,'ios':{'device_type':'SIMULATED.phone','runtime':'SIMULATED.runtime'}},'workflow':{'root':str(base/'workflow'),'max_cycles':100}}
  if pool is not None:config['resources']['pool']=pool
  if source_duty:
   config.update(responsibility_ref={'source':'neutral','pointer':'/responsibilities'},evidence_subjects={'production-label':[str(Path(roots[0 if platform=='ios' else 1])/('Component.swift' if platform=='ios' else 'Component.kt'))]},source_review_store=str(base/'source-reviews'/platform))
  save(b/'config.json',config)
 return base

def simulated_collector(self,argv,*,env,stdout,timeout=None):
 # This replaces the SDK execution boundary only. Controller/reconstruction/checks are unchanged.
 if os.environ.get("REVIEW_COLLECTOR_FAIL"):raise OSError("SIMULATED primary collector failure")
 def arg(k):return argv[argv.index(k)+1]
 output=Path(arg('--output'));output.mkdir(parents=True,exist_ok=False)
 fixtures=d.load(Path(arg('--fixtures')));actions=d.load(Path(arg('--actions')))
 config=d.load(Path(os.environ['REVIEW_CONFIG']))
 platform=d.load(Path(config['plan']))['design_contract']['platform']
 selected=fixtures['execution_states'];defs=fixtures['execution_state_definitions']
 instance='SIMULATED-'+uuid.uuid4().hex
 binding={'instance':instance,'fixture_index':0,'input_sha256':d.digest(fixtures['fixtures'][0]),'event_revision':0}
 label=(Path(config['platform_source_roots'][platform][0])/('Component.swift' if platform=='ios' else 'Component.kt')).read_text().strip()
 expectation=d.load(Path(config['environment']))
 snapshots=[];captures=[];steps=[]
 for index,action in enumerate(actions):
  state=action.get('state_id');entry=next((v for v in selected if v['state_id']==state),None)
  image=None
  if os.environ.get('REVIEW_DROP_STATE')==state:entry=None
  if entry:
   si=len(snapshots);image='state-'+str(si)+'.png';png(output/image)
   node={'identifier':'neutral-label','label':label,'role':'text','intersects_viewport':True,'enabled':True,'node_id':1}
   snap={'state_id':state,'screenshot':image,'binding':binding,'binding_after_capture':binding,'capture_consistent':True,'nodes':[node]}
   if platform=='ios':snap.update(viewport={'x':0,'y':0,'width':100,'height':100},runtime={'content_frame':{'x':0,'y':0,'width':100,'height':100},'actual_environment':{k:expectation[k] for k in ['direction','theme','dynamic_type']}})
   else:snap.update(logical_viewport_dp={'width':100,'height':100},scroll_offset_dp=0,scroll_max_dp=0,viewport_height_dp=100)
   if os.environ.get('REVIEW_TORN_CAPTURE'):
    snap['capture_consistent']=False;snap['binding_after_capture']=dict(binding,instance='SIMULATED-FOREIGN-EPOCH')
   snapshots.append(snap)
   captures.append({'state_id':state,'after_action':index,'binding':binding,'snapshot_indices':[si],'top_reached':True,'bottom_reached':True,'stable_binding':True})
  steps.append({'action':action,'state_id':state,'outcome':'observed','binding_after':binding,'after':len(snapshots)-1,'guard':{'protocol':1,'depends_on':action['depends_on'],'conditions':[],'ready':True,'established':True,'binding':binding}})
 obs={'evidence_class':'SIMULATED','measurement_kind':'XCUI-SIMULATED' if platform=='ios' else 'SIMULATED','guard_protocol':1,'guard_platform':platform,'guard_actions':actions,'snapshots':snapshots,'state_captures':captures,'steps':steps,'execution_scope':fixtures['execution_scope']}
 if platform=='android':obs['configuration']={'direction':'Ltr','night_mode_mask':16,'font_scale':1}
 save(output/'observation.json',obs)
 save(output/'manifest.json',{'evidence_class':'SIMULATED','reset_contract':'fresh_native_fixture','native_test_count':1,'session':instance,'fixture_sha256':d.digest(fixtures)})
 (output/'original-native-result.txt').write_text('SIMULATED native result; no SDK executed; session='+instance+'\n')
 row={'evidence_class':'SIMULATED','argv':argv,'instance':instance,'config':os.environ['REVIEW_CONFIG'],'at_unix':time.time()}
 with (ROOT/'raw'/'simulated-collector-calls.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 stdout.write('SIMULATED collector boundary; no SDK execution\n');stdout.flush()
 return 0
