"""Synthetic schema controls. Never imports candidate/baseline internals."""
from copy import deepcopy
import unittest
from normalize import normalize,canon_event,native_value

class FakeImmutableHelper:
    def __init__(self):self.called_expected=None
    def state_evidence(self,observation,spec):
        return [(0,observation['snapshot'])],True,'synthetic bounded capture',None
    def resolve(self,snapshot,selector,platform):
        node=snapshot['nodes'].get(selector['identifier'])
        if node is None:return dict(resolution='missing',facts={'present':False,'unique':False},semantic={},control={})
        return dict(resolution='no_native_control',facts=dict(present=True,unique=True,label=node['label']),semantic=node,control={})
    def callback_verdict(self,step,expected,platform,stimulus='activation'):
        self.called_expected=expected
        self.actual_step=deepcopy(step)
        return dict(status='passed',stimulus_established=True,interval_facts=step['callback_delta'],reason='synthetic exact gate')

class RawAdapterPolicyTests(unittest.TestCase):
    def test_copied_json_canonicalization_and_current_text(self):
        base=dict(platform='android',caseID='X',stateID='X.s1')
        c=dict(base,cellID='text',aspect='title.text',classification='runtime.business.current',targetID='title',operator='equal',expected='Visible')
        cb=dict(base,cellID='events',aspect='behavior.callbackInterval',classification='runtime.business.stimulus',targetID='button',operator='eventSequence',expected=[{'name':'x','payload':{'a':1,'b':2}}],gate='successfulExactActivation')
        stimulus=dict(base,cellID='dispatch',aspect='stimulus.dispatch',classification='stimulus.execution',targetID='button',operator='stimulus',expected={})
        observation={'snapshot':{'binding':{'instance':'proc','fixture_index':0,'event_revision':1},'nodes':{'title':{'label':'Visible','intersects_viewport':True}}},'steps':[{'immediate_after':3,'after':5,'callback_delta':['{"payload":{"b":2,"a":1},"name":"x"}'],'binding_after':{'instance':'proc','fixture_index':0,'event_revision':1}}]}
        before=deepcopy(observation)
        helper=FakeImmutableHelper()
        result=normalize({'cells':[c,cb,stimulus]},{'states':[dict(caseID='X',stateID='X.s1',full_content=True,actionIndex=1,trigger='activate')]},observation,{'X.s1':dict(state_id='X.s1',input_index=0,state_action_index=1,trigger_step_pointer='/steps/0')},'android','X','Anonymous','D0',helper,'raw.json','mapping.json')
        self.assertEqual(observation,before)
        self.assertEqual(helper.called_expected,[canon_event(cb['expected'][0])])
        rows={r['cellID']:r for r in result['records']}
        self.assertEqual(rows['text']['actual'],'Visible')
        self.assertEqual(rows['events']['actual'],cb['expected'])
        self.assertEqual(rows['events']['gate']['verdict'],'pass')
        self.assertEqual(rows['events']['context']['processID'],'proc')
        self.assertEqual(rows['events']['context']['eventRevision'],1)
    def test_style_uses_real_unique_text_descendant(self):
        c=dict(operator='scalar',aspect='mode.single.fontSize',classification='runtime.style.native')
        res=dict(facts={'unique':True,'label':'One'},semantic={'node_id':'button','intersects_viewport':True},control={})
        snap={'nodes':[{'node_id':'button'},{'node_id':'text','parent_id':'button','native_text':'One','font_sp':14}]}
        kind,actual,extra=native_value(c,res,'android',snap)
        self.assertEqual(kind,'native.fontSize');self.assertEqual(actual,14);self.assertEqual(extra['measurementNodePath'],['button','text'])
    def test_style_never_spatially_guesses_or_chooses_ambiguous_descendant(self):
        c=dict(operator='scalar',aspect='mode.single.fontSize',classification='runtime.style.native')
        res=dict(facts={'unique':True,'label':'One'},semantic={'node_id':'button','intersects_viewport':True},control={})
        self.assertIsNone(native_value(c,res,'android',{'nodes':[{'node_id':'nearby','native_text':'One','font_sp':14}]}))
        snap={'nodes':[{'node_id':'button'},{'node_id':'text1','parent_id':'button','native_text':'One','font_sp':14},{'node_id':'text2','parent_id':'button','native_text':'One','font_sp':18}]}
        kind,actual,extra=native_value(c,res,'android',snap)
        self.assertIsNone(actual);self.assertEqual(len(extra['measurementCandidates']),2)
    def test_clipped_control_bounds_are_not_a_small_control_failure(self):
        c=dict(operator='minimum',aspect='control.width',classification='runtime.layout.native',dimension='height',unit='dp')
        res=dict(facts={'unique':True,'touch_height':20},semantic={'intersects_viewport':True,'fully_visible':False},control={'fully_visible':False})
        self.assertIsNone(native_value(c,res,'android',{}))
        res['facts']['touch_height']=48;res['control']['fully_visible']=True
        self.assertEqual(native_value(c,res,'android',{})[1],48)
    def test_switch_on_uses_checked_value_not_default_selected_false(self):
        c=dict(operator='selected',aspect='priority.on',classification='runtime.business.current')
        res=dict(facts={'unique':True,'selected':False,'value':True,'control_role':'Switch'},semantic={'intersects_viewport':True},control={})
        self.assertIs(native_value(c,res,'ios',{})[1],True)
    def test_button_explicit_selected_value_is_allowed(self):
        c=dict(operator='selected',aspect='mode.duplex.selected',classification='runtime.business.current')
        res=dict(facts={'unique':True,'selected':False,'value':'Selected','control_role':'Button'},semantic={'intersects_viewport':True},control={})
        self.assertIs(native_value(c,res,'ios',{})[1],True)
    def test_contradictory_authoritative_selected_values_stay_unknown(self):
        c=dict(operator='selected',aspect='priority.on',classification='runtime.business.current')
        res=dict(facts={'unique':True,'selected':False,'value':True,'control_role':'Switch'},semantic={'intersects_viewport':True,'toggle_state':'Off'},control={})
        value=native_value(c,res,'android',{})
        self.assertIsNone(value[1]);self.assertEqual(len(value[2]['selectionCandidates']),2)
        c['aspect']='mode.duplex.selected';res['facts'].update(selected=True,value='Not selected',control_role='Button');res['semantic'].pop('toggle_state')
        self.assertIsNone(native_value(c,res,'ios',{})[1])
    def test_no_explicit_trigger_pointer_never_guesses_step(self):
        c=dict(cellID='cb',platform='android',caseID='X',stateID='X.s1',aspect='behavior.callbackInterval',classification='runtime.business.stimulus',targetID='button',operator='eventSequence',expected=[],gate='successfulExactActivation')
        ob={'snapshot':{'binding':{},'nodes':{}}}
        r=normalize({'cells':[c]},{'states':[dict(caseID='X',stateID='X.s1',full_content=False,actionIndex=1,trigger='activate')]},ob,{'X.s1':dict(state_id='X.s1',input_index=0,state_action_index=1)},'android','X','A','D0',FakeImmutableHelper(),'raw','map')
        self.assertEqual(r['records'],[])

if __name__=='__main__':unittest.main()
