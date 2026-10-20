import json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
platform=sys.argv[1]
run=f'compile-{platform}-{int(time.time())}'
out=root/'cache'/run
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(root),'--platform',platform,'--output',str(out)]
if platform=='ios': cmd += ['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T2/public/Bridge.swift']
start=time.time(); result=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
log=root/'agent-output'/(run+'.log'); log.write_text(result.stdout+result.stderr)
record={'command':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log.relative_to(root)),'output':str(out.relative_to(root))}
(root/'agent-output'/(run+'.json')).write_text(json.dumps(record,indent=2))
with open(root/'agent-output'/'commands.jsonl','a') as f: f.write(json.dumps(record)+'\n')
for file in out.rglob('*'):
 if file.is_file() and (file.suffix=='.log' or file.name.endswith('record.json')):
  import shutil
  destination=root/'agent-output'/'compile-logs'/run/file.relative_to(out)
  destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(file,destination)
print(json.dumps(record)); print(result.stdout[-8000:]);print(result.stderr[-2000:])
raise SystemExit(result.returncode)
