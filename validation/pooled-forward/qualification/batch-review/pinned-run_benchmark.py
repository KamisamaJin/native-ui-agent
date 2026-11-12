#!/usr/bin/env python3
"""Run the sealed AB/BA order once, with one hard enclosing deadline.

Only the already-qualified public episode and gate are invoked. Failed work and
bounded positive-owned cleanup are retained; no faster pair or rerun is selected.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

R=Path(__file__).resolve().parent


def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x')as f:json.dump(v,f,indent=2)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--admission',type=Path,required=True)
    a=p.parse_args();v=load(a.admission);out=R/'operators/benchmark-run';out.mkdir(exist_ok=False)
    assert v['batch_sha256']==sha(__file__)
    assert v['order']==[['block-1','A'],['block-1','B'],['block-2','B'],['block-2','A']]
    assert v['threshold']==.20 and v['required_native_atoms']==104 and v['max_machine_seconds']==7200
    assert v['driver_sha256']==sha(R/'neutral_episode.py')and v['verifier_sha256']==sha(R/'verify_benchmark.py')
    assert v['envelope_sha256']==sha(R/'native_envelope.py')and v['prepare_neutral_sha256']==sha(R/'prepare_neutral.py')
    for rel,h in v['prerequisite_files'].items():assert sha(R/rel)==h,rel
    start=time.clock_gettime(time.CLOCK_MONOTONIC);deadline=start+7200;proc=None;failed=None;episodes=[]
    def expired(_signum,_frame):raise TimeoutError('Whole benchmark deadline reached; no new episode is allowed')
    previous=signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,7200)
    try:
        for block,arm in v['order']:
            command=[sys.executable,'-B',str(R/'neutral_episode.py'),'--block',block,'--arm',arm,
                '--candidate',v['arms']['B']['skill'],'--freeze',v['arms']['B']['freeze'],
                '--baseline',v['arms']['A']['skill'],'--baseline-freeze',v['arms']['A']['freeze']]
            at=time.clock_gettime(time.CLOCK_MONOTONIC)
            save(out/(block+'-'+arm+'-request.json'),{'argv':command,'at_unix':time.time(),'clock_start':at,'deadline':deadline})
            with(out/(block+'-'+arm+'.log')).open('x')as stream:
                proc=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                code=proc.wait()
            result=load(R/'cache/benchmark'/block/arm/'result.json')
            row={'block':block,'arm':arm,'exit_code':code,'result_sha256':sha(R/'cache/benchmark'/block/arm/'result.json'),
                 'collection_wall_seconds':result['collection_wall_seconds'],'clock_end':time.clock_gettime(time.CLOCK_MONOTONIC)}
            episodes.append(row);save(out/(block+'-'+arm+'-result.json'),row)
            print(json.dumps(row),flush=True)
            if code or result['failed']:raise RuntimeError('Failed episode retained: '+block+'/'+arm)
            profile=load(R/'cache/benchmark'/block/arm/'profiles/ADMISSION.json')
            assert set(profile['configs'])=={'ios-cold.json','ios-warm.json','android.json'},'Unexpected profile/self-hash entry'
            proc=None
    except BaseException as error:
        failed={'type':type(error).__name__,'message':str(error),'at_unix':time.time()}
        save(out/'FAILURE.json',failed)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
        if proc is not None and proc.poll()is None:
            # This is the exact child group created above; no external PID or
            # name enters the signal set. Nested managed wrappers handle TERM.
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:proc.wait(timeout=180)
            except subprocess.TimeoutExpired:
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                proc.wait(timeout=10)
        if failed:
            # Reconcile only positively owned configured episode resources;
            # retain every failure/leftover and all cleanup wall time.
            for block,arm in v['order']:
                for case in ['ios-warm','android']:
                    config=R/'cache/benchmark'/block/arm/'profiles'/(case+'.json')
                    if not config.is_file():continue
                    name=block+'-'+arm+'-'+case;skill=R/v['arms'][arm]['skill']
                    command=[sys.executable,'-B',str(skill/'scripts/ui_loop.py'),'cleanup-native-resources',
                             '--config',str(config),'--output',str(out/('failure-cleanup-'+name))]
                    at=time.clock_gettime(time.CLOCK_MONOTONIC)
                    try:
                        with(out/('failure-cleanup-'+name+'.log')).open('x')as stream:
                            result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
                        item={'argv':command,'exit_code':result.returncode,'wall_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-at}
                    except BaseException as error:item={'argv':command,'error':str(error),'wall_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-at}
                    save(out/('failure-cleanup-'+name+'.json'),item)
    save(out/'RESULT.json',{'admission_sha256':sha(a.admission),'failed':failed,'episodes':episodes,
         'enclosing_wall_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-start,
         'scope':'All failed/cleanup wall retained. Deadline includes preparation as a conservative bound; primary collection is each enclosing episode clock. No retries.'})
    if failed:return 1
    gate=[sys.executable,'-B',str(R/'verify_benchmark.py'),'gate','--admission',str(a.admission.resolve()),'--output',str(R/'qualification/benchmark-gate')]
    with(out/'gate.log').open('x')as stream:result=subprocess.run(gate,stdout=stream,stderr=subprocess.STDOUT)
    print(json.dumps({'gate_exit_code':result.returncode,'gate_result':str(R/'qualification/benchmark-gate/RESULT.json')}))
    return result.returncode


if __name__=='__main__':raise SystemExit(main())
