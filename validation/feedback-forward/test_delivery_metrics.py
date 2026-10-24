import unittest
from delivery_metrics import compare,cost
class DeliveryTests(unittest.TestCase):
 def test_unknown_is_not_repaired_and_regression_is_distinct(self):
  initial=[{'key':'a','status':'failed','cause_category':'product'},{'key':'b','status':'passed'}]
  final=[{'key':'a','status':'unassessed'},{'key':'b','status':'failed','cause_category':'product'}]
  result=compare(initial,final,[['a']],{'a','b'})
  self.assertEqual(result['repairs']['productRowRepairRate'],0)
  self.assertEqual(result['unresolvedMustRows'],['a'])
  self.assertEqual(result['confirmedProductRegressions'],['b'])
 def test_missing_initial_row_is_rejected(self):
  with self.assertRaises(AssertionError):compare([{'key':'a','status':'passed'}],[],[],{'a'})
 def test_no_natural_bug_keeps_rate_undefined(self):
  result=compare([{'key':'a','status':'passed'}],[{'key':'a','status':'passed'}],[],{'a'})
  self.assertIsNone(result['repairs']['productRowRepairRate'])
  self.assertIsNone(result['finalPublicMissRate'])
 def test_verification_result_is_not_acceptance_latency(self):
  self.assertIsNone(cost(10,30,[],True)['handoffToAcceptedSeconds'])
  self.assertEqual(cost(10,30,[],True,45)['handoffToAcceptedSeconds'],35)
  with self.assertRaises(AssertionError):cost(10,30,[],False,45)
if __name__=='__main__':unittest.main()
