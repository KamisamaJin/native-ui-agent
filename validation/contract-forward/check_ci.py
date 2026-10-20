#!/usr/bin/env python3
"""Run the repository's Python CI commands locally and retain per-command logs."""
import argparse,json,os,shlex,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();out=a.output.resolve();assert not out.exists();out.mkdir(parents=True)
commands=[]
for line in(root/'.github/workflows/test.yml').read_text().splitlines():
 if line.startswith('      - run: '):
  cmd=shlex.split(line.split('      - run: ',1)[1])
  if cmd[:5]==['python','-m','pip','install','-r']:continue
  assert cmd[0]=='python';commands.append([sys.executable]+cmd[1:])
rows=[]
for i,cmd in enumerate(commands):
 started=time.time()
 with(out/(str(i).zfill(2)+'.log')).open('w')as stream:code=subprocess.run(cmd,cwd=root,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')).returncode
 rows.append({'argv':cmd,'exitCode':code,'startedAtUnix':started,'finishedAtUnix':time.time()});(out/'results.json').write_text(json.dumps({'root':str(root),'commands':rows,'planned':len(commands)},indent=2)+'\n');print(json.dumps({'step':i,'exitCode':code,'command':' '.join(cmd[1:])}),flush=True)
 if code:raise SystemExit(code)
print('PASS: all '+str(len(commands))+' local CI commands')
