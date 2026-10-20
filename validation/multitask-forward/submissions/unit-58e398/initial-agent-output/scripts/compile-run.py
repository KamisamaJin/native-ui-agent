import argparse,json,subprocess,time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('platform',choices=['ios','android']);args=parser.parse_args()
workspace=Path(__file__).resolve().parents[2]
output=workspace/'cache'/f'{args.platform}-compile-01'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(workspace),'--platform',args.platform,'--output',str(output)]
if args.platform=='ios':command+=['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T1/public/Bridge.swift']
record={'command':command,'startedAtUnix':time.time()}
(workspace/'agent-output'/f'compile-{args.platform}-running.json').write_text(json.dumps(record,indent=2)+'\n')
result=subprocess.run(command,capture_output=True,text=True)
log=workspace/'agent-output'/'logs'/f'compile-{args.platform}-01.log';log.write_text(result.stdout+result.stderr)
record.update(finishedAtUnix=time.time(),exitCode=result.returncode,log=str(log.relative_to(workspace)))
(workspace/'agent-output'/f'compile-{args.platform}-01.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
print(result.stdout[-3000:]); print(result.stderr[-3000:])
raise SystemExit(result.returncode)
