import json,subprocess,time
from pathlib import Path
workspace=Path(__file__).resolve().parents[2]
design=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T1/public')
compiler=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/candidate-v7/scripts/design_contract.py')
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  out=workspace/'agent-output'/'plans'/case/platform
  command=['python3',str(compiler),'compile','--lock',str(design/'design-lock.json'),'--lock-sha256','24a80e813cb3a2638499d9294fcacc0439891c680211ce85981a7a9b590c6b2c','--scenario',case,'--platform',platform,'--bindings',str(design/'bindings.json'),'--actions',str(design/'cases'/case/'actions.json'),'--output',str(out)]
  started=time.time(); result=subprocess.run(command,capture_output=True,text=True)
  log=workspace/'agent-output'/'logs'/f'plan-{case}-{platform}.log'; log.write_text(result.stdout+result.stderr)
  records.append({'command':command,'startedAtUnix':started,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log.relative_to(workspace))})
  print(case,platform,result.returncode,result.stdout,result.stderr)
(workspace/'agent-output'/'plan-commands.json').write_text(json.dumps(records,indent=2)+'\n')
if any(r['exitCode'] for r in records): raise SystemExit(1)
