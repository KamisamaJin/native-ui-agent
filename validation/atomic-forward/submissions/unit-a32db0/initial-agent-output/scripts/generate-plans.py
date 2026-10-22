import json,subprocess,time,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
skill=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/candidate-v8')
design=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T2/public')
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  argv=['python3',str(skill/'scripts/design_contract.py'),'compile','--lock',str(design/'design-lock.json'),'--lock-sha256','c21f3c012a188c7c39e8017dc92e8749b821a74aa3ad84d007732cfffa48e000','--scenario',case,'--platform',platform,'--bindings',str(design/'bindings.json'),'--actions',str(design/f'cases/{case}/actions.{platform}.json'),'--output',str(root/f'agent-output/plans/{case}/{platform}')]
  start=time.time(); p=subprocess.run(argv,cwd=root,text=True,capture_output=True); end=time.time()
  log=root/f'agent-output/logs/plan-{case}-{platform}.log'; log.write_text(p.stdout+p.stderr)
  records.append({'argv':argv,'cwd':str(root),'startedAtUnix':start,'finishedAtUnix':end,'returncode':p.returncode,'log':str(log.relative_to(root))})
  (root/'agent-output/plan-commands.json').write_text(json.dumps(records,indent=2)+'\n')
  print(case,platform,p.returncode,p.stdout,p.stderr)
  if p.returncode: raise SystemExit(p.returncode)
