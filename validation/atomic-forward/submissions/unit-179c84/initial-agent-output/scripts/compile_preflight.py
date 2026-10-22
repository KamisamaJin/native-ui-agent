import datetime,json,pathlib,subprocess,sys,time
work=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-179c84')
platform=sys.argv[1]
attempt=sys.argv[2] if len(sys.argv)>2 else '1'
output=work/'cache'/f'compile-{platform}-{attempt}'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(work),'--platform',platform,'--output',str(output)]
if platform=='ios':command+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T3/public/Bridge.swift']
log=work/'agent-output/logs'/f'compile-{platform}-{attempt}.log'
record={'command':command,'startedAtUnix':time.time(),'startedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with log.open('w') as f:
 result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,text=True)
record.update({'finishedAtUnix':time.time(),'finishedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':result.returncode,'log':str(log.relative_to(work)),'output':str(output.relative_to(work))})
(work/'agent-output'/f'compile-{platform}-{attempt}.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
print(log.read_text()[-5000:])
raise SystemExit(result.returncode)
