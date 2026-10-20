import subprocess,sys,json,datetime
from pathlib import Path
workspace=Path(__file__).resolve().parent.parent
platform=sys.argv[1];number=sys.argv[2];output=workspace/'agent-output'/f'compile-{platform}-{number}'
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
attempt={'platform':platform,'attempt':int(number),'start_utc':now(),'output':str(output),'status':'running'}
record=workspace/'agent-output'/f'compile-{platform}-{number}.attempt.json';record.write_text(json.dumps(attempt,indent=2)+'\n')
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/state-forward/compile_only.py','--workspace',str(workspace),'--platform',platform,'--output',str(output)]
if platform=='ios':cmd+=['--bridge',str(workspace/'brief/Bridge.swift')]
attempt['command']=cmd
p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(workspace/'agent-output'/f'compile-{platform}-{number}.log').write_text(p.stdout)
attempt.update(end_utc=now(),exit_code=p.returncode,status='passed' if p.returncode==0 else 'failed');record.write_text(json.dumps(attempt,indent=2)+'\n');print(json.dumps(attempt));print(p.stdout[-10000:])
