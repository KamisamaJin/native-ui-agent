"""SDK-free oracle controls. Synthetic evidence never enters production acceptance."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import oracle_common as oracle

def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False))
def load(p):return json.loads(p.read_text())

def synthetic(task,case,platform,out):
 root=D/task/('private' if case=='H1' else 'public');plan=load(root/'compiled'/case/platform/'plan.json');fixture=load(root/'compiled'/case/'fixtures.json');write(out/'fixtures.json',fixture)
 binding0={'fixture_index':0,'input_sha256':'input-zero','instance':'synthetic-session','event_revision':0,'pid':123}
 binding1=dict(binding0,fixture_index=1,input_sha256='input-one')
 snapshots=[];captures=[];steps=[{} for _ in range(7)];revision=0
 for st in plan['states']:
  sid=st['id'];specs=[a for a in plan['assertions'] if a['state']==sid];events=next((a['expected'] for a in specs if a['kind']=='event'),[])
  before=dict(binding1 if st['input_index'] else binding0,event_revision=revision)
  revision+=len(events);binding=dict(before,event_revision=revision)
  if sid=='replaced':binding=dict(binding1,event_revision=revision)
  nodes={};n=0
  for a in specs:
   if 'target' not in a or a['kind']=='manual':continue
   ident=a['target']['identifier']
   if a['kind']=='control' and a['property']=='present' and a['expected'] is False:continue
   if ident not in nodes:
    n+=1;nodes[ident]=dict(node_id=n,identifier=ident,label='',clickable=ident.split('.')[-1] in {'choiceA','choiceB','primary','extra','disclosure'},enabled=True,selected=False,intersects_viewport=True,fully_within_viewport=True,frame={'x':16,'y':20+n*50,'width':173,'height':56},bounds_dp=[16,20+n*50,189,76+n*50])
   node=nodes[ident]
   if a['kind']=='control' and a['property'] not in {'present','unique'}:node[a['property']]=a['expected']
   elif a['kind']=='text_layout':node[a['property']]=a['expected']
  # Detail absent checks must not create an otherwise unused node.
  for a in specs:
   if a['kind']=='control' and a['property']=='present' and not a['expected']:nodes.pop(a['target']['identifier'],None)
  groups=[{'selector':{'identifier':ident},'match_count':1,'semantic':node,'control':node if node['clickable'] else {},'resolution':'unique_native_control' if node['clickable'] else 'no_native_control'} for ident,node in nodes.items()]
  idx=len(snapshots);png=f'{sid}.png';Image.new('RGB',(10,10),'white').save(out/png)
  snap=dict(state_id=sid,binding=binding,capture_consistent=True,nodes=list(nodes.values()),control_groups=groups,screenshot=png,runtime={'content_frame':{'height':500},'actual_environment':{k:fixture[k] for k in ['theme','dynamic_type','direction']}},viewport={'y':0,'height':600},scroll_offset_dp=0,scroll_max_dp=0,viewport_height_dp=600)
  snap['runtime']['content_frame']['y']=0;snapshots.append(snap)
  captures.append(dict(state_id=sid,binding=binding,after_action=st['after_action'],snapshot_indices=[idx],top_reached=True,bottom_reached=True,stable_binding=True))
  action=st.get('stimulus_action',st['after_action'])
  stimulus='caller_update' if sid=='replaced' else 'activation';method='caller_fixture_update' if sid=='replaced' else 'xcui_tap' if platform=='ios' else 'compose_onclick'
  if sid=='replaced':before=dict(binding0,event_revision=revision)
  steps[action]=dict(state_id=sid,binding_after=binding,after=idx,immediate_after=idx,outcome='updated' if sid=='replaced' else 'tapped',callback_delta=events,dispatch=dict(attempted=True,succeeded=True,method=method,stimulus=stimulus,binding_before=before,event_start=before['event_revision'],event_end=binding['event_revision'],matches=1,native_controls=1,enabled=True))
 obs=dict(schema_version=3,snapshots=snapshots,state_captures=captures,steps=steps,configuration={'font_scale':fixture['fontScale'],'night_mode_mask':32 if fixture['theme']=='dark' else 16,'direction':fixture['direction']})
 write(out/'observation.json',obs);return obs

class OracleControls(unittest.TestCase):
 TASK='T1'
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=D);self.root=Path(self.temp.name);self.obs=synthetic(self.TASK,'P1','android',self.root)
 def tearDown(self):self.temp.cleanup()
 def grade(self,platform='android',manual=None):return oracle.grade_task(D/self.TASK,'P1',platform,self.root/'observation.json',manual=manual)
 def row(self,g,r,state='loaded'):return next(x for x in g['rows'] if x['requirement']==r and x['state']==state)
 def save(self):write(self.root/'observation.json',self.obs)
 def test_complete_denominator_and_positive_native_labels(self):
  g=self.grade();self.assertEqual(len(g['rows']),132);self.assertEqual(self.row(g,'title')['status'],'P');self.assertEqual(self.row(g,'details-copy')['status'],'N/A');self.assertEqual(self.row(g,'title-font-size')['status'],'P')
 def test_wrong_label_is_failure(self):
  self.obs['snapshots'][0]['nodes'][0]['label']='Corrupted title';self.save();self.assertEqual(self.row(self.grade(),'title')['status'],'F')
 def test_torn_state_binding_stays_unknown(self):
  self.obs['snapshots'][0]['binding']=dict(self.obs['snapshots'][0]['binding'],instance='wrong-instance');self.save();self.assertEqual(self.row(self.grade(),'title')['status'],'U')
 def test_duplicate_selector_never_passes(self):
  self.obs['snapshots'][0]['nodes'].append(copy.deepcopy(self.obs['snapshots'][0]['nodes'][0]));self.save();self.assertEqual(self.row(self.grade(),'title')['status'],'U')
 def test_native_font_corruption_fails(self):
  self.obs['snapshots'][0]['nodes'][0]['font_sp']=17;self.save();self.assertEqual(self.row(self.grade(),'title-font-size')['status'],'F')
 def test_missing_style_is_unknown(self):
  self.obs['snapshots'][0]['nodes'][0].pop('font_sp');self.save();self.assertEqual(self.row(self.grade(),'title-font-size')['status'],'U')
 def test_ios_style_never_borrowed_from_visual(self):
  self.obs=synthetic(self.TASK,'P1','ios',self.root);g=self.grade('ios');self.assertEqual(self.row(g,'title')['status'],'P');self.assertEqual(self.row(g,'title-font-size')['status'],'U')
 def test_disabled_stimulus_no_empty_callback_pass(self):
  self.obs['steps'][3]['dispatch'].update(attempted=False,succeeded=False,enabled=False);self.obs['steps'][3]['outcome']='blocked_disabled';self.save();self.assertEqual(self.row(self.grade(),'activation-callback','optioned')['status'],'U')
 def test_wrong_callback_after_real_dispatch_fails(self):
  step=self.obs['steps'][4];step['callback_delta']=['wrong'];self.save();self.assertEqual(self.row(self.grade(),'activation-callback','submitted')['status'],'F')
 def test_wrong_fixture_is_separate_input_failure(self):
  f=load(self.root/'fixtures.json');f['initial']['title']='Wrong input';write(self.root/'fixtures.json',f);g=self.grade();self.assertEqual(next(c for c in g['input_checks'] if c['id']=='caller-fixture')['status'],'F');self.assertEqual(self.row(g,'title')['status'],'U')
 def test_manual_without_original_png_hash_rejected(self):
  manual={'observation_sha256':oracle.sha(self.root/'observation.json'),'decisions':[{'id':'loaded/visual-composition','status':'passed','method':'visual','snapshot_indices':[0],'reason':'Synthetic test only','evidence':[{'path':'loaded.png','sha256':'0'*64}]}]}
  g=self.grade(manual=manual);self.assertEqual(self.row(g,'visual-composition')['status'],'U');self.assertTrue(any(c['status']=='F' for c in g['input_checks']))
 def test_claim_exactness_uncertainty_and_wrong_scope(self):
  g=self.grade();r=self.row(g,'title');claim={k:r[k] for k in ['case','platform','state','requirement','expected','unit']};claim['status']='P'
  self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'P')
  bad=dict(claim,expected='Different');self.assertEqual(oracle.match_claims(g,[bad])['claims'][0]['status'],'F')
  bad=dict(claim,case='H1');self.assertEqual(oracle.match_claims(g,[bad])['claims'][0]['status'],'F')
  g['rows'][0]['status']='U';self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'U')
 def test_pair_excludes_visual_and_preserves_native_denominator(self):
  a=self.grade();b=copy.deepcopy(a)
  for r in b['rows']:
   if r['class']=='visual':r['status']='F'
  c=oracle.compare_pair(a,b);self.assertEqual(c['denominator'],126);self.assertEqual(c['counts']['a'],c['counts']['b'])
 def test_failure_claim_supported_and_false_positive_rejected(self):
  self.obs['snapshots'][0]['nodes'][0]['label']='Corrupted title';self.save();g=self.grade();r=self.row(g,'title');claim={k:r[k] for k in ['case','platform','state','requirement','expected','unit']};claim['status']='F'
  self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'P')
  claim['status']='P';self.assertEqual(oracle.match_claims(g,[claim])['claims'][0]['status'],'F')
 def test_manual_original_state_png_can_be_reviewed(self):
  manual={'observation_sha256':oracle.sha(self.root/'observation.json'),'decisions':[{'id':'loaded/visual-composition','status':'failed','method':'visual','snapshot_indices':[0],'reason':'Synthetic visual failure control only','evidence':[{'path':'loaded.png','sha256':oracle.sha(self.root/'loaded.png')}]}]}
  g=self.grade(manual=manual);self.assertEqual(self.row(g,'visual-composition')['status'],'F');self.assertEqual(self.row(g,'title-font-size')['status'],'P')
 def test_full_visual_pass_requires_complete_original_sweep(self):
  self.obs['snapshots'][0]['runtime']['content_frame']['height']=1600;self.save()
  manual={'observation_sha256':oracle.sha(self.root/'observation.json'),'decisions':[{'id':'loaded/visual-composition','status':'passed','method':'visual','snapshot_indices':[0],'reason':'Synthetic incomplete-state positive control','evidence':[{'path':'loaded.png','sha256':oracle.sha(self.root/'loaded.png')}]}]}
  self.assertEqual(self.row(self.grade(manual=manual),'visual-composition')['status'],'U')
 def test_wrong_approved_plan_rejected(self):
  root=D/self.TASK/'public';plan=load(root/'compiled/P1/android/plan.json');plan['assertions'][0]['expected']='wrong';lock=load(root/'design-lock.json');digest=load(root/'approval.json')['design_lock_sha256']
  with self.assertRaises(ValueError):oracle.dc.verify_generated(plan,lock,digest,'android')
 def test_all_cases_platforms_have_fixed_full_rows(self):
  for case in ['P1','P2','H1']:
   for p in ['ios','android']:
    obs=synthetic(self.TASK,case,p,self.root);g=oracle.grade_task(D/self.TASK,case,p,self.root/'observation.json');self.assertEqual(len(g['rows']),132);self.assertEqual(len(set(r['id'] for r in g['rows'])),132)

if __name__=='__main__':unittest.main()
