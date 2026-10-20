#!/usr/bin/env python3
"""Prospective source capsules and timestamped native collection, no business rules."""
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
REPO=R.parents[1]
JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home'
SDK='/Users/rex/Library/Android/sdk'
DEV='/Applications/Xcode.app/Contents/Developer'
ROOTS=['alerttoast/Sources','reply/Reply/app/src/main']
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def fingerprint(w):return {str(p.relative_to(w)):sha(p)for rel in ROOTS for p in sorted((w/rel).rglob('*'))if p.is_file()}
def capsule(w,out):
 assert not out.exists();out.mkdir(parents=True)
 files=fingerprint(w)
 for rel in files:
  dst=out/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/rel,dst)
 licenses={}
 for repo in ['reply','alerttoast']:
  for name in ['LICENSE','LICENSE.md','LICENSE.txt','NOTICE']:
   path=w/repo/name
   if path.is_file():
    target=out/'licenses'/(repo+'-'+name);target.parent.mkdir(exist_ok=True);shutil.copy2(path,target);licenses[str(target.relative_to(out))]=sha(target)
 save(out/'seal.json',{'sealedAtUTC':utc(),'sealedAtUnix':time.time(),'files':files,'upstreamLicenses':licenses})
def restore(capsule,w):
 assert w.resolve().is_relative_to((R/'cache').resolve()),'Restore only an experiment-owned derived checkout'
 seal=read(capsule/'seal.json')
 for rel,h in seal['files'].items():assert sha(capsule/'source'/rel)==h
 for rel in ROOTS:
  target=w/rel
  if target.exists():shutil.rmtree(target)
 for rel in seal['files']:
  dst=w/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(capsule/'source'/rel,dst)
 assert fingerprint(w)==seal['files']
def argv(tool,w,platform,bridge,case,sim,out):
 actions=case/('actions.'+platform+'.json')
 if not actions.is_file():actions=case/'actions.json'
 cmd=[sys.executable,str(R/tool/'scripts'/f'{platform}_observe.py'),'run','--bridge',str(bridge.resolve()),
      '--fixtures',str((case/'fixtures.json').resolve()),'--actions',str(actions.resolve()),'--output',str(out.resolve())]
 if platform=='ios':cmd+=['--package',str((w/'alerttoast').resolve()),'--simulator',sim,'--developer-dir',DEV,'--build-cache',str((w/'ios-build-cache').resolve())]
 else:cmd+=['--project',str((w/'reply/Reply').resolve()),'--java-home',JAVA,'--android-sdk',SDK]
 return cmd
def collect(a):
 w=a.workspace.resolve();out=a.output.resolve();assert not out.exists();out.mkdir(parents=True)
 original=fingerprint(w);started=time.time()
 # Witness the operator before spawning native processes. Old own-D0 runs retain
 # their explicitly retrospective operator snapshot rather than a backdated one.
 operator=out/'operator-source.py';shutil.copy2(Path(__file__).resolve(),operator)
 save(out/'started.json',{'startedAtUTC':utc(),'startedAtUnix':started,'source':original,'tool':a.tool,'phase':a.phase,'operatorSHA256':sha(operator)})
 def platform_run(platform):
  dest=out/platform;dest.mkdir();rows=[]
  bridge=a.bridges/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt')
  for case in sorted(p for p in a.inputs.iterdir()if p.is_dir() and(p/'fixtures.json').is_file()):
   cmd=argv(a.tool,w,platform,bridge,case,a.simulator,dest/case.name)
   actual_actions=case/('actions.'+platform+'.json')
   if not actual_actions.is_file():actual_actions=case/'actions.json'
   row={'case':case.name,'argv':cmd,'startedAtUTC':utc(),'startedAtUnix':time.time(),'inputHashes':{'fixtures.json':sha(case/'fixtures.json'),actual_actions.name:sha(actual_actions)}}
   save(dest/(case.name+'-command.json'),row)
   with(dest/(case.name+'-wrapper.log')).open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR=DEV,PYTHONDONTWRITEBYTECODE='1')).returncode
   row.update(exitCode=code,finishedAtUTC=utc(),finishedAtUnix=time.time());row['wallSeconds']=row['finishedAtUnix']-row['startedAtUnix'];save(dest/(case.name+'-command.json'),row);rows.append(row)
   assert fingerprint(w)==original,'Source changed during native collection'
   print(json.dumps({'platform':platform,'case':case.name,'exitCode':code,'wallSeconds':row['wallSeconds']}),flush=True)
  save(dest/'corpus.json',{'phase':a.phase,'platform':platform,'source':original,'tool':a.tool,'runs':rows,'finishedAtUTC':utc(),'finishedAtUnix':time.time()})
  return platform,rows
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  results=dict(pool.map(platform_run,['ios','android']))
 save(out/'corpus.json',{'phase':a.phase,'source':original,'tool':a.tool,'startedAtUnix':started,'finishedAtUnix':time.time(),'finishedAtUTC':utc(),'platformRuns':results,'slots':{'ios':1,'android':1}})
 if a.archive:
  assert not a.archive.exists()
  subprocess.run([sys.executable,str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(out),str(a.archive)],check=True)
  save(a.archive/'corpus-seal.json',{'sealedAtUTC':utc(),'sealedAtUnix':time.time(),'producerFinishedAtUnix':read(out/'corpus.json')['finishedAtUnix'],'source':original,'portableManifestSHA256':sha(a.archive/'portable-sha256.json')})
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 s=sub.add_parser('capsule');s.add_argument('workspace',type=Path);s.add_argument('output',type=Path)
 s=sub.add_parser('restore');s.add_argument('capsule',type=Path);s.add_argument('workspace',type=Path)
 s=sub.add_parser('collect');s.add_argument('--workspace',type=Path,required=True);s.add_argument('--tool',choices=['baseline-v5','candidate-v6'],required=True);s.add_argument('--inputs',type=Path,required=True);s.add_argument('--bridges',type=Path,required=True);s.add_argument('--simulator',required=True);s.add_argument('--output',type=Path,required=True);s.add_argument('--archive',type=Path);s.add_argument('--phase',required=True)
 a=p.parse_args()
 if a.command=='capsule':capsule(a.workspace.resolve(),a.output.resolve())
 elif a.command=='restore':restore(a.capsule.resolve(),a.workspace.resolve())
 else:collect(a)
if __name__=='__main__':main()
