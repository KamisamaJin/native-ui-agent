import datetime, json, pathlib, subprocess
ROOT=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
WORK=ROOT/'cache/unit-179c84'
PUBLIC=ROOT/'design-v2/T3/public'
SKILL=ROOT/'baseline-v7'
records=[]
for case in ('P1','P2'):
 for platform in ('ios','android'):
  output=WORK/'agent-output/plans'/case/platform
  command=['python3',str(SKILL/'scripts/design_contract.py'),'compile','--lock',str(PUBLIC/'design-lock.json'),'--lock-sha256','0653c194d723fbb087b20ee8eac97b1388256ff2b8e3ba6db203c7a45cec4656','--scenario',case,'--platform',platform,'--bindings',str(PUBLIC/'bindings.json'),'--actions',str(PUBLIC/'cases'/case/f'actions.{platform}.json'),'--output',str(output)]
  start=datetime.datetime.now(datetime.timezone.utc)
  result=subprocess.run(command,capture_output=True,text=True)
  log=WORK/'agent-output/logs'/f'plans-{case}-{platform}.log'
  log.write_text(result.stdout+result.stderr)
  records.append({'command':command,'startedAtUtc':start.isoformat(),'finishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':result.returncode,'log':str(log.relative_to(WORK))})
  print(case,platform,result.returncode,result.stdout,result.stderr)
(WORK/'agent-output/plan-commands.json').write_text(json.dumps(records,indent=2)+'\n')
if any(r['exitCode'] for r in records): raise SystemExit(1)
