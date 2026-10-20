import json,subprocess,time,shutil
from pathlib import Path
out=Path(__file__).resolve().parent
workspace=out.parents[1]
cache=workspace/'cache/ios-repair-compile-01'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform','ios','--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T1/public/Bridge.swift','--output',str(cache)]
record={'command':command,'startedAtUnix':time.time()}
(out/'compile-running.json').write_text(json.dumps(record,indent=2)+'\n')
r=subprocess.run(command,capture_output=True,text=True)
(out/'compile-wrapper.log').write_text(r.stdout+r.stderr)
record.update(finishedAtUnix=time.time(),exitCode=r.returncode)
(out/'compile-command.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ['record.json','build.log']:
 if (cache/name).exists():shutil.copyfile(cache/name,out/f'ios-{name}')
print(json.dumps(record,indent=2));print(r.stdout[-2200:]);print(r.stderr[-2200:])
raise SystemExit(r.returncode)
