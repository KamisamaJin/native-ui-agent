from pathlib import Path
import subprocess,json,time,sys
w=Path(__file__).resolve().parents[2]
platform=sys.argv[1];attempt=sys.argv[2]
out=w/'cache'/f'compile-{platform}-{attempt}'
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(w),'--platform',platform,'--output',str(out)]
if platform=='ios':cmd+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public/Bridge.swift']
start=time.time()
r=subprocess.run(cmd,text=True,capture_output=True)
log=w/'agent-output'/'logs'/f'compile-{platform}-{attempt}.log'
log.write_text(r.stdout+r.stderr)
rec={'command':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':r.returncode,'log':str(log.relative_to(w)),'cacheOutput':str(out.relative_to(w))}
(w/'agent-output'/f'compile-{platform}-{attempt}-command.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps(rec));print(r.stdout);print(r.stderr)
