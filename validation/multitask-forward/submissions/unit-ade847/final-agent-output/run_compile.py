import pathlib,json,subprocess,time,shutil
work=pathlib.Path(__file__).resolve().parents[2]; output=pathlib.Path(__file__).resolve().parent
run='repair-compile-ios-'+str(int(time.time())); cache=work/'cache'/run
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(work),'--platform','ios','--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T2/public/Bridge.swift','--output',str(cache)]
start=time.time();result=subprocess.run(cmd,cwd=work,text=True,capture_output=True)
log=output/(run+'.log');log.write_text(result.stdout+result.stderr)
record={'command':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log.relative_to(work)),'output':str(cache.relative_to(work))}
(output/(run+'.json')).write_text(json.dumps(record,indent=2)+'\n')
with open(output/'commands.jsonl','a') as f:f.write(json.dumps(record)+'\n')
for name in ['build.log','record.json']:
 p=cache/name
 if p.exists():
  target=output/'compile-logs'/run/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
print(json.dumps(record));print(result.stdout[-3000:]);print(result.stderr[-1000:])
raise SystemExit(result.returncode)
