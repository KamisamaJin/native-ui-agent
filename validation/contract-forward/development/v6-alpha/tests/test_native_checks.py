import importlib.util,json,tempfile,unittest,hashlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('native_checks',Path(__file__).resolve().parents[1]/'scripts/native_checks.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class NativeChecks(unittest.TestCase):
 def snapshot(self,enabled=False):
  selector={'identifier':'row'};semantic={'identifier':'row','role_raw':1,'enabled':True,'selected':True,'label':'Context row','intersects_viewport':True};control={'role_raw':9,'enabled':enabled,'selected':False,'hittable':True,'frame':{'width':100,'height':48}}
  return {'screenshot':'state.png','binding':{'fixture_index':0,'input_sha256':'abc','event_revision':0},'runtime':{'content_frame':{'y':0,'height':900}},'viewport':{'y':0,'height':600},'control_groups':[{'selector':selector,'match_count':1,'semantic':semantic,'control':control,'resolution':'unique_native_control'}]}
 def observation(self):
  a=self.snapshot();b=self.snapshot();b['runtime']={'content_frame':{'y':-300,'height':900}}
  return {'snapshots':[a,b],'state_captures':[{'state_id':'initial','binding':a['binding'],'snapshot_indices':[0,1],'top_reached':True,'bottom_reached':True,'stable_binding':True,'complete':True,'after_action':-1}]}
 def plan(self,expected=False,prop='enabled'):
  return {'version':1,'states':[{'id':'initial','input_index':0,'after_action':-1}],'assertions':[{'id':'state','state':'initial','kind':'control','target':{'identifier':'row'},'property':prop,'expected':expected}]}
 def test_container_enabled_is_not_control_enabled(self):
  result=m.evaluate(self.plan(),self.observation(),'ios');self.assertEqual(result['counts'],{'passed':1,'failed':0,'unassessed':0})
  result=m.evaluate(self.plan(True),self.observation(),'ios');self.assertEqual(result['counts']['failed'],1)
 def test_compound_selected_trait_not_false_leaf_error(self):
  result=m.evaluate(self.plan(True,'selected'),self.observation(),'ios');self.assertEqual(result['counts']['passed'],1)
 def test_no_spatial_guess_for_old_flat_tree(self):
  o=self.observation()
  for s in o['snapshots']:s['nodes']=[s['control_groups'][0]['semantic']];s.pop('control_groups')
  self.assertEqual(m.evaluate(self.plan(),o,'ios')['counts']['unassessed'],1)
 def test_ambiguous_leaf_is_unknown_not_first_child(self):
  o=self.observation()
  for s in o['snapshots']:s['control_groups'][0]['resolution']='ambiguous_native_controls';s['control_groups'][0].pop('control')
  self.assertEqual(m.evaluate(self.plan(),o,'ios')['counts']['unassessed'],1)
 def test_state_union_recomputed_not_trusting_complete_boolean(self):
  o=self.observation();o['snapshots'][1]['runtime']['content_frame']['y']=-750
  self.assertFalse(m.state_evidence(o,{'id':'initial','input_index':0})[1])
 def test_input_and_callback_epoch_cannot_borrow_other_state(self):
  o=self.observation();o['snapshots'][1]['binding']=dict(o['snapshots'][1]['binding'],event_revision=1)
  self.assertEqual(m.evaluate(self.plan(),o,'ios')['counts']['unassessed'],1)
  o=self.observation();p=self.plan();p['states'][0]['input_index']=1
  self.assertEqual(m.evaluate(p,o,'ios')['counts']['unassessed'],1)
 def test_native_hierarchy_image_epoch_drift_is_unassessed(self):
  o=self.observation();o['snapshots'][1]['capture_consistent']=False
  self.assertEqual(m.evaluate(self.plan(),o,'ios')['counts']['unassessed'],1)
 def test_physical_touch_width_not_inferred_from_ax(self):
  self.assertEqual(m.evaluate(self.plan(44,'touch_width'),self.observation(),'ios')['counts']['unassessed'],1)
 def test_unexecuted_callback_does_not_become_failure(self):
  o=self.observation();o['steps']=[{'outcome':'unavailable','callback_delta':[],'binding_after':{'fixture_index':0}}];p=self.plan();p['assertions']=[{'id':'event','kind':'event','state':'initial','action_index':0,'expected':['done']}]
  self.assertEqual(m.evaluate(p,o,'ios')['counts']['unassessed'],1)
 def test_missing_contract_assertion_is_rejected(self):
  p=self.plan();p['required_assertion_ids']=['state','forgotten']
  with self.assertRaises(ValueError):m.evaluate(p,self.observation(),'ios')
 def test_manual_review_binds_actual_image_state_and_full_coverage(self):
  o=self.observation();p=self.plan();p['assertions']=[{'id':'visual','kind':'manual','state':'initial','allowed_methods':['visual']}]
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);image=root/'state.png';image.write_bytes(b'real image bytes');manual={'observation_sha256':'obs','decisions':[{'id':'visual','method':'visual','status':'passed','reason':'Compared current state','snapshot_indices':[0,1],'evidence':[{'path':'state.png','sha256':m.sha(image)}]}]}
   self.assertEqual(m.evaluate(p,o,'ios',manual,root,'obs')['counts']['passed'],1)
   o['snapshots'][1]['runtime']['content_frame']['y']=-750
   self.assertEqual(m.evaluate(p,o,'ios',manual,root,'obs')['counts']['unassessed'],1)
   with self.assertRaises(ValueError):m.evaluate(p,o,'ios',manual,root,'foreign')
 def test_target_action_checkpoint_needs_no_whole_body_sweep(self):
  o=self.observation();o['state_captures']=[];o['snapshots'][1]['state_id']='action-0';o['steps']=[{'state_id':'action-0','after':1,'binding_after':o['snapshots'][1]['binding'],'outcome':'tapped','callback_delta':[{'event':'done'}]}]
  before={'pid':123,'instance':'session','fixture_index':0,'input_sha256':'abc','event_revision':0};after=dict(before,event_revision=1)
  o['snapshots'][1]['binding']=after;o['steps'][0]['binding_after']=after
  o['steps'][0]['dispatch']={'attempted':True,'succeeded':True,'method':'xcui_tap','stimulus':'activation','binding_before':before,'event_start':0,'event_end':1,'matches':1,'native_controls':1,'enabled':True}
  p={'version':1,'states':[{'id':'action-0','input_index':0,'after_action':0,'coverage':'target'}],'assertions':[{'id':'event','state':'action-0','kind':'event','action_index':0,'expected':['done']}]}
  r=m.evaluate(p,o,'ios');self.assertEqual(r['counts']['passed'],1);self.assertFalse(r['states']['action-0']['complete'])
  o['snapshots'][1]['binding']=dict(o['snapshots'][1]['binding'],event_revision=2)
  self.assertEqual(m.evaluate(p,o,'ios')['counts']['unassessed'],1)
 def test_numeric_equality_preserves_boolean_distinction(self):
  self.assertTrue(m.compare(48.0,48,'eq'));self.assertFalse(m.compare(True,1,'eq'))
 def test_android_descendants_and_native_touch_bounds(self):
  s={'nodes':[{'node_id':1,'parent_id':-1,'identifier':'row','selected':True,'enabled':True,'intersects_viewport':True},{'node_id':2,'parent_id':1,'clickable':True,'enabled':False,'selected':False,'touch_bounds_dp':[0,0,100,48]}]}
  r=m.resolve(s,{'identifier':'row'},'android');self.assertFalse(r['facts']['enabled']);self.assertTrue(r['facts']['selected']);self.assertEqual(r['facts']['touch_height'],48)
 def test_android_nested_click_actions_are_ambiguous(self):
  s={'nodes':[{'node_id':1,'parent_id':-1,'identifier':'row','clickable':True},{'node_id':2,'parent_id':1,'clickable':True}]}
  r=m.resolve(s,{'identifier':'row'},'android');self.assertEqual(r['resolution'],'ambiguous_native_controls');self.assertNotIn('enabled',r['facts'])
 def test_duplicate_presence_is_not_unique_or_absent(self):
  o=self.observation()
  for s in o['snapshots']:s['control_groups']=[{'selector':{'identifier':'row'},'match_count':2,'resolution':'ambiguous_semantic'}]
  self.assertEqual(m.evaluate(self.plan(True,'present'),o,'ios')['counts']['passed'],1)
  self.assertEqual(m.evaluate(self.plan(False,'unique'),o,'ios')['counts']['passed'],1)
 def test_duplicate_text_layout_cannot_pass_wrong_target(self):
  o=self.observation()
  for s in o['snapshots']:s['nodes']=[{'identifier':'row','font_sp':16,'intersects_viewport':True}]*2
  p=self.plan();p['assertions']=[{'id':'font','state':'initial','kind':'text_layout','target':{'identifier':'row'},'property':'font_sp','expected':16}]
  self.assertEqual(m.evaluate(p,o,'android')['counts']['unassessed'],1)

