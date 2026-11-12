#!/usr/bin/env python3
"""Explicit finite continuations of exactly proven zero-inner-UI operations."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

OLD_COLLECTOR_SHA='d80522b8bb620e7b0a58a5da4a9bdb566c15a78d6cd3a69b7619023c335b7047'
ORDER_SHA='cbf3a8489dfb46dc9cfc55504b6947ab75cb604311b58266efd17756dacb754f'
INITIAL_SHA='178b49172cee5c10f9101650e2adfe1c193b54c0720884fa8e4e587f37a10c79'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def ref(p):return {'path':str(p),'sha256':sha(p)}
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    p.chmod(0o444)
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def need(value,message):
    if not value:raise ValueError(message)


def progress(root,task,arm,profile,stage,completed,forwarded):
    p=root/'operators/cohort2/coordination/INDEPENDENT-CONTINUATION-PROGRESS.json'
    value={'version':1,'updated_at_unix':time.time(),'active':{'task':task,'arm':arm,'profile':profile,'stage':stage},
           'closed_continuation_episodes':completed,'continued_first_UI_operations':forwarded,
           'prior_valid_first_UI_operations':2,'scope':'Derived only; original28 failures retained, no UI resampling or quality acceptance.'}
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)
    print(json.dumps({'task':task,'arm':arm,'profile':profile,'stage':stage,'continued_first_UI_operations':forwarded}),flush=True)


def main():
    entry_unix,entry_clock=time.time(),time.monotonic()
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['root','authority','monitor']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--authority-sha256',required=True);p.add_argument('--runner-sha256',required=True);a=p.parse_args()
    root=a.root.resolve();evidence=root/'cache/business/independent-evaluation';control=evidence/'continuation-collection'
    control.mkdir(parents=True,exist_ok=False)
    save(control/'ENTRY.json',{'version':1,'started_at_unix':entry_unix,'started_at_monotonic':entry_clock,'argv':sys.argv,'collector':ref(Path(__file__).resolve())})
    episode=start_path=None;outcomes={};closures={};completed=[];forwarded=0;monitor_closed=False;failure=None
    try:
        coord=root/'operators/cohort2/coordination';runner=coord/'independent_native_v2.py'
        need(sha(runner)==a.runner_sha256,'Externally pinned v2 runner differs')
        runner_module=module(runner,'explicit_zero_forward_runner_v2')
        authority,authority_pin=runner_module.continuation_authority(root,a.authority,a.authority_sha256)
        need(a.monitor.resolve()==Path(authority['initial_monitor_record']),'Exact new supplemental monitor window required')
        need((a.monitor/'READY.json').is_file() and not (a.monitor/'CLOSED.json').exists(),'Live new complete-union READY required')
        old_collector=coord/'collect_independent.py';need(sha(old_collector)==OLD_COLLECTOR_SHA,'Original collector changed')
        old=module(old_collector,'original_closed_collector_helpers')
        order_path=coord/'POST-PUBLIC-ACQUISITION-ORDER.json';need(sha(order_path)==ORDER_SHA,'Original finite schedule changed')
        full_order=load(order_path)['episodes'];old.validate_order(full_order)
        order=[item for item in full_order if (item['task'],item['scope'])!=('T1','I')]
        need(len(order)==14 and {runner_module.continuation_scope(i['task'],i['scope'],p) for i in order for p in i['profiles']}==set(authority['scopes']),'Exact28 licensed scopes in original relative order required')
        initial=root/'cache/business/initial-reference/PREPARATION-SEAL.json';need(sha(initial)==INITIAL_SHA,'Original initial preparation changed')
        save(control/'START.json',{'version':1,'at_unix':time.time(),'authority':authority_pin,'runner':ref(runner),'original_collector':ref(old_collector),
             'old_collection_end':ref(evidence/'collection-operations/END.json'),'original_order':ref(order_path),'new_monitor_ready':ref(a.monitor/'READY.json'),
             'scope':'Explicit append-only common operator continuation of unexecuted inner commands only; acquired I1 excluded, all original files/costs retained.'})
        for item in order:
            task,arm=item['task'],item['scope'];episode=evidence/'episodes'/task/arm/'continuation';start_path=episode/'START.json'
            outcomes={};closures={};old_episode=evidence/'episodes'/task/arm
            save(start_path,{'version':1,'kind':'explicit-zero-forward-continuation-episode-start','task':task,'arm':arm,
                 'started_at_unix':time.time(),'started_at_monotonic':time.monotonic(),'original_start':ref(old_episode/'START.json'),
                 'original_resource_closed_end':ref(old_episode/'END.json'),'authority':authority_pin,
                 'inter_episode_wait_seconds':time.monotonic()-load(old_episode/'END.json')['finished_at_monotonic'],
                 'scope':'Separate active continuation episode; original failed wall plus common repair/research gap remain reported, never removed or credited to a treatment.'})
            if arm!='I':need(monitor_closed,'All supplemental reference resources must positively close before final hidden UI')
            for profile in item['profiles']:
                need(not (root/'operators/RESOURCE-HALT.json').exists(),'Original common halt prohibits new UI')
                need(sha(runner)==a.runner_sha256 and sha(a.authority)==a.authority_sha256,'Continuation code/authority changed')
                row=authority['scopes'][runner_module.continuation_scope(task,arm,profile)]
                record=Path(row['record']);need(not record.exists(),'No continuation retry or later-record adoption')
                config=Path(row['original']['original_config']['path'])
                base=[sys.executable,'-B',str(runner),'--root',str(root),'--task',task,'--arm',arm,'--profile',profile,'--config',str(config)]
                command=base+['--record',str(record),'--action','native','--continuation-authority',str(a.authority),'--continuation-authority-sha256',a.authority_sha256]
                if arm=='I':command+=['--initial-monitor',str(a.monitor),'--initial-seal',str(initial),'--initial-seal-sha256',INITIAL_SHA]
                save(episode/(profile+'-invocation.json'),{'at_unix':time.time(),'argv':command,'original_unforwarded_outcome':row['original']['original_outcome']})
                progress(root,task,arm,profile,'first-inner-native-continuation',completed,forwarded)
                with (episode/(profile+'-launch.log')).open('x') as stream:result=subprocess.run(command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT)
                save(episode/(profile+'-process.json'),{'at_unix':time.time(),'returncode':result.returncode})
                outcome_path=record/'outcome.json';outcome=load(outcome_path) if outcome_path.is_file() else {}
                if outcome_path.is_file():outcomes[profile]=ref(outcome_path)
                env=Path(outcome.get('envelope_record',str(runner_module.envelope_record(record))))
                closure=next((p for p in [record/'service/resources.json',env/'error-recovery/resources.json'] if old.positive(p)),None)
                if closure is None:
                    cleanup=record.parent/'explicit-cleanup';cleanup_command=base+['--record',str(cleanup),'--action','cleanup-native-resources']
                    if arm=='I':cleanup_command+=['--initial-monitor',str(a.monitor),'--initial-seal',str(initial),'--initial-seal-sha256',INITIAL_SHA]
                    save(episode/(profile+'-cleanup-invocation.json'),{'at_unix':time.time(),'argv':cleanup_command,'reason':'Explicit positive-owned recovery only; never a second UI command.'})
                    with (episode/(profile+'-cleanup-launch.log')).open('x') as stream:recovered=subprocess.run(cleanup_command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT)
                    save(episode/(profile+'-cleanup-process.json'),{'returncode':recovered.returncode,'at_unix':time.time()})
                    if old.positive(cleanup/'service/resources.json'):closure=cleanup/'service/resources.json'
                need(closure is not None,'No next operation without positive owned closure')
                closures[profile]=ref(closure)
                need(outcome.get('source_unchanged') is True,'Source validation failed; resources closed, no next UI')
                need(outcome.get('new_ui_acquisition') is True and not outcome.get('capture_reused') and outcome.get('capture') and outcome.get('cycle'),
                     'No fresh original facts; stop at this explicit continuation, never cascade or retry')
                need(not outcome.get('error') and not outcome.get('preservation_errors'),'Continuation wrapper failed; stop with original facts retained')
                capture=Path(outcome['capture']['path']);need(sha(capture)==outcome['capture']['sha256'],'Original continuation capture changed')
                forwarded+=1
                need(not (root/'operators/RESOURCE-HALT.json').exists(),'Original common halt after positive resource closure; no next UI')
            old.close_episode(episode/'END.json',start_path,outcomes,closures,status='closed')
            completed.append({'task':task,'arm':arm,'end':ref(episode/'END.json')})
            progress(root,task,arm,None,'continuation-episode-closed-quality-pending',completed,forwarded)
            if task=='T5' and arm=='I':
                command=[sys.executable,'-B',str(root/'initial-reference-monitor/monitor.py'),'--record',str(a.monitor),'--preflight']
                with (control/'monitor-before-stop-preflight.log').open('x') as stream:check=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
                save(control/'monitor-before-stop-preflight.json',{'argv':command,'returncode':check.returncode})
                need(check.returncode==0,'Positive original/new zero slots before monitor STOP required')
                save(a.monitor/'STOP',{'at_unix':time.time(),'reason':'Only remaining I2-I5 first native commands finished; all supplemental resources positive closed.'})
                deadline=time.monotonic()+120
                while not (a.monitor/'CLOSED.json').exists() and time.monotonic()<deadline:time.sleep(0.25)
                closed=load(a.monitor/'CLOSED.json');need(closed.get('status')=='closed' and closed.get('positive_idle',{}).get('all_clear') is True,'Continuation monitor failed positive close')
                save(control/'INITIAL-MONITOR-CLOSURE.json',{'closed':ref(a.monitor/'CLOSED.json'),'original_v2_meter_continues':True})
                monitor_closed=True
        need(forwarded==28,'Every licensed unexecuted scope must have one first actual acquisition')
        save(control/'END.json',{'version':1,'status':'closed','finished_at_unix':time.time(),'entry_wall_seconds':time.monotonic()-entry_clock,
             'authority':authority_pin,'episodes':completed,'first_inner_UI_continuations':forwarded,'prior_valid_I1_acquisitions':2,
             'all_original28_failures_retained':True,'quality_evaluated':False,'mapping_revealed':False})
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc)}
        if episode is not None and start_path is not None and start_path.exists() and not (episode/'END.json').exists():
            try:
                old.close_episode(episode/'END.json',start_path,outcomes,closures,status='failed',error=failure)
            except BaseException as terminal:failure['terminal_record_error']={'type':type(terminal).__name__,'message':str(terminal)}
        save(control/'FAILED.json',{'version':1,'at_unix':time.time(),'error':failure,'traceback':traceback.format_exc(),
             'entry_wall_seconds':time.monotonic()-entry_clock,'current_episode':str(episode) if episode else None,'outcomes':outcomes,'closures':closures,
             'completed_episodes':completed,'first_UI_continuations':forwarded,'monitor_positive_closed':monitor_closed,
             'scope':'Stop on any new wrapper failure; no native resampling or automatic correction/retry.'})
        raise


if __name__=='__main__':main()
