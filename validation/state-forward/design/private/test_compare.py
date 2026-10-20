import unittest
from compare import compare

class FormatNeutralReviewTests(unittest.TestCase):
    def corpus(self,status):
        return dict(anonymousID='A',rows=[dict(cellID='row',classification='runtime.business.current',caseID='X',stateID='X.s0',status=status)])
    def test_zero_natural_failure_is_na(self):
        r=compare(self.corpus('P'),self.corpus('P'),{'claims':[]})
        self.assertIsNone(r['repairShare']);self.assertIsNone(r['reviewMatching']['combinedDetectionShare'])
    def test_failed_row_without_machine_findings_gets_equal_credit(self):
        claim=dict(claimID='v4-row',origin='typed',format='failedRow',typedCheckEstablished=True,typedNativeReportRefs=['actual-native-check.json#/row'],matches=[dict(cellID='row',adjudication='exact')])
        r=compare(self.corpus('F'),self.corpus('P'),{'claims':[claim]})
        self.assertEqual(r['repairShare'],1)
        self.assertEqual(r['reviewMatching']['combinedDetectionShare'],1)
        self.assertEqual(r['reviewMatching']['manualDetectionShare'],0)
    def test_planned_check_is_not_machine_detection(self):
        c=dict(claimID='plan',origin='typed',matches=[dict(cellID='row',adjudication='exact')])
        r=compare(self.corpus('F'),self.corpus('U'),{'claims':[c]})
        self.assertEqual(r['reviewMatching']['combinedDetectionShare'],0)
        self.assertEqual(r['reviewMatching']['claimCounts']['uncertainOrUnmapped'],1)
    def test_unmapped_and_false_claims_retained(self):
        claims=[dict(claimID='missing',origin='manual',matches=[]),dict(claimID='false',origin='manual',matches=[dict(cellID='row',adjudication='false')])]
        r=compare(self.corpus('P'),self.corpus('P'),{'claims':claims})['reviewMatching']
        self.assertEqual(len(r['claims']),2);self.assertEqual(r['conditionalFalseDiscoveryShare'],1);self.assertEqual(r['allUncertainConservativeInterval'],[.5,1])

if __name__=='__main__':unittest.main()
