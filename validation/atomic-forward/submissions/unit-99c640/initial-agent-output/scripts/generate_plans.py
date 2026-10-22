from pathlib import Path
import subprocess, json, time, hashlib
W=Path(__file__).resolve().parents[2]
D=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public')
S=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/baseline-v7')
commands=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  out=W/'agent-output'/'plans'/case/platform
  cmd=['python3',str(S/'scripts/design_contract.py'),'compile','--lock',str(D/'design-lock.json'),'--lock-sha256','1595cbbb3a50848a0fe9a639bc775dde0a781690fc94381a6eb8f0a469d4c31a','--scenario',case,'--platform',platform,'--bindings',str(D/'bindings.json'),'--actions',str(D/'cases'/case/f'actions.{platform}.json'),'--output',str(out)]
  started=time.time();r=subprocess.run(cmd,text=True,capture_output=True)
  log=W/'agent-output'/'logs'/f'plan-{case}-{platform}.log';log.write_text(r.stdout+r.stderr)
  commands.append({'command':cmd,'startedAtUnix':started,'finishedAtUnix':time.time(),'exitCode':r.returncode,'log':str(log.relative_to(W))})
  print(case,platform,r.returncode,r.stdout,r.stderr)
(W/'agent-output'/'plan-command-record.json').write_text(json.dumps(commands,indent=2)+'\n')
