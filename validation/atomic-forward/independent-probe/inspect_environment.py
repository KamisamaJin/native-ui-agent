import json,sys,hashlib,inspect,time
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts';sys.path.insert(0,str(S))
import acceptance
out={'checked_epoch':time.time(),'evaluator_sha256':hashlib.sha256((S/'acceptance.py').read_bytes()).hexdigest(),'scope':'Environment-only evaluator on original observations. No two-judge independent acceptance claimed. Expected widths remain390/260.','runs':{}}
for key in ['android-normal','android-narrow-large']:
 p=R/'captures'/key/'observation.json';env=json.loads((R/'environment'/f'{key}.json').read_text())
 out['runs'][key]={'observation_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'environment':acceptance.environment(json.loads(p.read_text()),env,'android')}
(R/'original-environment-checks.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v['environment']['status']for k,v in out['runs'].items()})
t=R/'tools-used';t.mkdir(exist_ok=True)
(t/'acceptance-at-environment-check.py').write_bytes((S/'acceptance.py').read_bytes())
