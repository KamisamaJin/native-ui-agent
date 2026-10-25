import copy,unittest
from metrics import summarize
class MetricControls(unittest.TestCase):
 def item(self):return {'unit':'opaque','residual_initial_defects':[],'new_regressions':[],'alarm_causes':['uncertain'],'native_complete':False,'source_audit_complete':True,'independent_quality_complete':False,'failed':0,'unassessed':1,'applicable':5,'author_seconds':10,'d0_seconds':20,'repair_endpoint_seconds':30}
 def test_no_success_or_repair_rate_is_fabricated(self):
  row=summarize({'initial_confirmed_defects':[],'arms':[self.item()]})['arms'][0]
  self.assertIsNone(row['repair_rate']);self.assertIsNone(row['successful_delivery_cost_seconds']);self.assertIsNone(row['false_discovery_rate_among_judged']);self.assertEqual(row['failed_endpoint_cost_seconds'],60)
 def test_uncertain_alarm_cannot_become_false_positive(self):
  item=self.item();item['alarm_causes']=['product','false_alarm','uncertain'];row=summarize({'initial_confirmed_defects':['a'],'arms':[item]})['arms'][0]
  self.assertEqual(row['false_discovery_rate_among_judged'],.5);self.assertEqual(row['false_discovery_bounds_all_alarms'],[1/3,2/3]);self.assertEqual(row['repair_rate'],1)
 def test_regression_prevents_success(self):
  item=self.item();item.update(native_complete=True,independent_quality_complete=True,unassessed=0,new_regressions=['b'])
  self.assertFalse(summarize({'initial_confirmed_defects':[],'arms':[item]})['arms'][0]['accepted'])
if __name__=='__main__':unittest.main()
