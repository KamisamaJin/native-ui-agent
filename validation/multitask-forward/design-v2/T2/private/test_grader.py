from pathlib import Path
import sys,unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from v2_oracle_controls import NewTaskControls
class TaskControls(NewTaskControls):
    TASK='T2'
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TaskControls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
