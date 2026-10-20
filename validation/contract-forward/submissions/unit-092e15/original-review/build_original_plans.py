from pathlib import Path
from datetime import datetime, timezone
import subprocess, json
root=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
out=Path(__file__).resolve().parent
records=[]
for scenario in ['P1','P2']:
 for platform in ['ios','android']:
  dest=out/'plans'/scenario/platform
  cmd=['python3',str(root/'candidate-v6/scripts/design_contract.py'),'compile','--lock',str(root/'design/public/design-lock.json'),'--lock-sha256','c2548a601384046a016e98258728877982f30a4ed25be22455d9ec9ea4399bc1','--scenario',scenario,'--platform',platform,'--bindings',str(root/'design/public/bindings.json'),'--actions',str(root/f'design/public/cases/{scenario}/actions.{platform}.json'),'--output',str(dest)]
  start=datetime.now(timezone.utc).isoformat()
  r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  record={'argv':cmd,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'exit_code':r.returncode,'output':r.stdout}
  records.append(record)
  print(scenario,platform,r.returncode,r.stdout[:300])
(out/'plan-compile-records.json').write_text(json.dumps(records,indent=2)+'\n')
if any(r['exit_code'] for r in records): raise SystemExit(1)
