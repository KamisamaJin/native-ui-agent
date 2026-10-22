import subprocess,time,json,pathlib,sys,shutil
root=pathlib.Path(__file__).resolve().parents[3]
base=root.parents[1];platform=sys.argv[1]
out=root/'agent-output/repair';destination=root/f'cache/repair-compile-{platform}-1'
argv=['python3',str(base/'compile_only.py'),'--workspace',str(root),'--platform',platform,'--output',str(destination)]
if platform=='ios':argv+=['--bridge',str(base/'design-v2/T2/public/Bridge.swift')]
record={'argv':argv,'cwd':str(root),'startedAtUnix':time.time(),'log':str(out/f'logs/compile-{platform}-1.log')}
recordpath=out/f'compile-{platform}-1-command.json';recordpath.write_text(json.dumps(record,indent=2)+'\n')
with open(record['log'],'w') as stream:p=subprocess.run(argv,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
record.update(finishedAtUnix=time.time(),exitCode=p.returncode);recordpath.write_text(json.dumps(record,indent=2)+'\n')
for name in ['build.log','record.json']:
 if (destination/name).exists():shutil.copyfile(destination/name,out/f'logs/{platform}-1-{name}')
print(json.dumps(record));print(pathlib.Path(record['log']).read_text())
