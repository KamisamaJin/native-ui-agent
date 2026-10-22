import json,sys,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts';sys.path.insert(0,str(S));import acceptance
out={'checked_epoch':time.time(),'evaluator_sha256':hashlib.sha256((S/'acceptance.py').read_bytes()).hexdigest(),'scope':'Environment-only revised provider-specific check on fresh native acquisitions; no independent two-judge acceptance. No expected width or tolerance changed.','runs':{}}
for scenario in ['normal','narrow-large']:
 key='android-'+scenario+'-v2';p=R/'captures'/key/'observation.json';env=json.loads((R/'environment'/f'{key}.json').read_text())
 out['runs'][key]={'observation_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'environment':acceptance.environment(json.loads(p.read_text()),env,'android')}
(R/'revised-environment-checks.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v['environment']['status']for k,v in out['runs'].items()})
