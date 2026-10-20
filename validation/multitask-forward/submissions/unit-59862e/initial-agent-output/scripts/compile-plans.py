import json, subprocess, time
from pathlib import Path
workspace = Path(__file__).resolve().parents[2]
public = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T3/public')
skill = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/baseline-v6')
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  output=workspace/'agent-output'/'plans'/case/platform
  command=['python3',str(skill/'scripts/design_contract.py'),'compile','--lock',str(public/'design-lock.json'),'--lock-sha256','97d640f5a1ed98aabd13caf59d593c307d4488030dec031a529554ad023e3b42','--scenario',case,'--platform',platform,'--bindings',str(public/'bindings.json'),'--actions',str(public/'cases'/case/'actions.json'),'--output',str(output)]
  start=time.time(); result=subprocess.run(command,capture_output=True,text=True)
  log=workspace/'agent-output'/'logs'/f'plans-{case}-{platform}.log';log.write_text(result.stdout+result.stderr)
  records.append({'command':command,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log)})
  print(case, platform, result.returncode, result.stdout, result.stderr)
(workspace/'agent-output'/'plan-commands.json').write_text(json.dumps(records,indent=2)+'\n')
