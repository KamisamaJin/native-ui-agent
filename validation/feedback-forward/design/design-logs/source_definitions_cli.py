#!/usr/bin/env python3
"""Run the actual shared definitions CLI with its frozen design dependency."""
from pathlib import Path
import sys,runpy
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
frozen=root.parent/'candidate-v9'/'scripts'
sys.path.insert(0,str(frozen))
import design_contract
assert Path(design_contract.__file__).resolve()==frozen/'design_contract.py'
utility=root.parents[2]/'tools'/'implementation_audit.py'
assert sys.argv[1]=='definitions','Design author may validate definitions only.'
sys.argv[0]=str(utility)
namespace=runpy.run_path(str(utility),run_name='__main__')
assert namespace['d'] is design_contract
