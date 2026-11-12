#!/usr/bin/env python3
"""Real owned-device/SDK interruption control; no component or performance claim."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

R=Path(__file__).resolve().parent


def load(p):return json.loads(Path(p).read_text())
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x')as f:json.dump(v,f,indent=2)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['skill','config','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--child',choices=['after-create','during-sdk']);p.add_argument('--nonce')
    a=p.parse_args();sys.path.insert(0,str(a.skill.resolve()/'scripts'))
    from resource_manager import Resources
    c=load(a.config);out=a.output.resolve();env=dict(os.environ,DEVELOPER_DIR=c['native_options']['developer-dir'])
    if c['resources']['root']!=str(R/'cache/qualification/resources/ios'):
        raise ValueError('Only the predeclared, positively owned qualification resource root is admitted')
    if a.child:
        with Resources(c,out/'owner-resources')as owner:
            device=owner.native_options(platform='ios')['simulator']
            save(out/'owned-ready.json',{'nonce':a.nonce,'pid':os.getpid(),'device':device,'resource_identity':owner.identity,'phase':a.child})
            if a.child=='after-create':
                # Finite pause exposes a durable create/active lease, not a fake
                # SDK command. The parent kills only this exact Popen owner PID.
                time.sleep(30)
            else:
                owner.simctl('boot',device)
                with(out/'bootstatus.log').open('x')as stream:
                    code=owner.run(['xcrun','simctl','bootstatus',device,'-b'],env=env,stdout=stream,timeout=60)
                save(out/'sdk-finished.json',{'code':code})
                time.sleep(20)
        return 0
    out.mkdir(parents=True,exist_ok=False)
    save(out/'ADMISSION.json',{'at_unix':time.time(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'skill':str(a.skill.resolve()),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),
        'phases':['after-create','during-sdk'],'scope':'HOST SIGKILL plus actual native-owned create/inventory/SDK bootstatus/reconciliation/delete. Zero component UI tests, business defects or speed credit.'})
    checks=[]
    def members(pgid):
        result=subprocess.run(['ps','-ax','-o','pid=,ppid=,pgid=,comm='],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        rows=[]
        for line in result.stdout.splitlines():
            fields=line.strip().split(None,3)
            if len(fields)==4 and fields[2]==str(pgid):rows.append({'pid':int(fields[0]),'ppid':int(fields[1]),'pgid':int(fields[2]),'executable':fields[3]})
        return rows
    def inventory(device):
        result=subprocess.run(['xcrun','simctl','list','devices','--json'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
        raw=json.loads(result.stdout)
        return {'argv':['xcrun','simctl','list','devices','--json'],'exit_code':result.returncode,
                'target_rows':[v for rows in raw['devices'].values()for v in rows if v['udid']==device],
                'raw_stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),
                'device_data_exists':(Path.home()/'Library/Developer/CoreSimulator/Devices'/device).exists()}
    for phase in ['after-create','during-sdk']:
        current=out/phase;current.mkdir();nonce=uuid.uuid4().hex;proc=None;ready=None;group=None;observed=[]
        argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--skill',str(a.skill.resolve()),'--config',str(a.config.resolve()),
              '--output',str(current),'--child',phase,'--nonce',nonce]
        try:
            with(current/'owner.log').open('x')as stream:
                proc=subprocess.Popen(argv,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                deadline=time.clock_gettime(time.CLOCK_MONOTONIC)+40
                while time.clock_gettime(time.CLOCK_MONOTONIC)<deadline:
                    if(current/'owned-ready.json').is_file():
                        ready=load(current/'owned-ready.json')
                        assert ready['pid']==proc.pid and ready['nonce']==nonce and ready['phase']==phase
                        if phase=='after-create':break
                        journal=load(Path(c['resources']['root'])/'journal.json');group=journal.get('process')
                        if group and group['argv']==['xcrun','simctl','bootstatus',ready['device'],'-b']:
                            observed=members(group['pgid'])
                            if any(Path(v['executable']).name=='simctl'for v in observed):break
                    if proc.poll()is not None:raise RuntimeError('Owner exited before interruption boundary')
                    time.sleep(.05)
                else:raise RuntimeError('Real native interruption boundary was not observed')
                if phase=='during-sdk':
                    assert observed and not(current/'sdk-finished.json').exists()
                    actual=Resources.process_identity(group['pid'])
                    assert Resources.same_process(group['identity'],actual,group['token'],group['pid'])
                    # Freeze only the positively acquired SDK group so this
                    # control cannot accidentally kill an already idle owner.
                    os.killpg(group['pgid'],signal.SIGSTOP)
                before=inventory(ready['device']);assert len(before['target_rows'])==1
                save(current/'BEFORE-KILL.json',{'argv':argv,'ready':ready,'process':group,'actual_group_members':observed,'inventory':before})
                proc.kill();code=proc.wait(timeout=5);assert code==-signal.SIGKILL
            # The same public resource implementation must reconcile its exact
            # journaled process/device. No UUID/PID from an external user list is
            # ever placed in a deletion or kill set by this controller.
            reentry_deadline=time.clock_gettime(time.CLOCK_MONOTONIC)+30;waits=0
            while True:
                try:
                    with Resources(c,current/'recovery',final=True)as recovered:
                        recovered.simctl('list','devices','--json')
                    break
                except RuntimeError as error:
                    if str(error)!='Resource lease is active; concurrent acquisition refused'or time.clock_gettime(time.CLOCK_MONOTONIC)>=reentry_deadline:raise
                    waits+=1;time.sleep(.1)
            after=inventory(ready['device']);receipt=load(current/'recovery/resources.json')
            group_after=members(group['pgid'])if group else[]
            passed=not(after['target_rows']or after['device_data_exists']or receipt['remaining_devices']or receipt['remaining_directories']or receipt['cleanup_errors']or group_after)
            item={'phase':phase,'passed':passed,'owner_exit':code,'after':after,'group_after':group_after,
                  'bounded_reentry_lease_waits':waits,
                  'recovery_resources_sha256':hashlib.sha256((current/'recovery/resources.json').read_bytes()).hexdigest()}
            save(current/'RESULT.json',item);checks.append(item)
            if not passed:raise RuntimeError('Interrupted owned resource retirement not demonstrated')
        finally:
            if proc is not None and proc.poll()is None:proc.kill();proc.wait(timeout=5)
            if group:
                actual=Resources.process_identity(group['pid'])
                if Resources.same_process(group['identity'],actual,group['token'],group['pid']):
                    try:os.killpg(group['pgid'],signal.SIGCONT)
                    except ProcessLookupError:pass
    save(out/'RESULT.json',{'passed':all(v['passed']for v in checks),'checks':checks,'native_ui_tests':0,'performance_samples':0,'business_tasks':0})
    print(json.dumps({'passed':all(v['passed']for v in checks),'controls':len(checks)}))
    return 0


if __name__=='__main__':raise SystemExit(main())
