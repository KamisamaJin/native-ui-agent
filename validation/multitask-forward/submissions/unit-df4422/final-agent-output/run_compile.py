import json,pathlib,subprocess,time,shutil
w=pathlib.Path(__file__).resolve().parents[2]
out=w/'agent-output/repair';cache=w/'cache/compile-ios-repair-1'
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(w),'--platform','ios','--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T1/public/Bridge.swift','--output',str(cache)]
record={'command':cmd,'startedAtUnix':time.time(),'output':str(cache)}
(out/'compile-command.json').write_text(json.dumps(record,indent=2))
with (out/'compile-command.log').open('w') as f:
 p=subprocess.run(cmd,cwd=w,text=True,stdout=f,stderr=subprocess.STDOUT)
record.update({'finishedAtUnix':time.time(),'exitCode':p.returncode})
(out/'compile-command.json').write_text(json.dumps(record,indent=2))
for name in ['build.log','record.json']:
 if (cache/name).exists():shutil.copy2(cache/name,out/name)
print(json.dumps(record,indent=2));print((out/'compile-command.log').read_text()[-4000:])
