"""Synthetic accounting controls only; no candidate production mutation."""
import unittest
import metrics
def row(identity,status,platform='ios'):
 return dict(id=identity,case='P1',platform=platform,state='loaded',requirement='size',expected=48,unit='pt',status=status)
def claim(platform='ios',expected=48):return dict(case='P1',platform=platform,state='loaded',requirement='size',expected=expected,unit='pt',status='F')
def summary(product=(),nonproduct=(),uncertain=(),clusters=()):return dict(product_failure_row_ids=list(product),non_product_f_rows=list(nonproduct),uncertain_f_rows=list(uncertain),defect_clusters=list(clusters))
class AccountingControls(unittest.TestCase):
 def test_unmapped_and_zero_natural_denominator_stay_unknown(self):
  c=claim();c['requirement']='not-selected';v=metrics.detection([row('p','P')],summary(),[('manual',c)])
  self.assertEqual(v['counts']['U'],1);self.assertIsNone(v['clusterRecall']);self.assertIsNone(v['conditionalFalseDiscoveryRatio']);self.assertEqual(v['allClaimsFalseDiscoveryBounds'],[0,1])
 def test_known_measurement_alarm_is_not_product_detection(self):
  v=metrics.detection([row('f','F')],summary(nonproduct=['f']),[('machine',claim())]);self.assertEqual(v['counts']['FP'],1);self.assertEqual(v['detectedProductRows'],0);self.assertIsNone(v['rowRecall'])
 def test_cluster_detection_and_complete_repair_have_distinct_denominators(self):
  rows=[row('ios','F'),row('android','F','android')];s=summary(product=['ios','android'],clusters=[dict(cluster_id='one',fixed_row_ids=['ios','android'])]);v=metrics.detection(rows,s,[('machine',claim())]);self.assertEqual(v['clusterRecall'],1);self.assertEqual(v['rowRecall'],.5)
  repair=metrics.repairs(rows,[row('ios','P'),row('android','U','android')],s);self.assertEqual(repair['productRowRepairRate'],.5);self.assertEqual(repair['clusterRepairRate'],0);self.assertEqual(repair['unassessedClusters'],['one'])
 def test_duplicate_machine_and_manual_do_not_double_count(self):
  s=summary(product=['f'],clusters=[dict(cluster_id='one',fixed_row_ids=['f'])]);v=metrics.detection([row('f','F')],s,[('machine',claim()),('manual',claim())]);self.assertEqual(v['counts']['TP'],1);self.assertEqual(v['counts']['duplicates'],1)
 def test_wrong_original_expected_receives_no_retroactive_credit(self):
  s=summary(product=['f'],clusters=[dict(cluster_id='one',fixed_row_ids=['f'])]);v=metrics.detection([row('f','F')],s,[('manual',claim(expected=50))]);self.assertEqual(v['counts']['FP'],1);self.assertEqual(v['clusterRecall'],0)
if __name__=='__main__':unittest.main()
