#!/usr/bin/env python3
"""Old decision utilities with the identical shared acquisition compatibility layer."""
import argparse,runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'candidate-v10/scripts'))
import execution_plan
p=argparse.ArgumentParser();p.add_argument('module',choices=['requirement_routes','retest_plan']);a,rest=p.parse_known_args()
# The v9 decision algorithms remain frozen. Execution manifests are interpreted
# by the same pre-released acquisition compiler used by both conditions.
sys.path.insert(0,str(R/'baseline-v9/scripts'))
sys.argv=[a.module+'.py',*rest];runpy.run_path(str(R/'baseline-v9/scripts'/(a.module+'.py')),run_name='__main__')
