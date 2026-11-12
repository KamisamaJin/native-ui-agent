import hashlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'revision-v8/alarm-material-tools-v8/batch.py'
RAW=SOURCE.read_bytes()
def fresh():
    module=types.ModuleType('fresh_private_batch_pin_control');module.__file__=str(SOURCE)
    exec(compile(RAW,str(SOURCE),'exec'),module.__dict__);return module
class CodePins(unittest.TestCase):
    def test_changed_local_lens_code_fails_before_data_access(self):
        real=Path.read_bytes
        def changed(path):
            raw=real(path);return raw+b'\n'if path.name=='claim_metadata_lens.py'else raw
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaisesRegex(ValueError,'Pinned metadata lens source differs'):fresh()
    def test_cached_host_module_cannot_replace_verified_private_lens(self):
        fake=types.ModuleType('claim_metadata_lens');fake.sha=lambda raw:'forged'
        with patch.dict(sys.modules,{'claim_metadata_lens':fake,'lens':fake,'batch_private_worker_metadata_lens':fake}):
            module=fresh()
            self.assertIsNot(module.lens,fake);self.assertEqual(module.lens.sha(b'fixture'),hashlib.sha256(b'fixture').hexdigest())
if __name__=='__main__':unittest.main()
