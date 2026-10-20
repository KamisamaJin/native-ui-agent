import json,pathlib,subprocess,sys,time
workspace=pathlib.Path(__file__).resolve().parents[2]
platform=sys.argv[1]; attempt=sys.argv[2]
output=workspace/'cache'/f'compile-{platform}-{attempt}'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios': command += ['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T1/public/Bridge.swift']
record={'command':command,'startedAtUnix':time.time(),'output':str(output.relative_to(workspace))}
record_path=workspace/'agent-output'/f'compile-{platform}-{attempt}.json'
record_path.write_text(json.dumps(record,indent=2))
log=workspace/'agent-output'/'logs'/f'compile-{platform}-{attempt}.log'
with log.open('w') as f:
 p=subprocess.run(command,cwd=workspace,text=True,stdout=f,stderr=subprocess.STDOUT)
record.update({'finishedAtUnix':time.time(),'exitCode':p.returncode,'commandLog':str(log.relative_to(workspace))})
record_path.write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2));print(log.read_text()[-7000:])
