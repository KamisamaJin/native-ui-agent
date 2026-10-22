#!/usr/bin/env python3
import concurrent.futures,json,os,subprocess,sys,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 seal=json.loads((R/'operators/root-neutral-input-seal.json').read_text());devices=json.loads((R/'operators/simulators.json').read_text())['devices'];tool=R/'development/native-v8-attempt1'
 def run(pl):
  rows=[]
  for case in ['N1','N2']:
   for rel,h in seal['files'].items():assert sha(R/rel)==h
   out=R/'cache/neutral-captures'/pl/case
   cmd=[sys.executable,'-B',str(tool/'scripts'/f'{pl}_observe.py'),'run','--bridge',str(R/'neutral'/('Bridge.swift'if pl=='ios'else'ObserverBridge.kt')),'--fixtures',str(R/'neutral'/case/'fixtures.json'),'--actions',str(R/'neutral'/case/'actions.json'),'--output',str(out)]
   if pl=='ios':cmd+=['--package',str(R/'cache/generic-host/alerttoast'),'--simulator',devices['own-a'],'--developer-dir','/Applications/Xcode.app/Contents/Developer','--build-cache',str(R/'cache/neutral-ios-build')]
   else:cmd+=['--project',str(R/'cache/generic-host/reply/Reply'),'--java-home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home','--android-sdk','/Users/rex/Library/Android/sdk']
   record={'argv':cmd,'platform':pl,'case':case,'startedAtUnix':time.time(),'sealedInputsSHA256':sha(R/'operators/root-neutral-input-seal.json')}
   with(R/'operators'/f'neutral-{pl}-{case}.log').open('w')as stream:record['exitCode']=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',PYTHONDONTWRITEBYTECODE='1')).returncode
   record['finishedAtUnix']=time.time();save(R/'operators'/f'neutral-{pl}-{case}.json',record)
   if out.exists():
    archive=R/'neutral-evidence'/pl/case;subprocess.run([sys.executable,'-B',str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(out),str(archive)],stdout=subprocess.DEVNULL,check=True)
   rows.append(record);print(pl,case,record['exitCode'],flush=True)
  return rows
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=[v for rr in pool.map(run,['ios','android'])for v in rr]
 save(R/'operators/root-neutral-runs.json',{'finishedAtUnix':time.time(),'runs':rows})
if __name__=='__main__':main()
