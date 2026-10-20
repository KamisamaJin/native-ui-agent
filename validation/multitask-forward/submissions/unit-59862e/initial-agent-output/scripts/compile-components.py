import json, subprocess, time, sys
from pathlib import Path
workspace = Path(__file__).resolve().parents[2]
platform=sys.argv[1]
output=workspace/'cache'/f'compile-{platform}-initial'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios':command += ['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T3/public/Bridge.swift']
started=time.time()
log=workspace/'agent-output'/'logs'/f'compile-{platform}-initial.log'
record=workspace/'agent-output'/f'compile-{platform}-command.json'
record.write_text(json.dumps({'command':command,'startedAtUnix':started,'status':'running','log':str(log)},indent=2)+'\n')
with log.open('w') as stream: result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
record.write_text(json.dumps({'command':command,'startedAtUnix':started,'finishedAtUnix':time.time(),'exitCode':result.returncode,'log':str(log)},indent=2)+'\n')
for path in output.rglob('*'):
 if path.is_file() and (path.name.endswith('.log') or path.name in ['record.json','build-record.json','compile.json']):
  import shutil
  dest=workspace/'agent-output'/'logs'/f'{platform}-{path.name}'
  if dest.exists():dest=dest.with_name(f'{platform}-{path.parent.name}-{path.name}')
  shutil.copyfile(path,dest)
print(platform, result.returncode, log.read_text()[-10000:])
