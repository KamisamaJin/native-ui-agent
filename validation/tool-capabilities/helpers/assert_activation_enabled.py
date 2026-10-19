#!/usr/bin/env python3
"""Caller assertions on actual native activation leaf facts; one intentional negative.

Inputs are native observer records, never source code or inferred fixture state.
Expected indices are the frozen v2 semantic positive action mapping.
"""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--output',required=True);a=p.parse_args()
root=Path(a.evidence);path=root/'observation.json';o=json.loads(path.read_text());m=json.loads((root/'manifest.json').read_text())
def activation(index):
    s=o['steps'][index]
    leaf=s.get('activation_target') or {}
    role=str(leaf.get('role','')).lower()
    known=bool(leaf) and (leaf.get('role_raw')==9 or role=='button' or role.endswith('.button')) and isinstance(leaf.get('enabled'),bool)
    return s,leaf,known
checks=[]
for check_id,index,expected in [('S9',0,True),('S10',0,False),('S11',3,True)]:
    step,leaf,known=activation(index)
    actual=leaf.get('enabled') if known else None
    result='passed' if known and actual is expected else 'failed' if known else 'unknown'
    checks.append({'assertion_id':check_id,'source':'actual native activation_target','step_index':index,'expected_enabled':expected,'actual_enabled':actual,'actual_native_role':leaf.get('role'),'actual_native_role_raw':leaf.get('role_raw'),'actual_identifier':leaf.get('identifier'),'known_native_button_leaf':known,'assertion_status':result,'expected_assertion_status':'failed' if check_id=='S9' else 'passed','callback_delta':step.get('callback_delta'),'raw_activation_target':leaf})
report={'observation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_test_count':m.get('native_test_count',0),'assertions':checks,'capability_status':'passed' if m.get('native_test_count',0)>0 and all(c['assertion_status']==c['expected_assertion_status'] for c in checks) else 'failed'}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'capability_status':report['capability_status'],'assertions':[{k:c[k] for k in ['assertion_id','actual_enabled','assertion_status','expected_assertion_status']} for c in checks]},indent=2))
