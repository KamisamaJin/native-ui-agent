from pathlib import Path
import subprocess,json,time,shutil
O=Path(__file__).resolve().parent;W=O.parents[1]
output=W/'cache/compile-ios-repair-01'
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(W),'--platform','ios','--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public/Bridge.swift','--output',str(output)]
start=time.time();r=subprocess.run(cmd,text=True,capture_output=True)
(O/'compile-ios-01-wrapper.log').write_text(r.stdout+r.stderr)
record={'command':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':r.returncode,'output':str(output),'wrapper_log':str(O/'compile-ios-01-wrapper.log')}
(O/'compile-ios-01-command.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ['build.log','record.json']:
 if (output/name).exists():shutil.copy2(output/name,O/f'compile-ios-01-{name}')
print(json.dumps(record));print(r.stdout[-3000:]);print(r.stderr[-3000:])
