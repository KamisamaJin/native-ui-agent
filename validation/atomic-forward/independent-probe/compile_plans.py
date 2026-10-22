import json,sys,subprocess,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts';a=json.loads((R/'APPROVAL.json').read_text())
for platform in ['ios','android']:
 for scenario in ['normal','narrow-large']:
  out=R/'generated'/f'{platform}-{scenario}'
  for cmd in [[sys.executable,str(S/'design_contract.py'),'compile','--lock',str(R/'design/lock.json'),'--lock-sha256',a['design_lock_sha256'],'--scenario',scenario,'--platform',platform,'--bindings',str(R/'bindings.json'),'--actions',str(R/'actions.json'),'--output',str(out)],[sys.executable,str(S/'review_contract.py'),'catalog','--plan',str(out/'plan.json'),'--design-lock',str(R/'design/lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(R/'design/policy.json'),'--policy-sha256',a['policy_sha256'],'--platform',platform,'--output',str(out/'catalog.json')]]:
   subprocess.run([sys.executable,str(R/'run.py')]+cmd,check=True)
(R/'implementation-seal.json').write_text(json.dumps({'epoch':time.time(),'files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in list((R/'sources').glob('*'))+list((R/'bridges').glob('*'))}},indent=2)+'\n')
