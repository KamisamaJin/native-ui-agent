"""SDK-free controls over arbitrary approved native targets; no production mutation."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import oracle_common as oracle

def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False))

def synthetic(task,case,platform,out):
 source=D/task/('private' if case=='H1' else 'public');plan=read(source/'compiled'/case/platform/'plan.json');fixture=read(source/'compiled'/case/'fixtures.json');write(out/'fixtures.json',fixture)
 steps=[{} for _ in plan['design_contract']['base_actions']];captures=[];snapshots=[];revision=0
 for state in plan['states']:
  sid=state['id'];specs=[a for a in plan['assertions'] if a['state']==sid];ev=next((a for a in specs if a['kind']=='event'),None);events=ev['expected'] if ev else []
  before=dict(fixture_index=state['input_index'],input_sha256='input-one' if state['input_index'] else 'input-zero',instance='synthetic-native-session',event_revision=revision,pid=123)
  revision+=len(events);binding=dict(before,event_revision=revision)
  absent={a['target']['identifier'] for a in specs if a['kind']=='control' and a['property']=='present' and not a['expected']}
  clickable={a['target']['identifier'] for a in specs if a['kind']=='geometry' or (a['kind']=='control' and a['property'] in ['selected','enabled'])}
  clickable|={a['target']['identifier'] for a in plan['design_contract']['base_actions'] if 'target' in a}
  nodes={};n=0
  for a in specs:
   if 'target' not in a or a['kind']=='manual':continue
   identity=a['target']['identifier']
   if identity in absent:continue
   if identity not in nodes:
    n+=1;yy=10+n*16;nodes[identity]=dict(node_id=n,identifier=identity,label='',enabled=True,selected=False,clickable=identity in clickable,intersects_viewport=True,fully_within_viewport=True,frame={'x':16,'y':yy,'width':100,'height':48},unclipped_bounds_dp=[16,yy,116,yy+48])
   node=nodes[identity]
   if a['kind']=='control' and a['property'] not in ['present','unique']:node[a['property']]=a['expected']
   if a['kind']=='text_layout':node[a['property']]=a['expected']
   if a['kind']=='geometry':
    node['frame'][a['property']]=a['expected'];f=node['frame'];node['unclipped_bounds_dp']=[f['x'],f['y'],f['x']+f['width'],f['y']+f['height']]
  groups=[dict(selector={'identifier':i},match_count=1,semantic=copy.deepcopy(node),control=copy.deepcopy(node) if node['clickable'] else {},resolution='unique_native_control' if node['clickable'] else 'no_native_control') for i,node in nodes.items()]
  ix=len(snapshots);png=sid+'.png';Image.new('RGB',(12,12),'white').save(out/png)
  snapshots.append(dict(state_id=sid,binding=copy.deepcopy(binding),capture_consistent=True,nodes=list(nodes.values()),control_groups=groups,screenshot=png,runtime={'content_frame':{'y':0,'height':500},'actual_environment':{k:fixture[k] for k in ['theme','dynamic_type','direction']}},viewport={'y':0,'height':600},scroll_offset_dp=0,scroll_max_dp=0,viewport_height_dp=600))
  captures.append(dict(state_id=sid,binding=copy.deepcopy(binding),after_action=state['after_action'],snapshot_indices=[ix],top_reached=True,bottom_reached=True,stable_binding=True))
  action=state.get('stimulus_action',state['after_action']);base=plan['design_contract']['base_actions'][action];update=base['type']=='apply_next_fixture';enabled=nodes.get(base.get('target',{}).get('identifier'),{}).get('enabled',True)
  if update:before=dict(before,fixture_index=0,input_sha256='input-zero')
  method='caller_fixture_update' if update else 'xcui_tap' if platform=='ios' else 'compose_onclick'
  steps[action]=dict(state_id=sid,binding_after=copy.deepcopy(binding),after=ix,immediate_after=ix,outcome='updated' if update else 'tapped' if enabled else 'blocked_disabled',callback_delta=events,dispatch=dict(attempted=enabled,succeeded=enabled,method=method,stimulus='caller_update' if update else 'activation',binding_before=before,event_start=before['event_revision'],event_end=binding['event_revision'],matches=1,native_controls=1,enabled=enabled))
 obs=dict(schema_version=3,snapshots=snapshots,state_captures=captures,steps=steps,configuration=dict(font_scale=fixture['fontScale'],night_mode_mask=32 if fixture['theme']=='dark' else 16,direction=fixture['direction']))
 write(out/'observation.json',obs);return obs

class NewTaskControls(unittest.TestCase):
 TASK='T2'
 def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=D);self.root=Path(self.temp.name);self.obs=synthetic(self.TASK,'P1','android',self.root)
 def tearDown(self):self.temp.cleanup()
 def grade(self,platform='android',manual=None):return oracle.grade_task(D/self.TASK,'P1',platform,self.root/'observation.json',manual=manual)
 def row(self,g,requirement,state='loaded'):return next(r for r in g['rows'] if r['state']==state and r['requirement']==requirement)
 def save(self):write(self.root/'observation.json',self.obs)
 def title_node(self):return next(n for n in self.obs['snapshots'][0]['nodes'] if n['identifier'].endswith('.title'))
 def test_full_approved_denominator(self):
  g=self.grade();self.assertEqual(len(g['rows']),132);self.assertEqual(self.row(g,'title')['status'],'P');self.assertEqual(self.row(g,'title-font-size')['status'],'P');self.assertEqual(len({r['id'] for r in g['rows']}),132)
 def test_all_cases_platforms_arbitrary_target_structure(self):
  for case in ['P1','P2','H1']:
   for platform in ['ios','android']:
    synthetic(self.TASK,case,platform,self.root);g=oracle.grade_task(D/self.TASK,case,platform,self.root/'observation.json');self.assertEqual(len(g['rows']),132);self.assertEqual(self.row(g,'title')['status'],'P')
 def test_wrong_title_is_native_failure(self):self.title_node()['label']='Corrupted';self.save();self.assertEqual(self.row(self.grade(),'title')['status'],'F')
 def test_wrong_font_is_native_failure(self):self.title_node()['font_sp']=19;self.save();self.assertEqual(self.row(self.grade(),'title-font-size')['status'],'F')
 def test_missing_font_is_unknown(self):self.title_node().pop('font_sp');self.save();self.assertEqual(self.row(self.grade(),'title-font-size')['status'],'U')
 def test_ios_style_remains_unknown(self):synthetic(self.TASK,'P1','ios',self.root);g=self.grade('ios');self.assertEqual(self.row(g,'title-font-size')['status'],'U')
 def test_wrong_derived_summary_fails(self):
  node=next(n for n in self.obs['snapshots'][0]['nodes'] if n['identifier'].endswith('.summary'));node['label']='Wrong calculation';self.save();req='derived-load' if self.TASK=='T2' else 'completion-summary';self.assertEqual(self.row(self.grade(),req)['status'],'F')
 def test_geometry_uses_actual_native_box(self):
  g=self.grade();self.assertEqual(self.row(g,'primary-height')['status'],'P');node=next(n for n in self.obs['snapshots'][0]['nodes'] if n['identifier'].endswith('.primary'));node['unclipped_bounds_dp'][3]+=3;self.save();self.assertEqual(self.row(self.grade(),'primary-height')['status'],'F')
 def test_torn_binding_unknown(self):self.obs['snapshots'][0]['binding']['instance']='other';self.save();self.assertEqual(self.row(self.grade(),'title')['status'],'U')
 def test_duplicate_target_unknown(self):self.obs['snapshots'][0]['nodes'].append(copy.deepcopy(self.title_node()));self.save();self.assertEqual(self.row(self.grade(),'title')['status'],'U')
 def test_unexecuted_activation_never_empty_callback_pass(self):
  state='leveled' if self.TASK=='T2' else 'reasoned';idx=1 if self.TASK=='T2' else 2;self.obs['steps'][idx]['dispatch'].update(attempted=False,succeeded=False);self.obs['steps'][idx]['outcome']='blocked_disabled';self.save();self.assertEqual(self.row(self.grade(),'activation-callback',state)['status'],'U')
 def test_wrong_confirm_receipt_fails(self):
  ix=4 if self.TASK=='T2' else 5;self.obs['steps'][ix]['callback_delta']=['wrong'];self.save();self.assertEqual(self.row(self.grade(),'activation-callback','submitted')['status'],'F')
 def test_caller_update_has_own_success_proof(self):self.assertEqual(self.row(self.grade(),'replacement-callback','replaced')['status'],'P')
 def test_fixture_mismatch_separate_and_withholds_native_pass(self):
  fixture=read(self.root/'fixtures.json');fixture['initial']['title']='Wrong caller';write(self.root/'fixtures.json',fixture);g=self.grade();self.assertEqual(next(i for i in g['input_checks'] if i['id']=='caller-fixture')['status'],'F');self.assertEqual(self.row(g,'title')['status'],'U')
 def manual(self,good=True,passed=False):return dict(observation_sha256=oracle.sha(self.root/'observation.json'),decisions=[dict(id='loaded/visual-composition',status='passed' if passed else 'failed',method='visual',snapshot_indices=[0],reason='Synthetic control only',evidence=[dict(path='loaded.png',sha256=oracle.sha(self.root/'loaded.png') if good else '0'*64)])])
 def test_manual_original_state_png_supported(self):g=self.grade(manual=self.manual());self.assertEqual(self.row(g,'visual-composition')['status'],'F');self.assertEqual(self.row(g,'title-font-size')['status'],'P')
 def test_manual_wrong_original_hash_rejected(self):self.assertEqual(self.row(self.grade(manual=self.manual(False)),'visual-composition')['status'],'U')
 def test_full_layout_manual_pass_requires_full_coverage(self):self.obs['snapshots'][0]['runtime']['content_frame']['height']=1500;self.save();self.assertEqual(self.row(self.grade(manual=self.manual(passed=True)),'visual-composition')['status'],'U')
 def test_exact_claim_matching_and_uncertainty(self):
  self.title_node()['label']='Corrupted';self.save();g=self.grade();r=self.row(g,'title');claim={k:r[k] for k in ['case','platform','state','requirement','expected','unit']};claim['status']='F';self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'P');self.assertEqual(oracle.match_claims(g,[dict(claim,unit='dp')])['claims'][0]['status'],'F');self.assertEqual(oracle.match_claims(g,[dict(claim,case='H1')])['claims'][0]['status'],'F');g['rows'][0]['status']='U';self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'U')
 def test_false_defect_claim_rejected(self):
  g=self.grade();r=self.row(g,'title');claim={k:r[k] for k in ['case','platform','state','requirement','expected','unit']};claim['status']='F';self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'F')
 def test_pair_excludes_visual_without_dropping_unknowns(self):
  a=self.grade();b=copy.deepcopy(a)
  for r in b['rows']:
   if r['class']=='visual':r['status']='F'
  pair=oracle.compare_pair(a,b);self.assertEqual(pair['denominator'],126);self.assertEqual(pair['counts']['a'],pair['counts']['b'])
 def test_changed_expected_plan_rejected(self):
  source=D/self.TASK/'public';plan=read(source/'compiled/P1/android/plan.json');plan['assertions'][0]['expected']='Changed';lock=read(source/'design-lock.json');digest=read(source/'approval.json')['design_lock_sha256']
  with self.assertRaises(ValueError):oracle.dc.verify_generated(plan,lock,digest,'android')
 def test_conditional_absence_has_independent_rule(self):
  rid='overload-presence' if self.TASK=='T2' else 'care-category-presence';self.assertEqual(self.row(self.grade(),rid)['status'],'P')
