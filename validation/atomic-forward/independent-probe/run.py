#!/usr/bin/env python3
import subprocess,sys,time,json,datetime,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
cmd=sys.argv[1:]
if not cmd:raise SystemExit('command required')
start=time.time();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();ident=f'{time.time_ns()}'
log=R/'logs'/f'{ident}.log';log.parent.mkdir(exist_ok=True)
with log.open('w')as out:
 p=subprocess.Popen(cmd,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
 for line in p.stdout:out.write(line);out.flush();print(line,end='',flush=True)
 code=p.wait()
record={'started_utc':stamp,'duration_seconds':time.time()-start,'argv':cmd,'cwd':str(R),'exit_code':code,'log':str(log.relative_to(R)),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
with(R/'commands.jsonl').open('a')as f:f.write(json.dumps(record)+'\n')
print(json.dumps(record),flush=True);sys.exit(code)
