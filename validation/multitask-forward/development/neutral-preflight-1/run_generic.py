#!/usr/bin/env python3
"""Actual neutral native pair, sealed inputs before SDK invocation."""
import concurrent.futures,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1];sys.path.insert(0,str(REPO/'native-ui-agent/scripts'));import cohort_gate as gate
DEV='/Applications/Xcode.app/Contents/Developer';JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home';SDK='/Users/rex/Library/Android/sdk'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 try:gate.authorize(R/'gates','d0-sources',R)
 except ValueError as e:save(R/'operators/early-launch-refused.json',{'recordedAtUnix':time.time(),'result':'rejected_before_sdk','reason':str(e),'nativeCommandStarted':False})
 else:raise AssertionError('Early business launch was authorized')
 registry=R/'generic/gates';registry.mkdir();save(registry/'config.json',{'version':1,'artifact_root':str(R),'stages':{'sources':{'members':['baseline-v6','candidate-v7'],'requires':[]}}})
 common=[str(p.relative_to(R))for p in(R/'generic').rglob('*')if p.is_file()and'gates'not in p.parts];neutral=R/'development/v7-neutral-candidate';tools={'baseline-v6':R/'baseline-v6','candidate-v7':neutral}
 members={key:common+[str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and '__pycache__'not in p.parts]for key,root in tools.items()};gate.seal(registry,'sources',members,R)
 devices=json.loads((R/'operators/simulators.json').read_text())['devices']
 def worker(platform):
  records=[]
  for case,order in [('N1',['baseline-v6','candidate-v7']),('N2',['candidate-v7','baseline-v6'])]:
   for tool in order:
    root=tools[tool];key=platform+'-'+case+'-'+tool;out=R/'cache/generic-runs'/key;source=R/'generic'/case;bridge=R/'generic'/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt');receipt=gate.authorize(registry,'sources',R)
    cmd=[sys.executable,'-B',str(root/'scripts'/f'{platform}_observe.py'),'run','--bridge',str(bridge),'--fixtures',str(source/'fixtures.json'),'--actions',str(source/'actions.json'),'--output',str(out)]
    if platform=='ios':cmd+=['--package',str(R/'cache/generic-host/alerttoast'),'--simulator',devices['own-a'],'--developer-dir',DEV,'--build-cache',str(R/'cache/generic-ios-build')]
    else:cmd+=['--project',str(R/'cache/generic-host/reply/Reply'),'--java-home',JAVA,'--android-sdk',SDK]
    started=time.time();log=R/'operators'/(key+'.log')
    with log.open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR=DEV,PYTHONDONTWRITEBYTECODE='1')).returncode
    record={'platform':platform,'case':case,'tool':tool,'argv':cmd,'startedAtUnix':started,'finishedAtUnix':time.time(),'exitCode':code,'authorization':receipt};save(R/'operators'/(key+'.json'),record)
    subprocess.run([sys.executable,str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(out),str(R/'generic-evidence'/key)],check=True,stdout=subprocess.DEVNULL)
    records.append(record);print(json.dumps({'run':key,'exitCode':code,'wallSeconds':record['finishedAtUnix']-started}),flush=True)
  return records
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=[row for result in pool.map(worker,['ios','android'])for row in result]
 save(R/'generic-runs.json',rows)
if __name__=='__main__':main()
