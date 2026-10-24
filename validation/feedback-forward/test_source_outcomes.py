import unittest
from source_outcomes import summarize
class Tests(unittest.TestCase):
 def test_unknown_not_fixed_and_false_release_needs_known_product_violation(self):
  before=[{'id':'a','priority':'must','status':'failed','cause_category':'product'},{'id':'b','priority':'must','status':'passed'}]
  after=[dict(before[0],status='unassessed'),dict(before[1],status='failed',cause_category='product')]
  own=[{'id':'a','status':'unassessed'},{'id':'b','status':'passed'}]
  result=summarize(before,after,own,own,complete_accepted=True)
  self.assertEqual(result['repairRate'],0);self.assertEqual(result['repairUnknown'],['a']);self.assertEqual(result['finalKnownMisses'],['b']);self.assertTrue(result['confirmedSourceFalseRelease'])
 def test_no_product_denominator_stays_undefined(self):
  rows=[{'id':'a','priority':'must','status':'passed'}];out=summarize(rows,rows,rows,rows,complete_accepted=True);self.assertIsNone(out['repairRate']);self.assertIsNone(out['knownMissRate'])
if __name__=='__main__':unittest.main()
