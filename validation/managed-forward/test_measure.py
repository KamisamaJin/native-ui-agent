from pathlib import Path
import json,tempfile,time,unittest
from measure import Meter,allocated


class MeasurementTests(unittest.TestCase):
 def test_observed_peak_and_final_residual_are_different(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);group=root/'arm';group.mkdir();out=root/'samples.jsonl'
   spec={'sample_seconds':.1,'groups':{'anonymous':{'paths':[str(group)]}},'filesystem_root':str(root),'max_total_allocated_bytes':1024,'min_free_bytes':0}
   with Meter(spec,out)as meter:
    p=group/'transient';p.write_bytes(b'x'*32000);meter.boundary('allocated');p.unlink();meter.boundary('released')
   result=json.loads(out.with_suffix('.summary.json').read_text())
   self.assertGreater(result['observed_peak_allocated_bytes']['anonymous'],0);self.assertEqual(result['post_run_allocated_bytes']['anonymous'],0)
   self.assertTrue(result['budget_exceeded']);self.assertIsNone(result['sampling_error'])
 def test_same_file_union_does_not_double_count_nested_roots(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);q=p/'nested';q.mkdir();(q/'object').write_bytes(b'y'*12000)
   self.assertEqual(allocated([p,q]),allocated([p]))

if __name__=='__main__':unittest.main()
