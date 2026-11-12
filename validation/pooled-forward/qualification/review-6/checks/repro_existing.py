"""Read-only repro from archived review artifacts; never uses a native SDK."""
import argparse,sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--arm',choices=['candidate-v13.5','baseline-v12.6-common-2'],required=True);p.add_argument('--case',choices=['A07-raster16-lowbit-admitted-host','A08-joint-witness-admitted-host','A09-forged-runtime-shape','A11-late-presence','A12-late-unique','A14-real-duplicate-then-one'],required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];pooled=root.parents[1];sys.path.insert(0,str(pooled/a.arm/'scripts'))
import native_checks
run='admitted-runtime-retry-1'if a.arm=='candidate-v13.5'else'admitted-runtime';folder=root/'work'/a.arm/run/a.case;o=json.loads((folder/'observation.json').read_text());s=json.loads((folder.parent/'A01-approved-runtime-shape-positive/state.json').read_text());native=folder/'packet/native';found,full,reason,cap=native_checks.bound_state_evidence(o,s,native)
if a.case.startswith(('A11','A12','A14')):
 prop='present'if a.case.startswith('A11')else'unique';target='semantic-target';expected=True
else:prop='present';target='absent-target';expected=False
plan={'version':1,'states':[s],'required_assertion_ids':['repro'],'assertions':[{'id':'repro','state':'start','kind':'control','target':{'identifier':target},'property':prop,'expected':expected}]};report=native_checks.evaluate(plan,o,'ios',root=native)
print(json.dumps({'evidence_class':'HOST read-only validator invocation on SIMULATED archived packet','native_runs':0,'observation':str(folder/'observation.json'),'observation_sha256':hashlib.sha256((folder/'observation.json').read_bytes()).hexdigest(),'full_content':full,'reason':reason,'status':report['assertions'][0]['status'],'actual':report['assertions'][0]['actual']},indent=2))
