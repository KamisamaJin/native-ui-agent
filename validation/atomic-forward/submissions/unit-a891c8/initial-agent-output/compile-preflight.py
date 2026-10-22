from pathlib import Path
import json, shutil, subprocess, sys, time
w=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-a891c8')
p=sys.argv[1]
name='compile-only-'+p+'-01'
out=w/'cache'/name
args=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(w),'--platform',p,'--output',str(out)]
if p=='ios':args+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T2/public/Bridge.swift']
started=time.time()
logs=w/'agent-output'/'logs';logs.mkdir(exist_ok=True)
with (logs/(name+'.log')).open('w') as f:
    result=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,text=True,cwd=w)
record={'name':name,'argv':args,'startedAtUnix':started,'finishedAtUnix':time.time(),'returncode':result.returncode,'output':str(out),'log':str((logs/(name+'.log')).relative_to(w/'agent-output'))}
(logs/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
with (w/'agent-output'/'commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
for path in out.glob('*.log'):shutil.copy2(path,logs/(name+'-'+path.name))
for path in out.glob('*.json'):shutil.copy2(path,logs/(name+'-'+path.name))
print(json.dumps(record,indent=2))
print((logs/(name+'.log')).read_text()[-3000:])
raise SystemExit(result.returncode)
