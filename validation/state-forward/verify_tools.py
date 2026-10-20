#!/usr/bin/env python3
"""Check prospective tool snapshots, unchanged callback gate, and matrix output."""
import ast,hashlib,json,sys
from datetime import datetime
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 for name in ['baseline-v4','candidate-v5']:
  freeze=read(R/(name+'-freeze.json'))
  for rel,h in freeze['files'].items():assert sha(R/name/rel)==h,(name,rel)
  actual={str(p.relative_to(R/name))for p in(R/name).rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.name!='.DS_Store'}
  assert actual==set(freeze['files'])
 old=ast.parse((R/'baseline-v4/scripts/native_checks.py').read_text());new=ast.parse((R/'candidate-v5/scripts/native_checks.py').read_text())
 body=lambda tree:ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='callback_verdict'),include_attributes=False)
 assert body(old)==body(new),'Callback behavior gate changed'
 sys.path.insert(0,str(R/'candidate-v5/scripts'));import state_plan
 plan,actions=state_plan.compile_matrix(read(R/'generic/matrix.json'),read(R/'generic/actions-base.json'))
 assert plan==read(R/'generic/compiled/plan.json')and actions==read(R/'generic/compiled/actions.json')
 independent=read(R/'independent-generic/summary.json')
 assert independent['status']=='passed_for_declared_scope'and len(independent['runs'])==4
 freeze=read(R/'candidate-v5-freeze.json')
 assert sha(R/'independent-generic/summary.json')==freeze['independentSummarySHA256']
 assert sha(R/'generic-summary.json')==freeze['rootGenericSummarySHA256']
 print('PASS: immutable v4/v5 tools, unchanged callback gate, declared matrix, independent predesign native validation')
if __name__=='__main__':main()
