import copy,unittest
import metrics as m
class MetricControls(unittest.TestCase):
 def setUp(self):
  self.truth=[{'key':'a','status':'failed','cause_category':'product'},{'key':'b','status':'passed','cause_category':None},{'key':'c','status':'unassessed','cause_category':None}]
 def claim(self,status='TP',rows=None,**kwargs):
  v={'status':status,'supported_rows':rows if rows is not None else['a'],'reason':'Original supported evidence','false_alarm_supported':status=='FP'}
  return dict(claim_id='x',origin='machine',original_status='failed',original_scope=['a'],judge_one=copy.deepcopy(v),judge_two=copy.deepcopy(v),**kwargs)
 def test_schema_rejection_is_separate_from_product_false_alarm(self):
  d=m.detection(self.truth,[self.claim(schema_rejected=True)],[['a']]);self.assertEqual(d['counts'],{'TP':1,'FP':0,'U':0});self.assertEqual(d['schemaRejections'],1)
 def test_disagreement_and_zero_denominators_remain_unknown(self):
  c=self.claim();c['judge_two']['status']='U';d=m.detection(self.truth,[c],[['a']]);self.assertEqual(d['counts']['U'],1);self.assertIsNone(d['conditionalFalseDiscoveryRatio'])
  self.assertIsNone(m.detection([],[],[])['rowRecall'])
 def test_no_retrospective_scope_expansion(self):
  c=self.claim();c['judge_one']['supported_rows']=['b']
  with self.assertRaises(AssertionError):m.detection(self.truth,[c],[['a']])
 def test_false_alarm_requires_both_supported_original_judgments(self):
  c=self.claim('FP',[]);c['original_scope']=['b'];d=m.detection(self.truth,[c],[['a']]);self.assertEqual(d['counts']['FP'],1)
  c['judge_two']['false_alarm_supported']=False;self.assertEqual(m.detection(self.truth,[c],[['a']])['counts']['U'],1)
 def test_cluster_names_do_not_matter_but_membership_disagreement_does(self):
  a=[{'id':'one','rows':['a','b'],'reason':'One root cause','certainty':'confirmed'}];b=[{'id':'different-name','rows':['b','a'],'reason':'One root cause','certainty':'confirmed'}]
  self.assertEqual(len(m.agreed_clusters(a,b,['a','b'])['confirmed']),1)
  b=[{'rows':['a'],'reason':'First cause','certainty':'confirmed'},{'rows':['b'],'reason':'Second cause','certainty':'confirmed'}]
  self.assertEqual(m.agreed_clusters(a,b,['a','b'])['membershipUncertainRows'],['a','b'])
 def test_unknown_final_does_not_count_as_repaired(self):
  final=copy.deepcopy(self.truth);final[0]['status']='unassessed';d=m.repairs(self.truth,final,[['a']]);self.assertEqual(d['clusterRepairRate'],0)
 def test_duplicate_and_nonfailure_do_not_inflate_alarm_counts(self):
  c=self.claim();dup=dict(self.claim(),claim_id='y',duplicate_of='x');good=dict(self.claim(),claim_id='z',original_status='passed')
  d=m.detection(self.truth,[c,dup,good],[['a']]);self.assertEqual(d['counts']['TP'],1);self.assertEqual(d['duplicates'],1);self.assertEqual(d['nonFailureObservations'],1)
 def test_uncertain_groups_do_not_become_confirmed_singletons(self):
  groups=[{'rows':['a'],'reason':'Cause association uncertain','certainty':'uncertain'}]
  result=m.agreed_clusters(groups,groups,['a']);self.assertEqual(result['confirmed'],[]);self.assertEqual(result['membershipUncertainRows'],['a'])
 def test_manual_subset_can_reference_immutable_machine_duplicate(self):
  machine=self.claim();manual=dict(self.claim(),claim_id='manual',origin='manual',duplicate_of='x')
  d=m.detection(self.truth,[manual],[['a']],all_claims=[machine,manual]);self.assertEqual(d['duplicates'],1);self.assertEqual(d['counts']['TP'],0)
if __name__=='__main__':unittest.main()
