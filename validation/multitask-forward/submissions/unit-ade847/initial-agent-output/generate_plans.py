import json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parent.parent
DESIGN=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T2/public')
COMPILER=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/baseline-v6/scripts/design_contract.py')
DIGEST='3f151681f5478eef9359ce6de0c8ce51ca2b8785581a7c7a594285d57d2dd152'
for case in ['P1','P2']:
 for platform in ['ios','android']:
  out=ROOT/'agent-output'/'plans'/case/platform
  cmd=['python3',str(COMPILER),'compile','--lock',str(DESIGN/'design-lock.json'),'--lock-sha256',DIGEST,'--scenario',case,'--platform',platform,'--bindings',str(DESIGN/'bindings.json'),'--actions',str(DESIGN/'cases'/case/'actions.json'),'--output',str(out)]
  start=time.time(); result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  log=ROOT/'agent-output'/f'plan-{case}-{platform}.log';log.write_text(result.stdout+result.stderr)
  with open(ROOT/'agent-output'/'commands.jsonl','a') as f: f.write(json.dumps({'command':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log.relative_to(ROOT))})+'\n')
  print(case,platform,result.returncode,result.stdout,result.stderr)
  if result.returncode: raise SystemExit(result.returncode)
