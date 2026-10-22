#!/usr/bin/env python3
import json,subprocess,sys,time,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def main():
 assignment=json.loads((R/'private/assignment.json').read_text());roots=list(assignment['units'])+['audit-a','audit-b']
 def work(unit):
  cmd=[sys.executable,'-B',str(REPO/'validation/dispatch-forward/bootstrap.py'),'--workspace',str(R/'cache'/unit),'--java-home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home','--android-sdk','/Users/rex/Library/Android/sdk','--local-upstreams',str(R/'cache/generic-host')];row={'argv':cmd,'startedAtUnix':time.time()}
  with(R/'operators'/('setup-'+unit+'.log')).open('w')as stream:row['exitCode']=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
  row['finishedAtUnix']=time.time();(R/'operators'/('setup-'+unit+'.json')).write_text(json.dumps(row,indent=2)+'\n');assert row['exitCode']==0;print(unit,'setup complete',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(work,roots))
if __name__=='__main__':main()
