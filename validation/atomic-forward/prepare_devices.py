#!/usr/bin/env python3
"""Simulator readiness only; never launches a candidate app or captures its UI."""
import concurrent.futures,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer');config=json.loads((R/'operators/simulators.json').read_text())['devices'];t=time.time()
state=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],env=env));by={d['udid']:d for rows in state['devices'].values()for d in rows}
def run(item):
 label,udid=item;rows=[]
 commands=[]if by[udid]['state']=='Booted'else[['xcrun','simctl','boot',udid]]
 commands.append(['xcrun','simctl','bootstatus',udid,'-b'])
 for cmd in commands:
  start=time.time();p=subprocess.run(cmd,env=env,capture_output=True,text=True);rows.append({'argv':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 return{'label':label,'udid':udid,'priorState':by[udid]['state'],'commands':rows}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,config.items()))
p=R/'operators/device-readiness.json';assert not p.exists();p.write_text(json.dumps({'startedAtUnix':t,'finishedAtUnix':time.time(),'scope':'OS device readiness only, no candidate launch or capture; common infrastructure cost.','runs':rows},indent=2)+'\n');print([(r['label'],[c['exitCode']for c in r['commands']])for r in rows])
