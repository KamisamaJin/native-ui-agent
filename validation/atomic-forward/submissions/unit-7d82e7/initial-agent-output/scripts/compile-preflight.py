import json,pathlib,subprocess,sys,time
workspace=pathlib.Path(__file__).resolve().parents[2]
platform=sys.argv[1]
attempt=sys.argv[2]
output=workspace/'cache'/f'compile-{platform}-{attempt}'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios': command += ['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T3/public/Bridge.swift']
log=workspace/'agent-output'/'logs'/f'compile-{platform}-{attempt}.log'
record=workspace/'agent-output'/f'compile-{platform}-{attempt}.json'
data={'command':command,'startedAtUnix':time.time(),'output':str(output.relative_to(workspace)),'log':str(log.relative_to(workspace)),'status':'running'}
record.write_text(json.dumps(data,indent=2)+'\n')
try:
 with log.open('w') as handle:
  process=subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT,timeout=650)
 data.update(status='passed' if process.returncode==0 else 'failed',exitCode=process.returncode)
except subprocess.TimeoutExpired:
 data.update(status='timeout',exitCode=None)
finally:
 data['finishedAtUnix']=time.time()
 record.write_text(json.dumps(data,indent=2)+'\n')
 for file in output.rglob('*.json'):
  if file.name in ['compile-record.json','record.json','build-record.json','compile.json']:
   (workspace/'agent-output'/f'{platform}-{attempt}-{file.name}').write_bytes(file.read_bytes())
print(json.dumps(data))
