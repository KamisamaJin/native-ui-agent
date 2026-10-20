import subprocess,json,time
from pathlib import Path
root=Path(__file__).resolve().parent
skill=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/candidate-v7')
design=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T3/public')
commands=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  dest=root/'plans'/case/platform
  cmd=['python3',str(skill/'scripts/design_contract.py'),'compile','--lock',str(design/'design-lock.json'),'--lock-sha256','97d640f5a1ed98aabd13caf59d593c307d4488030dec031a529554ad023e3b42','--scenario',case,'--platform',platform,'--bindings',str(design/'bindings.json'),'--actions',str(design/'cases'/case/'actions.json'),'--output',str(dest)]
  t=time.time(); result=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log=root/f'plan-{case}-{platform}.log';log.write_text(result.stdout)
  commands.append({'argv':cmd,'startedAtUnix':t,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log)})
  print(case,platform,result.returncode,result.stdout[-500:])
  (root/'plan-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  if result.returncode: raise SystemExit(result.returncode)
