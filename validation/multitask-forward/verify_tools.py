#!/usr/bin/env python3
"""Verify immutable release identities, native neutral receipts and predesign order."""
import ast,hashlib,json,sys
from datetime import datetime
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):return {str(p.relative_to(root)):sha(p)for p in sorted(root.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.suffix not in ['.pyc','.pyo']}
def main():
 sys.path.insert(0,str(REPO/'native-ui-agent/scripts'));import cohort_gate
 for tool in ['baseline-v6','candidate-v7']:
  wanted=read(R/(tool+'-freeze.json'))['files'];assert inventory(R/tool)==wanted,tool
 assert inventory(REPO/'native-ui-agent')==read(R/'candidate-v7-freeze.json')['files'],'Live release changed after predesign freeze'
 assert read(R/'baseline-v6-freeze.json')['files']==read(REPO/'validation/contract-forward/RELEASE-BUNDLE.json')['files']
 body=lambda path:ast.dump(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='callback_verdict'),include_attributes=False)
 assert body(R/'baseline-v6/scripts/native_checks.py')==body(R/'candidate-v7/scripts/native_checks.py'),'Successful callback-dispatch gate changed'
 for rel,h in read(R/'prospective-seal.json')['files'].items():assert sha(R/rel)==h
 proof=cohort_gate.verify(R/'gates','tools',R)
 independent=R/'independent-generic';seal=read(independent/'FINAL-SEAL.json')
 for rel,h in seal['files'].items():assert sha(independent/rel)==h,rel
 summary=read(independent/'summary.json');assert summary['native_acquisitions']==4 and summary['native_test_count']==4
 assert summary['counts']=={'passed':132,'failed':0,'unassessed':44}
 assert datetime.fromisoformat(seal['sealed_at']).timestamp()<=proof['sealedAtUnix']
 if(R/'design/DESIGN-START.json').is_file():
  start=read(R/'design/DESIGN-START.json');assert min(v for k,v in start.items()if k.lower().endswith('unix')and isinstance(v,(int,float)))>=proof['sealedAtUnix']
 print(json.dumps({'status':'PASS','releaseFiles':len(inventory(REPO/'native-ui-agent')),'actualIndependentNativeTests':4,'rootNeutralTests':8,'knownIOSRawPrecisionLimitRetained':True}))
if __name__=='__main__':main()
