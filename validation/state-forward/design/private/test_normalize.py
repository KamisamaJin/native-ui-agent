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
    def callback_verdict(self,step,expected,platform,required_method=None,stimulus='activation'):
        self.called_expected=expected
        self.actual_step=deepcopy(step)
        return dict(status='passed',stimulus_established=True,interval_facts=step['callback_delta'],reason='synthetic exact gate')

class RawAdapterPolicyTests(unittest.TestCase):
    def test_copied_json_canonicalization_and_current_text(self):
        base=dict(platform='android',caseID='X',stateID='X.s1')
        c=dict(base,cellID='text',aspect='title.text',classification='runtime.business.current',targetID='title',operator='equal',expected='Visible')
        cb=dict(base,cellID='events',aspect='behavior.callbackInterval',classification='runtime.business.stimulus',targetID='button',operator='eventSequence',expected=[{'name':'x','payload':{'a':1,'b':2}}],gate='successfulExactActivation')
        stimulus=dict(base,cellID='dispatch',aspect='stimulus.dispatch',classification='stimulus.execution',targetID='button',operator='stimulus',expected={})
        observation={'snapshot':{'binding':{'instance':'proc','fixture_index':0,'event_revision':1},'nodes':{'title':{'label':'Visible','intersects_viewport':True}}},'steps':[{'state_id':'X.s1','selector':{'identifier':'button'},'immediate_after':3,'after':5,'callback_delta':['{"payload":{"b":2,"a":1},"name":"x"}'],'binding_after':{'instance':'proc','fixture_index':0,'event_revision':1}}]}
        before=deepcopy(observation)
        helper=FakeImmutableHelper()
        result=normalize({'cells':[c,cb,stimulus]},{'states':[dict(caseID='X',stateID='X.s1',full_content=True,actionIndex=1,trigger='activate')]},observation,{'X.s1':dict(state_id='X.s1',input_index=0,state_action_index=1,trigger_step_pointer='/steps/0',trigger_state_id='X.s1')},'android','X','Anonymous','D0',helper,'raw.json','mapping.json')
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
        res=dict(resolution='unique_native_control',facts={'unique':True,'touch_height':20},semantic={'intersects_viewport':True,'fully_visible':False},control={'fully_visible':False,'unclipped_bounds_dp':[0,0,20,48]})
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
    def test_semantic20_touch48_uses_semantic_layout_and_fails_minimum(self):
        from grade import grade_cell
        c=dict(cellID='android.X.s1.control.width',platform='android',caseID='X',stateID='X.s1',targetID='button',operator='minimum',aspect='control.button.semanticBounds.width',classification='runtime.layout.native',dimension='width',unit='dp',expected=48)
        res=dict(resolution='unique_native_control',facts={'unique':True,'touch_width':48},semantic={'intersects_viewport':True},control={'node_id':'native-button','fully_visible':True,'unclipped_bounds_dp':[10,20,30,80],'touch_bounds_dp':[0,20,48,80]})
        kind,actual,extra=native_value(c,res,'android',{})
        self.assertEqual(actual,20);self.assertEqual(extra['nativeRectangles']['touch_bounds_dp'],[0,20,48,80]);self.assertEqual(extra['uncertainty'],2)
        record=dict(cellID=c['cellID'],evidenceKind=kind,actual=actual,evidenceRefs=['synthetic-native.json#/control'],context=dict(platform='android',caseID='X',stateID='X.s1',processID='p',inputRevision=0,eventRevision=1,mappingRef='map#/X.s1'),**extra)
        graded=grade_cell(c,[record]);self.assertEqual(graded['status'],'F');self.assertEqual(graded['normalization']['measurementSourcePath'],'control.unclipped_bounds_dp')
    def test_semantic60_touch48_uses_semantic_layout_and_passes_minimum(self):
        from grade import grade_cell
        c=dict(cellID='android.X.s1.control.width',platform='android',caseID='X',stateID='X.s1',targetID='button',operator='minimum',aspect='control.button.semanticBounds.width',classification='runtime.layout.native',dimension='width',unit='dp',expected=48)
        res=dict(resolution='unique_native_control',facts={'unique':True,'touch_width':48},semantic={'intersects_viewport':True},control={'node_id':'native-button','fully_visible':True,'unclipped_bounds_dp':[10,20,70,80],'touch_bounds_dp':[0,20,48,80]})
        kind,actual,extra=native_value(c,res,'android',{})
        self.assertEqual(actual,60);self.assertEqual(extra['nativeRectangles']['unclipped_bounds_dp'],[10,20,70,80])
        record=dict(cellID=c['cellID'],evidenceKind=kind,actual=actual,evidenceRefs=['synthetic-native.json#/control'],context=dict(platform='android',caseID='X',stateID='X.s1',processID='p',inputRevision=0,eventRevision=1,mappingRef='map#/X.s1'),**extra)
        self.assertEqual(grade_cell(c,[record])['status'],'P')
    def test_no_explicit_trigger_pointer_never_guesses_step(self):
        c=dict(cellID='cb',platform='android',caseID='X',stateID='X.s1',aspect='behavior.callbackInterval',classification='runtime.business.stimulus',targetID='button',operator='eventSequence',expected=[],gate='successfulExactActivation')
        ob={'snapshot':{'binding':{},'nodes':{}}}
        r=normalize({'cells':[c]},{'states':[dict(caseID='X',stateID='X.s1',full_content=False,actionIndex=1,trigger='activate')]},ob,{'X.s1':dict(state_id='X.s1',input_index=0,state_action_index=1)},'android','X','A','D0',FakeImmutableHelper(),'raw','map')
        self.assertEqual(r['records'],[])


