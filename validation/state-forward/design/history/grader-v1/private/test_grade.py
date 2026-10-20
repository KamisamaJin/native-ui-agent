"""Synthetic pre-source checks, not a business implementation or trial outcome."""
import unittest
from grade import grade_cell

class GenericEvidencePolicyTests(unittest.TestCase):
    def cell(self,op='equal',expected='Disabled label',cls='runtime.business.current',aspect='approve.text'):
        return dict(cellID='android.X.s1.'+aspect,platform='android',caseID='X',stateID='X.s1',aspect=aspect,classification=cls,targetID='target',operator=op,expected=expected)
    def rec(self,kind='native.text',actual='Disabled label',**extra):
        return dict(evidenceKind=kind,actual=actual,evidenceRefs=['synthetic.json#/native'],context=dict(platform='android',caseID='X',stateID='X.s1',processID='p',inputRevision=1,eventRevision=1,mappingRef='mapping.json#/X.s1'),**extra)
    def test_current_fact_does_not_need_prior_activation(self):
        self.assertEqual(grade_cell(self.cell(),[self.rec(gate={'verdict':'unknown'})])['status'],'P')
    def test_disabled_action_does_not_prove_zero_callback(self):
        c=self.cell('eventSequence',[], 'runtime.business.stimulus');c['gate']='successfulExactActivation'
        self.assertEqual(grade_cell(c,[self.rec('native.events',[],gate=dict(verdict='unknown',kind='successfulExactActivation',evidenceRefs=['dispatch']))])['status'],'U')
    def test_successful_exact_noop_can_prove_zero_callback(self):
        c=self.cell('eventSequence',[], 'runtime.business.stimulus');c['gate']='successfulExactActivation'
        r=self.rec('native.events',[],gate=dict(verdict='pass',kind='successfulExactActivation',targetID='target',attempts=1,intervalComplete=True,evidenceRefs=['dispatch']))
        self.assertEqual(grade_cell(c,[r])['status'],'P')
    def test_interval_not_extended_by_sweep(self):
        c=self.cell('eventSequence',[], 'runtime.business.stimulus');c['gate']='successfulExactActivation'
        r=self.rec('native.events',[],gate=dict(verdict='pass',kind='successfulExactActivation',targetID='target',attempts=1,intervalComplete=False,evidenceRefs=['dispatch']))
        self.assertEqual(grade_cell(c,[r])['status'],'U')
    def test_absence_needs_complete_coverage(self):
        c=self.cell('presence',False)
        self.assertEqual(grade_cell(c,[self.rec('native.presence',False)])['status'],'U')
        self.assertEqual(grade_cell(c,[self.rec('native.presence',False,completeCoverage=True)])['status'],'P')
    def test_actual_presence_proves_failure_without_full_coverage(self):
        self.assertEqual(grade_cell(self.cell('presence',False),[self.rec('native.presence',True)])['status'],'F')
    def test_native_minimum_keeps_uncertainty(self):
        c=self.cell('minimum',48,'runtime.layout.native','control.width');c['unit']='dp'
        self.assertEqual(grade_cell(c,[self.rec('native.bounds',48,unit='dp')])['status'],'U')
        self.assertEqual(grade_cell(c,[self.rec('native.bounds',51,unit='dp')])['status'],'P')
        self.assertEqual(grade_cell(c,[self.rec('native.bounds',45,unit='dp')])['status'],'F')
    def test_conflicts_are_not_last_write_wins(self):
        self.assertEqual(grade_cell(self.cell(),[self.rec(),self.rec(actual='different')])['status'],'U')
    def test_style_cannot_be_sourced(self):
        c=self.cell('scalar',14,'runtime.style.native','title.fontSize');c['unit']='sp'
        self.assertEqual(grade_cell(c,[self.rec('manual.source',14,unit='sp')])['status'],'U')
    def test_valid_same_state_fact_survives_unavailable_other_frame(self):
        c=self.cell('scalar',14,'runtime.style.native','title.fontSize');c['unit']='sp'
        a=self.rec('native.fontSize',14,unit='sp',measurementNodePath=['a'])
        u=self.rec('native.fontSize',None,unit='sp',measurementCandidates=[{'node_id':'unknown'}])
        r=grade_cell(c,[a,u]);self.assertEqual(r['status'],'P');self.assertTrue(r['normalization']['unresolvedRecords'])
    def test_equal_values_can_union_different_native_node_paths(self):
        c=self.cell('scalar',14,'runtime.style.native','title.fontSize');c['unit']='sp'
        a=self.rec('native.fontSize',14,unit='sp',measurementNodePath=['a'])
        b=self.rec('native.fontSize',14,unit='sp',measurementNodePath=['b'])
        r=grade_cell(c,[a,b]);self.assertEqual(r['status'],'P');self.assertEqual(len(r['normalization']['normalizationOccurrences']),2)
    def test_current_bool_does_not_equal_integer(self):
        self.assertEqual(grade_cell(self.cell('enabled',False),[self.rec('native.enabled',0)])['status'],'F')
    def test_callback_json_integer_type_is_preserved(self):
        c=self.cell('eventSequence',[{'name':'example','payload':{'count':1}}], 'runtime.business.stimulus');c['gate']='successfulExactActivation'
        r=self.rec('native.events',[{'name':'example','payload':{'count':1.0}}],gate=dict(verdict='pass',kind='successfulExactActivation',targetID='target',attempts=1,intervalComplete=True,evidenceRefs=['dispatch']))
        self.assertEqual(grade_cell(c,[r])['status'],'F')
    def test_color_property_cannot_turn_foreground_into_fill(self):
        c=self.cell('color','#265FE4','runtime.style.native','approve.fill')
        self.assertEqual(grade_cell(c,[self.rec('native.color',0xff265fe4,nativeProperty='textColor')])['status'],'U')
        self.assertEqual(grade_cell(c,[self.rec('native.color',0xff265fe4,nativeProperty='fill')])['status'],'P')
    def test_screenshot_declaration_is_not_review(self):
        c=self.cell('screenshotReview','meaning','runtime.style.visual')
        self.assertEqual(grade_cell(c,[self.rec('native.text','meaning')])['status'],'U')

if __name__=='__main__':unittest.main()
