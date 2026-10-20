import json, pathlib, subprocess, time
workspace=pathlib.Path(__file__).resolve().parents[2]
skill=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/baseline-v6')
design=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T1/public')
records=[]
for case in ('P1','P2'):
 for platform in ('ios','android'):
  output=workspace/'agent-output'/'plans'/case/platform
  command=['python3',str(skill/'scripts/design_contract.py'),'compile','--lock',str(design/'design-lock.json'),'--lock-sha256','24a80e813cb3a2638499d9294fcacc0439891c680211ce85981a7a9b590c6b2c','--scenario',case,'--platform',platform,'--bindings',str(design/'bindings.json'),'--actions',str(design/'cases'/case/'actions.json'),'--output',str(output)]
  start=time.time();p=subprocess.run(command,text=True,capture_output=True)
  log=workspace/'agent-output'/'logs'/f'plans-{case}-{platform}.log';log.write_text(p.stdout+p.stderr)
  records.append({'command':command,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':p.returncode,'log':str(log.relative_to(workspace))})
  print(case,platform,p.returncode,p.stdout,p.stderr)
  if p.returncode: break
(workspace/'agent-output'/'plan-commands.json').write_text(json.dumps(records,indent=2))
