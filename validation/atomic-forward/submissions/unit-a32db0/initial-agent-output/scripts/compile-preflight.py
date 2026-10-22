import subprocess,time,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[2]
platform=sys.argv[1]
attempt=sys.argv[2] if len(sys.argv)>2 else '1'
argv=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(root),'--platform',platform,'--output',str(root/f'cache/compile-{platform}-{attempt}')]
if platform=='ios': argv+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T2/public/Bridge.swift']
start=time.time()
log=root/f'agent-output/logs/compile-{platform}-{attempt}.log'
record={'argv':argv,'cwd':str(root),'startedAtUnix':start,'log':str(log.relative_to(root))}
path=root/f'agent-output/compile-{platform}-{attempt}-command.json'
path.write_text(json.dumps(record,indent=2)+'\n')
with log.open('w') as stream: p=subprocess.run(argv,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
record.update(finishedAtUnix=time.time(),returncode=p.returncode)
path.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));print(log.read_text())
