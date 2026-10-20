import pathlib,subprocess,json,time,sys
workspace=pathlib.Path(__file__).resolve().parent.parent
platform=sys.argv[1]
output=workspace/'cache'/('compile-'+platform+'-initial')
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios': command.extend(['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T2/public/Bridge.swift'])
started=time.time()
record={'command':command,'startedAtUnix':started,'status':'running'}
recordpath=workspace/'agent-output'/('compile-'+platform+'-record.json')
recordpath.write_text(json.dumps(record,indent=2))
with (workspace/'agent-output'/('compile-'+platform+'-driver.log')).open('w') as f:
 result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
record.update(finishedAtUnix=time.time(),exitCode=result.returncode,status='finished')
recordpath.write_text(json.dumps(record,indent=2))
for p in output.rglob('*'):
 if p.is_file() and (p.suffix=='.log' or (p.suffix=='.json' and ('record' in p.name or 'result' in p.name))):
  destination=workspace/'agent-output'/('compile-'+platform+'-'+p.name)
  destination.write_bytes(p.read_bytes())
print(json.dumps(record,indent=2))
raise SystemExit(result.returncode)
