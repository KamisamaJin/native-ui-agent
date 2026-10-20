import unittest,json,tempfile,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import grader
ROOT=grader.cfroot();sys.path.insert(0,str(ROOT/'candidate-v6/scripts'));import native_checks as n
class Controls(unittest.TestCase):
 def step(self,platform='android',events=None):
  events=[] if events is None else events;b=dict(instance='control',fixture_index=0,input_sha256='abc',event_revision=0,pid=99);after=dict(b,event_revision=len(events))
  return dict(outcome='tapped',dispatch=dict(attempted=True,succeeded=True,method='xcui_tap' if platform=='ios' else 'compose_onclick',stimulus='activation',matches=1,native_controls=1,enabled=True,binding_before=b,event_start=0,event_end=len(events)),binding_after=after,callback_delta=events)
 def test_callbacks_correct_wrong_missing(self):
  for p in ['ios','android']:
   self.assertEqual(n.callback_verdict(self.step(p,['reserve:x']),['reserve:x'],p)['status'],'passed')
   self.assertEqual(n.callback_verdict(self.step(p,[]),['reserve:x'],p)['status'],'failed')
   s=self.step(p);s['dispatch']['succeeded']=False
   self.assertEqual(n.callback_verdict(s,[],p)['status'],'unassessed')
 def test_caller_update_gate(self):
  s=self.step();s['outcome']='updated';s['dispatch'].update(method='caller_fixture_update',stimulus='caller_update');s['binding_after']['fixture_index']=1;s['binding_after']['input_sha256']='next'
  self.assertEqual(n.callback_verdict(s,[],'android',stimulus='caller_update')['status'],'passed')
  s['binding_after']['fixture_index']=0
  self.assertEqual(n.callback_verdict(s,[],'android',stimulus='caller_update')['status'],'unassessed')
 def synthetic(self,bad=False):
  b=dict(instance='control',fixture_index=0,input_sha256='abc',event_revision=0)
  node=dict(node_id=1,parent_id=None,identifier='enroll.title',label='WRONG' if bad else 'Workshop enrollment',intersects_viewport=True,native_text=True,font_sp=22,color_argb=int('FF172B3A',16))
  snap=dict(state_id='browse',binding=b,nodes=[node],scroll_offset_dp=0,scroll_max_dp=0,viewport_height_dp=640,screenshot='control.png')
  cap=dict(state_id='browse',binding=b,after_action=0,snapshot_indices=[0],top_reached=True,bottom_reached=True,stable_binding=True)
  return dict(snapshots=[snap],state_captures=[cap],steps=[])
 def test_design_owned_oracle_correct_wrong_unknown(self):
  for bad in [False,True]:
   with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'observation.json';p.write_text(json.dumps(self.synthetic(bad)))
    result=grader.grade('P1','android',p)
    rows={r['id']:r for r in result['rows']}
    self.assertEqual(rows['P1/android/browse/heading']['status'],'F' if bad else 'P')
    self.assertEqual(rows['P1/android/browse/title-font']['status'],'P')
    self.assertEqual(rows['P1/android/browse/activation']['status'],'N/A')
    self.assertEqual(rows['P1/android/configured/total']['status'],'U')
    self.assertEqual(len(rows),120)
 def test_equal_matching_and_wrong_expectation(self):
  row=dict(id='P1/android/browse/heading',case='P1',platform='android',state='browse',aspect='heading',expected='A',unit='string',status='F',**{'class':'native_content'})
  g={'rows':[row]}
  for origin in ['typed_native_check','manual']:
   c=dict(row,origin=origin);self.assertEqual(grader.match_claims(g,[c])['TP'],1)
   c['expected']='B';self.assertEqual(grader.match_claims(g,[c])['TP'],0)
  self.assertEqual(grader.match_claims({'rows':[]},[])['recall'],'N/A')
 def test_fixed_row_repair(self):
  r=dict(id='x',expected=False,status='F',**{'class':'style_native'})
  for s in ['P','F','U']:
   out=grader.repair({'rows':[r]},{'rows':[dict(r,status=s)]});self.assertEqual(out['counts'][s],1)
 def test_no_float_equality_and_no_layout_guess(self):
  self.assertTrue(n.compare(22.025,22,'near',.05));self.assertFalse(n.compare(22.1,22,'near',.05))
  self.assertIsNone(n.geometry_value({},dict(measurement='layout_box'),'ios'))
if __name__=='__main__':unittest.main()
