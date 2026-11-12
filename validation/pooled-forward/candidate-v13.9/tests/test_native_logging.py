"""Actual interrupted subprocess logging; no native SDK or fabricated frames."""
import os
from pathlib import Path
import subprocess,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import resource_manager as rm


class NativeLoggingTests(unittest.TestCase):
 def test_interrupted_native_command_retains_original_stream_prefix(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp).resolve();source=root/'source';source.write_text('preserved')
   log=root/'partial-sdk.log';scripts=Path(__file__).resolve().parents[1]/'scripts'
   body='import time;print("real partial SDK stdout prefix",flush=True);time.sleep(20)'
   call='import sys,os;from pathlib import Path;sys.path.insert(0,'+repr(str(scripts))+');import ios_observe;ios_observe.command([sys.executable,"-c",'+repr(body)+'],dict(os.environ),Path('+repr(str(log))+'))'
   config={'source_roots':[str(source)],'native_options':{},'resources':{'root':str(root/'scratch'),'min_free_bytes':0,'sample_seconds':.1}}
   with self.assertRaises(subprocess.TimeoutExpired):
    with rm.Resources(config,root/'receipt',final=True)as manager:
     with (root/'outer.log').open('w')as outer:manager.run([sys.executable,'-B','-c',call],env=dict(os.environ),stdout=outer,timeout=1)
   self.assertIn('real partial SDK stdout prefix',log.read_text())
   self.assertEqual(source.read_text(),'preserved')

if __name__=='__main__':unittest.main()
