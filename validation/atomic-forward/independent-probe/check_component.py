import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts';a=json.loads((R/'APPROVAL.json').read_text());key=sys.argv[1];platform=key.split('-')[0];base=key.removesuffix('-v2');out=R/'checks'/f'{key}.json';out.parent.mkdir(exist_ok=True)
cmd=[sys.executable,str(S/'native_checks.py'),'--plan',str(R/'generated'/base/'plan.json'),'--observation',str(R/'captures'/key/'observation.json'),'--platform',platform,'--manual',str(R/'reviews'/key/'manual.json'),'--design-lock',str(R/'design/lock.json'),'--design-sha256',a['design_lock_sha256'],'--review-policy',str(R/'design/policy.json'),'--review-policy-sha256',a['policy_sha256'],'--output',str(out)]
sys.exit(subprocess.run([sys.executable,str(R/'run.py')]+cmd).returncode)
