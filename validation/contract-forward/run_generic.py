"""Timestamped, equal-input cold/warm native acquisition controls."""
import concurrent.futures,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home';SDK='/Users/rex/Library/Android/sdk'
SIM='75FE065B-819E-45C8-9B4B-7CB768FCE17E'
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def run(platform):
 results=[]
 for tool,version in [('baseline-v5','v5-cold'),('live','v6-cold'),('live','v6-warm'),('baseline-v5','v5-warm')]:
  root=REPO/'native-ui-agent'if tool=='live'else R/tool
  out=R/'cache/generic-evidence'/(platform+'-'+version)
  assert not out.exists()
  cmd=[sys.executable,str(root/'scripts'/f'{platform}_observe.py'),'run','--bridge',str(R/'generic'/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt')),'--fixtures',str(R/'generic/fixtures.json'),'--actions',str(R/'generic'/('actions.'+platform+'.json')),'--output',str(out)]
  if platform=='ios':cmd+=['--simulator',SIM,'--build-cache',str(R/'cache/ios-builds')]
  else:cmd+=['--project',str(REPO/'validation/state-forward/cache/generic-host/reply/Reply'),'--java-home',JAVA,'--android-sdk',SDK]
  row={'argv':cmd,'startedAtUTC':datetime.now(timezone.utc).isoformat(),'startedAtUnix':time.time()}
  log=R/'generic/commands'/(platform+'-'+version+'.log');log.parent.mkdir(parents=True,exist_ok=True)
  with log.open('w')as stream:row['exitCode']=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',PYTHONDONTWRITEBYTECODE='1')).returncode
  row['finishedAtUnix']=time.time();row['wallSeconds']=row['finishedAtUnix']-row['startedAtUnix'];save(log.with_suffix('.json'),row)
  subprocess.run([sys.executable,str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(out),str(R/'generic-evidence'/(platform+'-'+version))],check=True)
  print(json.dumps({'platform':platform,'version':version,'exitCode':row['exitCode'],'wallSeconds':row['wallSeconds']}),flush=True)
  results.append(row)
 return platform,results
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:results=dict(pool.map(run,['ios','android']))
 save(R/'generic-runs.json',results)
