from review3_support import *
import runpy,resource_manager
resource_manager.Resources.run=recording_collector
sys.argv=[str(CANDIDATE/'scripts'/'ui_loop.py'),*sys.argv[1:]]
runpy.run_path(str(CANDIDATE/'scripts'/'ui_loop.py'),run_name='__main__')
