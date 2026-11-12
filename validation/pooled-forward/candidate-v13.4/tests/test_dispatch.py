import copy
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import design_contract as d,requirement_routes as rr,retest_plan as retest
import test_delivery_plan as fixtures
import ax_calibration as ax

class DispatchTests(unittest.TestCase):
 setUp=fixtures.DeliveryPlanTests.setUp
 audit=fixtures.DeliveryPlanTests.audit
 def select(self,report,*,visual=(),changed=False,final=False):
  tasks=[]
  for row in report['assertions']:
   if row['status']!='passed':tasks.append({'obligation_id':'caption','assertion_ids':[row['id']],'state':row['state'],'priority':'must','action':'review_measurement_or_visual'if row['id']in visual else'diagnose_product'})
  return retest.dispatch(self.coverage,self.plan,report,{'tasks':tasks},changed_files=['View.swift']if changed else[],source_before='a'*64,source_after=('b'if changed else'a')*64,visual_ids=visual,final=final)
 def test_review_queue_never_launches_native_on_unchanged_source(self):
  report=copy.deepcopy(self.report);report['assertions'][0]['status']='unassessed';key=report['assertions'][0]['id']
  plan=self.select(report,visual=[key]);self.assertEqual(plan['states'],[]);self.assertEqual(plan['status'],'awaiting_review')
  self.assertEqual(plan['review_only_ids'],[key]);self.assertFalse(plan['requires_fresh_capture'])
 def test_bound_visual_failure_requires_repair_not_identical_rescan(self):
  report=copy.deepcopy(self.report);report['assertions'][0]['status']='failed';key=report['assertions'][0]['id']
  self.assertEqual(self.select(report,visual=[key])['status'],'awaiting_source_repair')
  repaired=self.select(report,visual=[key],changed=True)
  self.assertEqual(repaired['states'],['ready']);self.assertTrue(repaired['requires_fresh_capture'])
 def test_complete_feedback_is_not_a_final_acceptance_or_new_scan(self):
  self.assertEqual(self.select(self.report)['status'],'feedback_complete')
  self.assertEqual(self.select(self.report)['states'],[])
  self.assertEqual(self.select(self.report,final=True)['states'],['ready','chosen','updated'])
 def test_source_edit_without_proven_impact_falls_back_full(self):
  self.assertEqual(self.select(self.report,changed=True)['states'],['ready','chosen','updated'])
 def test_calibration_never_changes_strict_verdict_or_expectation(self):
  profile={'version':1,'status':'validated','provider':'xcui_cgrect','numeric_encoding':'binary64','context':{'screen_scale':2,'os_version':'neutral'},'factor':1,'factor_fit_uses_heldout':False,'domain':{'max_abs_coordinate':10000,'max_extent':200},'scope':'neutral empirical diagnostic'}
  sample={'ratio':[66000000000000001,1000000000000000],'sources':[{'provider':'xcui_cgrect','unit':'pt','sample':{'x':20.25,'y':900.125,'width':66.0,'height':31.25}}]}
  self.assertEqual(ax.classify(sample,66,'eq',None,profile,profile['context'])['classification'],'outside_calibrated_scope')
  profile['provenance']={'extraction_sha256':'a'*64}
  profile['raw_residuals']=[{'identifier':'neutral.leaf','frame':sample['sources'][0]['sample']}]
  sample['sources'][0]['calibration_reference']={'identifier':'neutral.leaf','extraction_sha256':'a'*64}
  result=ax.classify(sample,66,'eq',None,profile,profile['context'])
  self.assertEqual(result['classification'],'boundary_overlap');self.assertTrue(result['strict_verdict_preserved']);self.assertEqual(result['expected_unchanged'],66)
  wrong=dict(sample,ratio=[65,1]);self.assertEqual(ax.classify(wrong,66,'gte',None,profile,profile['context'])['classification'],'definite_within_profile')
  self.assertEqual(ax.classify(sample,66,'gte',None,profile,{'screen_scale':3})['classification'],'outside_calibrated_scope')
if __name__=='__main__':unittest.main()