# These controls exercise only actual receipt provenance, with no business UI/source.
class NoPostObservationHelper(FakeImmutableHelper):
    def state_evidence(self,observation,spec):
        return [],False,'synthetic later viewport unavailable',None

class ActualReceiptProvenanceTests(unittest.TestCase):
    def fixture(self,platform='android',replacement=False):
        from grade import grade_cell
        callback=dict(cellID='events',platform=platform,caseID='X',stateID='X.s1',aspect='behavior.callbackInterval',classification='runtime.business.stimulus',targetID='caller.model' if replacement else 'button',operator='eventSequence',expected=[],gate='replacementApplied' if replacement else 'successfulExactActivation')
        execution=dict(callback,cellID='execution',aspect='stimulus.dispatch',classification='stimulus.execution',operator='stimulus')
        step=dict(state_id='X.s1',selector={'identifier':'button'},action={'target':{'identifier':'button'}},callback_delta=[],immediate_after=3,after=5,binding_after=dict(instance='native-p',fixture_index=1 if replacement else 0,event_revision=1),dispatch=dict(method='caller_fixture_update' if replacement else 'native_action',binding_before=dict(fixture_index=0)))
        mapping={'X.s1':dict(state_id='X.s1',trigger_state_id='X.s1',input_index=1 if replacement else 0,state_action_index=1,trigger_action_index=1,trigger_step_pointer='/steps/0')}
        ledger={'states':[dict(caseID='X',stateID='X.s1',full_content=True,actionIndex=1,trigger='replaceModel' if replacement else 'activate')]}
        return callback,execution,step,mapping,ledger
    def run_receipt(self,callback,execution,step,mapping,ledger,platform='android'):
        from grade import grade_cell
        output=normalize({'cells':[callback,execution]},ledger,{'steps':[step]},mapping,platform,'X','A','D0',NoPostObservationHelper(),'raw.json','mapping.json')
        record=next(r for r in output['records'] if r['cellID']=='events')
        return record,grade_cell(callback,[record]),output
    def test_wrong_target_empty_callback_is_unknown_and_actual_target_retained(self):
        c,e,step,m,l=self.fixture();step['selector']['identifier']='wrong-native-target'
        record,grade,_=self.run_receipt(c,e,step,m,l)
        self.assertEqual(record['gate']['targetID'],'wrong-native-target');self.assertEqual(grade['status'],'U')
        self.assertIn('actual requested native identifier differs from expected target',record['gate']['provenance']['reasons'])
    def test_wrong_action_pointer_state_is_unknown(self):
        c,e,step,m,l=self.fixture();step['state_id']='X.s9'
        record,grade,_=self.run_receipt(c,e,step,m,l)
        self.assertEqual(grade['status'],'U');self.assertEqual(record['gate']['provenance']['actualStateID'],'X.s9')
    def test_wrong_immediate_input_is_unknown(self):
        c,e,step,m,l=self.fixture();step['binding_after']['fixture_index']=8
        record,grade,_=self.run_receipt(c,e,step,m,l)
        self.assertEqual(grade['status'],'U');self.assertEqual(record['gate']['provenance']['actualInputIndex'],8)
    def test_missing_actual_selector_never_uses_oracle_target(self):
        c,e,step,m,l=self.fixture();step.pop('selector')
        record,grade,_=self.run_receipt(c,e,step,m,l)
        self.assertIsNone(record['gate']['targetID']);self.assertEqual(grade['status'],'U')
    def test_ios_actual_selector_forms(self):
        for action in [{'target':{'identifier':'button'}},{'identifier':'button'}]:
            with self.subTest(action=action):
                c,e,step,m,l=self.fixture('ios');step['action']=action
                record,grade,_=self.run_receipt(c,e,step,m,l,'ios')
                self.assertEqual(record['gate']['targetID'],'button');self.assertEqual(grade['status'],'P')
    def test_callback_does_not_require_later_post_observation(self):
        c,e,step,m,l=self.fixture()
        record,grade,_=self.run_receipt(c,e,step,m,l)
        self.assertEqual(grade['status'],'P');self.assertEqual(record['context']['processID'],'native-p')
    def test_caller_update_uses_actual_method_and_binding_advance(self):
        c,e,step,m,l=self.fixture(replacement=True)
        record,grade,_=self.run_receipt(c,e,step,m,l)
        self.assertEqual(grade['status'],'P');self.assertIsNone(record['gate']['targetID'])
        step['dispatch']['method']='source_injected_update'
        self.assertEqual(self.run_receipt(c,e,step,m,l)[1]['status'],'U')
        step['dispatch']['method']='caller_fixture_update';step['dispatch']['binding_before']['fixture_index']=1
        self.assertEqual(self.run_receipt(c,e,step,m,l)[1]['status'],'U')
    def test_invalid_pointer_is_retained_as_diagnostic(self):
        c,e,step,m,l=self.fixture();m['X.s1']['trigger_step_pointer']='/steps/9'
        record,grade,output=self.run_receipt(c,e,step,m,l)
        self.assertEqual(grade['status'],'U');self.assertTrue(output['adapterDiagnostics'])

if __name__=='__main__':unittest.main()
