import json,subprocess,time,shutil
from pathlib import Path
w=Path(__file__).resolve().parents[2];out=w/'agent-output/repair';build=w/'cache/compile-ios-repair'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(w),'--platform','ios','--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T3/public/Bridge.swift','--output',str(build)]
start=time.time();record={'command':command,'startedAtUnix':start,'status':'running'}
(out/'compile-command.json').write_text(json.dumps(record,indent=2)+'\n')
with (out/'compile-helper.log').open('w') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
record.update({'finishedAtUnix':time.time(),'exitCode':result.returncode,'status':'finished','log':str(out/'compile-helper.log')})
(out/'compile-command.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ['build.log','record.json']:
 if (build/name).exists():shutil.copyfile(build/name,out/name)
print(json.dumps(record,indent=2))
