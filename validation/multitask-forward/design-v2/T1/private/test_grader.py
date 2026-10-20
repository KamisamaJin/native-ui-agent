from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from test_oracle_common import OracleControls
class TaskControls(OracleControls):
    TASK='T1'
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TaskControls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
