import json,pathlib,subprocess,time
workspace=pathlib.Path(__file__).resolve().parents[2]
public=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T3/public')
compiler=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/candidate-v8/scripts/design_contract.py')
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  output=workspace/'agent-output'/'plans'/case/platform
  command=['python3',str(compiler),'compile','--lock',str(public/'design-lock.json'),'--lock-sha256','0653c194d723fbb087b20ee8eac97b1388256ff2b8e3ba6db203c7a45cec4656','--scenario',case,'--platform',platform,'--bindings',str(public/'bindings.json'),'--actions',str(public/'cases'/case/f'actions.{platform}.json'),'--output',str(output)]
  start=time.time()
  p=subprocess.run(command,capture_output=True,text=True)
  log=workspace/'agent-output'/'logs'/f'plans-{case}-{platform}.log'
  log.write_text(p.stdout+p.stderr)
  records.append({'command':command,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':p.returncode,'log':str(log.relative_to(workspace))})
  (workspace/'agent-output'/'plan-commands.json').write_text(json.dumps(records,indent=2)+'\n')
  print(case,platform,p.returncode,p.stdout,p.stderr)
  if p.returncode: raise SystemExit(p.returncode)
