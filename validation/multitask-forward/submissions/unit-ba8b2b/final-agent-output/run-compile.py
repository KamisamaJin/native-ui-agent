import sys,time,json,subprocess,shutil
from pathlib import Path
workspace=Path(__file__).resolve().parents[2]
platform=sys.argv[1];label=sys.argv[2]
output=workspace/'cache'/label
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios':cmd+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T3/public/Bridge.swift']
start=time.time();r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
out=workspace/'agent-output/repair';log=out/f'{label}.log';log.write_text(r.stdout)
record={'argv':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':r.returncode,'log':str(log),'output':str(output)}
(out/f'{label}-command.json').write_text(json.dumps(record,indent=2)+'\n')
for name in ['build.log','record.json']:
 p=output/name
 if p.is_file():shutil.copyfile(p,out/f'{label}-{name}')
print(json.dumps(record,indent=2));print(r.stdout[-4000:]);sys.exit(r.returncode)
