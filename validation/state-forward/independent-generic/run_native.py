#!/usr/bin/env python3
"""Keep this evaluator's exact source copy, command, wall time and output durable."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys, time

p = argparse.ArgumentParser()
p.add_argument('platform', choices=['ios','android'])
p.add_argument('phase', choices=['probe','component'])
a = p.parse_args()
root = Path(__file__).resolve().parent
repo = root.parents[2]
cache = repo/'validation/state-forward/cache/independent-generic'
skill = repo/'native-ui-agent'
copy = cache/f'skill-{a.platform}-{a.phase}'
out = root/f'{a.platform}-{a.phase}'
if copy.exists() or out.exists():
    raise SystemExit('Fresh paths required; this script never retries a native run.')
def dig(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(base):
    return {str(p.relative_to(base)):dig(p) for p in sorted(base.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
before = hashes(skill)
shutil.copytree(skill, copy, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
after = hashes(copy)
if before != after or before != hashes(skill):
    raise SystemExit('Skill changed during copy; no native command executed.')
name = 'probe-' if a.phase == 'probe' else ''
plan = root/('probe-plan' if a.phase == 'probe' else 'component-plan')
if not plan.exists():
    subprocess.run([sys.executable,str(copy/'scripts/state_plan.py'),'--matrix',str(root/f'{name}matrix.json'),
                    '--actions',str(root/f'{name}actions.original.json'),'--output',str(plan)],check=True)
bridge = root/('ProbeBridge' if a.phase == 'probe' else 'ReadingBridge')
cmd = [sys.executable,str(copy/f'scripts/{a.platform}_observe.py'),'run',
       '--bridge',str(bridge.with_suffix('.swift' if a.platform == 'ios' else '.kt')),
       '--fixtures',str(root/f'{name}{a.platform}-fixtures.json'),
       '--actions',str(plan/'actions.json'),'--output',str(out)]
if a.platform == 'ios':
    cmd += ['--simulator','D1F80E14-0DB7-4EE9-8018-35D3071BEF1D',
            '--developer-dir','/Applications/Xcode.app/Contents/Developer',
            '--build-cache',str(cache/'ios-build-cache')]
else:
    cmd += ['--project',str(cache/'host/reply/Reply'),
            '--java-home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home',
            '--android-sdk','/Users/rex/Library/Android/sdk']
record = {'platform':a.platform,'phase':a.phase,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'command':cmd,'cwd':str(repo),'skill_copy':str(copy),'skill_sha256':after,
          'input_sha256':{str(x.relative_to(root)):dig(x) for x in
           [bridge.with_suffix('.swift' if a.platform == 'ios' else '.kt'),root/f'{name}{a.platform}-fixtures.json',plan/'plan.json',plan/'actions.json']}}
meta=root/f'{a.platform}-{a.phase}-invocation.json'
meta.write_text(json.dumps(record,indent=2)+'\n')
started=time.monotonic()
result=subprocess.run(cmd,cwd=repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                      env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer'))
record.update(exit_code=result.returncode,wall_seconds=time.monotonic()-started,
              finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
meta.write_text(json.dumps(record,indent=2)+'\n')
(root/f'{a.platform}-{a.phase}-stdout.log').write_text(result.stdout)
print(json.dumps({'platform':a.platform,'phase':a.phase,'exit_code':result.returncode,
                  'wall_seconds':record['wall_seconds'],'output':str(out),'stdout':result.stdout}),flush=True)
raise SystemExit(result.returncode)
