import unittest
from final_outcome_metrics import summarize
class FinalTests(unittest.TestCase):
 def test_final_miss_unknown_and_false_alarm_are_separate(self):
  truth=[{'key':k,'case':'P1','status':v,'cause_category':'product'if v=='failed'else None}for k,v in [('detected','failed'),('missed','failed'),('unknown','failed'),('false','passed')]]
  own=[{'key':k,'status':v}for k,v in [('detected','failed'),('missed','passed'),('unknown','unassessed'),('false','failed')]]
  out=summarize(truth,own,{v['key']for v in truth},self_accepted=False)
  self.assertEqual(out['finalKnownFalseNegatives'],['missed']);self.assertEqual(out['finalUnresolvedProductFailures'],['unknown']);self.assertEqual(out['finalKnownFalseAlarmRows'],['false'])
  self.assertEqual(out['missBounds'],[1/3,2/3]);self.assertFalse(out['confirmedFalseRelease'])
 def test_hidden_and_zero_public_denominator_are_not_invented_repairs(self):
  out=summarize([{'key':'hidden','case':'H1','status':'failed','cause_category':'product'}],[],{'hidden'},self_accepted=True)
  self.assertIsNone(out['knownMissRate']);self.assertEqual(out['hiddenConfirmedMustFailures'],['hidden']);self.assertFalse(out['confirmedFalseRelease'])
 def test_missing_self_row_is_rejected(self):
  with self.assertRaises(AssertionError):summarize([{'key':'a','case':'P1','status':'passed'}],[],{'a'},self_accepted=True)
if __name__=='__main__':unittest.main()
