import sys,time,json,subprocess
from pathlib import Path
workspace=Path(__file__).resolve().parent.parent
platform=sys.argv[1]
label=sys.argv[2]
output=workspace/'cache'/label
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios': cmd+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T3/public/Bridge.swift']
start=time.time();r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
log=workspace/'agent-output'/f'{label}.log';log.write_text(r.stdout)
record={'argv':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':r.returncode,'log':str(log),'output':str(output)}
(workspace/'agent-output'/f'{label}-command.json').write_text(json.dumps(record,indent=2)+'\n')
for p in output.rglob('*.json'):
 if p.name in ['compile.json','record.json','build-record.json']:
  (workspace/'agent-output'/f'{label}-{p.name}').write_text(p.read_text())
print(json.dumps(record,indent=2));print(r.stdout[-7000:]);sys.exit(r.returncode)
