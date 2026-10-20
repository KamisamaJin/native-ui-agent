#!/usr/bin/env python3
"""Known enum aliases, rejection boundaries, and actual native wire integration."""
import importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[1]/'tools'))
from native_environment import direction,ENCODING
class NativeEnvironmentTests(unittest.TestCase):
 def test_known_wire_identifiers(self):
  for raw,want in [('Ltr','ltr'),('Rtl','rtl'),('ltr','ltr'),('rtl','rtl')]:
   self.assertEqual(direction(raw,encoding=ENCODING),dict(raw=raw,canonical=want,recognized=True,encoding=ENCODING))
 def test_no_case_or_locale_guess(self):
  for raw in ['LTR','RTL','left-to-right',' Ltr','',None,0,False,[],{}]:
   d=direction(raw,encoding=ENCODING);self.assertFalse(d['recognized']);self.assertEqual(d['raw'],raw);self.assertEqual(d['canonical'],raw)
 def test_provider_must_be_explicit(self):
  with self.assertRaises(ValueError):direction('Ltr',encoding='unknown-provider')
 def test_real_predesign_wire_records(self):
  paths=sorted((R/'generic-evidence-v2').glob('*android*/observation.json'));self.assertEqual(len(paths),4)
  for p in paths:
   raw=json.loads(p.read_text())['configuration']['direction'];self.assertEqual(raw,'Ltr');self.assertEqual(direction(raw,encoding=ENCODING)['canonical'],'ltr')
 def test_shared_patch_does_not_change_native_assertions(self):
  # Same actual native input and exact frozen native report; only input gate differs.
  spec=importlib.util.spec_from_file_location('shared_oracle',R/'shared-environment-v1/oracle_common.py');fixed=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixed)
  spec=importlib.util.spec_from_file_location('original_oracle',R/'design-v2/oracle_common.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  task=R/'design-v2/T1';op=R/'common-corpora/T1/source-a/d0/android/P1/observation.json'
  a=old.grade_task(task,'P1','android',op);b=fixed.grade_task(task,'P1','android',op)
  self.assertEqual(a['native_report'],b['native_report']);self.assertEqual(len(a['rows']),len(b['rows']))
  for x,y in zip(a['rows'],b['rows']):
   self.assertEqual({k:x[k]for k in ['id','expected','unit','op','tolerance']},{k:y[k]for k in ['id','expected','unit','op','tolerance']})
  ar=next(x for x in a['input_checks']if x['id']=='native-environment');br=next(x for x in b['input_checks']if x['id']=='native-environment');self.assertEqual(ar['status'],'F');self.assertEqual(br['status'],'P');self.assertEqual(br['direction_encoding_proof']['raw'],'Ltr')
if __name__=='__main__':unittest.main()