class CallbackPreconditions(unittest.TestCase):
 def step(self,events=('done',),platform='ios'):
  before={'pid':123,'instance':'native-session','fixture_index':0,'input_sha256':'input','event_revision':2}
  after=dict(before,event_revision=2+len(events))
  return {'outcome':'tapped','binding_after':after,'callback_delta':list(events),
          'dispatch':{'attempted':True,'succeeded':True,'method':'xcui_tap'if platform=='ios'else'compose_onclick','stimulus':'activation','binding_before':before,'event_start':2,'event_end':2+len(events),'matches':1,'native_controls':1,'enabled':True}}
 def test_dispatched_missing_wrong_and_matching_callbacks(self):
  self.assertEqual(m.callback_verdict(self.step(),['done'],'ios')['status'],'passed')
  self.assertEqual(m.callback_verdict(self.step(()),['done'],'ios')['status'],'failed')
  self.assertEqual(m.callback_verdict(self.step(('other',)),['done'],'ios')['status'],'failed')
  self.assertEqual(m.callback_verdict(self.step(()),[],'ios')['status'],'passed')
 def test_blocked_unavailable_and_observed_never_prove_zero_or_failure(self):
  for outcome in ['blocked_disabled','unavailable','observed','unsupported','completed']:
   for actual in [(),('spurious',)]:
    s=self.step(actual);s['outcome']=outcome
    for expected in [[],['done']]:
     r=m.callback_verdict(s,expected,'ios');self.assertEqual(r['status'],'unassessed');self.assertFalse(r['stimulus_established']);self.assertEqual(r['interval_facts'],list(actual))
 def test_success_flag_without_native_attempt_does_not_establish_stimulus(self):
  s=self.step();s['dispatch']['attempted']=False
  self.assertEqual(m.callback_verdict(s,['done'],'ios')['status'],'unassessed')
  s=self.step();s.pop('dispatch')
  self.assertEqual(m.callback_verdict(s,['done'],'ios')['status'],'unassessed')
 def test_method_fallback_does_not_prove_requested_method(self):
  self.assertEqual(m.callback_verdict(self.step(),['done'],'ios','ax_activate')['status'],'unassessed')
  s=self.step(platform='android')
  self.assertEqual(m.callback_verdict(s,['done'],'android','os_touch')['status'],'unassessed')
  self.assertEqual(m.callback_verdict(s,['done'],'android')['status'],'passed')
 def test_input_process_and_event_boundaries_are_hard_preconditions(self):
  for key,value in [('instance','other'),('pid',456),('input_sha256','other'),('fixture_index',1),('event_revision',7)]:
   s=self.step();s['binding_after'][key]=value
   self.assertEqual(m.callback_verdict(s,['done'],'ios')['status'],'unassessed')
  s=self.step();s['dispatch']['event_start']=1
  self.assertEqual(m.callback_verdict(s,['done'],'ios')['status'],'unassessed')
 def test_ambiguous_or_disabled_target_does_not_establish_delivery(self):
  for key,value in [('matches',2),('native_controls',2),('enabled',False),('matches',True)]:
   s=self.step();s['dispatch'][key]=value
   self.assertEqual(m.callback_verdict(s,['done'],'ios')['status'],'unassessed')
 def test_update_quietness_needs_explicit_success_and_catches_spurious_update_event(self):
  for actual,expected_status in [((), 'passed'),(('spurious',), 'failed')]:
   s=self.step(actual);s['outcome']='updated';s['binding_after'].update(fixture_index=1,input_sha256='new')
   s['dispatch'].update(stimulus='caller_update',method='caller_fixture_update')
   self.assertEqual(m.callback_verdict(s,[],'ios',stimulus='caller_update')['status'],expected_status)
   self.assertEqual(m.callback_verdict(s,[],'ios')['status'],'unassessed')
  s['binding_after']['fixture_index']=0
  self.assertEqual(m.callback_verdict(s,[],'ios',stimulus='caller_update')['status'],'unassessed')
if __name__=='__main__':unittest.main()
