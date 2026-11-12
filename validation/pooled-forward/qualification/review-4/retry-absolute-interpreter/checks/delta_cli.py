from delta_support import *
import resource_manager,runpy
resource_manager.Resources.run=delta_collector
sys.argv=[str(CANDIDATE/'scripts'/'ui_loop.py'),*sys.argv[1:]]
runpy.run_path(str(CANDIDATE/'scripts'/'ui_loop.py'),run_name='__main__')
