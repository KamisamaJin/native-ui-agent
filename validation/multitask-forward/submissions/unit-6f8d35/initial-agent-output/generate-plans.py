import pathlib, subprocess, json, time, hashlib
workspace=pathlib.Path(__file__).resolve().parent.parent
public=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T2/public')
compiler=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/candidate-v7/scripts/design_contract.py')
pin='3f151681f5478eef9359ce6de0c8ce51ca2b8785581a7c7a594285d57d2dd152'
lock=json.loads((public/'design-lock.json').read_text())
canonical=json.dumps(lock,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
assert hashlib.sha256(canonical).hexdigest()==pin
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  output=workspace/'agent-output'/'plans'/case/platform
  command=['python3',str(compiler),'compile','--lock',str(public/'design-lock.json'),'--lock-sha256',pin,'--scenario',case,'--platform',platform,'--bindings',str(public/'bindings.json'),'--actions',str(public/'cases'/case/'actions.json'),'--output',str(output)]
  started=time.time(); result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log=workspace/'agent-output'/('plan-'+case+'-'+platform+'.log');log.write_text(result.stdout)
  records.append({'command':command,'startedAtUnix':started,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log.relative_to(workspace))})
  print(case,platform,result.returncode,result.stdout.strip())
  (workspace/'agent-output'/'plan-commands.json').write_text(json.dumps(records,indent=2))
  if result.returncode: raise SystemExit(result.returncode)
