#!/usr/bin/env python3
"""Remaining first native executions; explicit entry permit, never resampling."""
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

ORDER_SHA='cbf3a8489dfb46dc9cfc55504b6947ab75cb604311b58266efd17756dacb754f'
V2_COLLECTOR_SHA='6d8cdda538e115d01fea2116d2bc9d4397867a4bfe80536e7226d0ec5b5dd8a2'
ORIGINAL_COLLECTOR_SHA='d80522b8bb620e7b0a58a5da4a9bdb566c15a78d6cd3a69b7619023c335b7047'
AUTHORITY_SHA='d434f96e5e1edc10ff7cfac7fa273d135d27c7e8ce8590d59b8b016978cd4be1'

def need(value,message):
    if not value:raise ValueError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def ref(p):return {'path':str(p),'sha256':sha(p)}
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    p.chmod(0o444)
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def clocks():return {'at_unix':time.time(),'at_monotonic':time.monotonic(),'at_clock_gettime_monotonic':time.clock_gettime(time.CLOCK_MONOTONIC)}

def validate_plan(plan,full_order,authority):
    flattened=[(i['task'],i['scope'],p) for i in full_order if (i['task'],i['scope'])!=('T1','I') for p in i['profiles']]
    expected=[('/'.join(v),authority['scopes']['/'.join(v)]['record']) for v in flattened[11:]]
    need(len(flattened)==28 and len(expected)==17 and expected[0][0]=='T1/B/android','Exact original remaining seventeen scopes required')
    need(plan['kind']=='remaining-unexecuted-native-scopes-v3' and [(r['scope'],r['licensed_record']) for r in plan['remaining']]==expected,'Remaining schedule differs from original relative order')
    need(len({r['record'] for r in plan['remaining']})==17,'Native records must be unique')
    for n,row in enumerate(plan['remaining']):
        need(row['record']==(plan['entry_resumption_record'] if n==0 else row['licensed_record']),'Only exact preclaim entry may use an additional record')
    return plan['remaining']

def close_episode(path,start_path,outcomes,closures,status,error=None):
    start=load(start_path);now=clocks()
    value={'version':2,'status':status,'start':ref(start_path),'finished_at_unix':now['at_unix'],'finished_at_monotonic':now['at_monotonic'],
           'finished_at_clock_gettime_monotonic':now['at_clock_gettime_monotonic'],'wall_seconds':now['at_clock_gettime_monotonic']-start['started_at_clock_gettime_monotonic'],
           'outcomes':outcomes,'positive_resource_closures':closures,'quality_evaluated':False,'mapping_revealed':False}
    if error:value['error']=error
    save(path,value)

def check_halt(root):need(not (root/'operators/RESOURCE-HALT.json').exists(),'Original common halt prohibits new native UI')

def closed_initial_gate(root,monitor,rm):
    rm.monitor_gate(root,monitor,False)
    need((monitor/'CLOSED.json').is_file(),'Initial monitor must be positively CLOSED before final acquisitions')

def execute_one(root,runner,runner_sha,rm,old,row,authority,authority_sha,permit,permit_sha,episode):
    task,arm,profile=row['scope'].split('/');record=Path(row['record']);config=Path(authority['scopes'][row['scope']]['original']['original_config']['path'])
    need(not record.exists(),'Existing record must never be retried or adopted as a later sample')
    need(not rm.continuation_claim_path(root/'cache/business/independent-evaluation',task,arm,profile).exists(),'Existing native continuation claim prohibits execution')
    check_halt(root);need(sha(runner)==runner_sha,'Reviewed runner changed')
    base=[sys.executable,'-B',str(runner),'--root',str(root),'--task',task,'--arm',arm,'--profile',profile,'--config',str(config)]
    command=base+['--record',str(record),'--action','native','--continuation-authority',str(permit['base_authority']['path']),'--continuation-authority-sha256',authority_sha]
    if row['record']!=row['licensed_record']:command+=['--entry-permit',str(permit['_path']),'--entry-permit-sha256',permit_sha]
    save(episode/(profile+'-invocation.json'),{**clocks(),'argv':command,'scope':row['scope'],'licensed_record':row['licensed_record']})
    with (episode/(profile+'-launch.log')).open('x') as stream:process=subprocess.run(command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT)
    save(episode/(profile+'-process.json'),{**clocks(),'returncode':process.returncode})
    outcome_path=record/'outcome.json';outcome=load(outcome_path) if outcome_path.is_file() else {}
    env=Path(outcome.get('envelope_record',str(rm.envelope_record(record))))
    closure=next((p for p in [record/'service/resources.json',env/'error-recovery/resources.json'] if old.positive(p)),None)
    # Positive recovery comes before post-execution halt/error checks. No retry.
    if closure is None:
        cleanup=record.parent/'explicit-cleanup-v3';cleanup_command=base+['--record',str(cleanup),'--action','cleanup-native-resources']
        save(episode/(profile+'-cleanup-invocation.json'),{**clocks(),'argv':cleanup_command,'scope':'Positive owned recovery only; no UI'})
        with (episode/(profile+'-cleanup-launch.log')).open('x') as stream:recovered=subprocess.run(cleanup_command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT)
        save(episode/(profile+'-cleanup-process.json'),{**clocks(),'returncode':recovered.returncode})
        if old.positive(cleanup/'service/resources.json'):closure=cleanup/'service/resources.json'
    return outcome_path,outcome,closure

def validate_facts(rm,evidence,row,outcome_path,outcome,closure,authority):
    need(closure is not None,'No next scope without positive owned resource closure')
    need(outcome.get('source_unchanged') is True and not outcome.get('error') and not outcome.get('preservation_errors'),'Native wrapper failed; preserve current terminal and stop')
    original=authority['scopes'][row['scope']]['original'];task,arm,profile=row['scope'].split('/')
    rm.native_reference(evidence,task,arm,profile,original['original_config'],original['original_source_capsule'],outcome_path,sha(outcome_path))

def main():
    entry=clocks();p=argparse.ArgumentParser(description=__doc__)
    for key in ['root','permit','plan']:p.add_argument('--'+key,type=Path,required=True)
    for key in ['permit-sha256','plan-sha256','runner-sha256']:p.add_argument('--'+key,required=True)
    a=p.parse_args();root=a.root.resolve();evidence=root/'cache/business/independent-evaluation';control=evidence/'continuation-collection-v3'
    control.mkdir(parents=True,exist_ok=False);save(control/'ENTRY.json',{'version':3,**entry,'argv':sys.argv,'collector':ref(Path(__file__).resolve())})
    episode=start=None;outcomes={};closures={};completed=[];forwarded=0
    try:
        coord=root/'operators/cohort2/coordination';runner=coord/'independent_native_v3.py';need(sha(runner)==a.runner_sha256,'Externally pinned v3 runner differs')
        rm=module(runner,'independent_v3_collector_runner');need(sha(a.permit)==a.permit_sha256 and sha(a.plan)==a.plan_sha256,'External permit/plan pin differs')
        permit=load(a.permit);plan=load(a.plan);permit['_path']=str(a.permit)
        need(permit['operator_review_completed'] is True and permit['remaining_plan']==ref(a.plan),'Reviewed exact remaining plan required')
        authority_path=coord/'UNFORWARDED-CONTINUATION-AUTHORIZATION.json';authority,pin=rm.continuation_authority(root,authority_path,AUTHORITY_SHA)
        need(permit['base_authority']==pin==load(evidence/'NATIVE-CONTINUATION-AUTHORITY.json'),'Original authority/registry must remain unchanged')
        need(sha(coord/'collect_independent_v2.py')==V2_COLLECTOR_SHA and sha(coord/'collect_independent.py')==ORIGINAL_COLLECTOR_SHA,'Original collectors changed')
        old=module(coord/'collect_independent.py','v3_original_positive_helpers');order_path=coord/'POST-PUBLIC-ACQUISITION-ORDER.json';need(sha(order_path)==ORDER_SHA,'Original order changed')
        full_order=load(order_path)['episodes'];old.validate_order(full_order);remaining=validate_plan(plan,full_order,authority)
        for row in remaining:
            need(not Path(row['record']).exists(),'Remaining record already exists; no continuation resampling')
            need(not rm.continuation_claim_path(evidence,*row['scope'].split('/')).exists(),'Remaining scope already claimed')
        rm.entry_resume(root,authority['scopes']['T1/B/android'],Path(remaining[0]['record']),a.permit,a.permit_sha256)
        monitor=Path(authority['initial_monitor_record']);closed_initial_gate(root,monitor,rm)
        save(control/'START.json',{**clocks(),'permit':ref(a.permit),'plan':ref(a.plan),'authority':pin,'prior_failed_collection':ref(evidence/'continuation-collection/FAILED.json'),
             'initial_monitor_closed':ref(monitor/'CLOSED.json'),'scope':'Seventeen first executions only; prior thirteen actual acquisitions and all failed work/gaps retained.'})
        last=None
        for row in remaining:
            task,arm,profile=row['scope'].split('/');key=(task,arm)
            if key!=last:
                episode=evidence/'episodes'/task/arm/'remaining-first-execution-v3';start=episode/'START.json';outcomes={};closures={}
                old_episode=evidence/'episodes'/task/arm;now=clocks()
                save(start,{'version':3,'task':task,'arm':arm,'started_at_unix':now['at_unix'],'started_at_monotonic':now['at_monotonic'],
                     'started_at_clock_gettime_monotonic':now['at_clock_gettime_monotonic'],'original_start':ref(old_episode/'START.json'),
                     'original_failed_end':ref(old_episode/'END.json'),'previous_continuation_end':ref(old_episode/'continuation/END.json') if (old_episode/'continuation/END.json').exists() else None,
                     'permit':ref(a.permit),'scope':'Additional active segment; no prior failed wall or supervision/grading gap is removed.'})
                last=key
            outcome_path,outcome,closure=execute_one(root,runner,a.runner_sha256,rm,old,row,authority,AUTHORITY_SHA,permit,a.permit_sha256,episode)
            if outcome_path.is_file():outcomes[profile]=ref(outcome_path)
            if closure is not None:closures[profile]=ref(closure)
            validate_facts(rm,evidence,row,outcome_path,outcome,closure,authority);forwarded+=1
            check_halt(root)
            next_index=remaining.index(row)+1
            if next_index==len(remaining) or remaining[next_index]['scope'].split('/')[:2]!=[task,arm]:
                close_episode(episode/'END.json',start,outcomes,closures,'closed');completed.append({'task':task,'arm':arm,'end':ref(episode/'END.json')})
            progress={'version':3,'updated_at_unix':time.time(),'active':{'task':task,'arm':arm,'profile':profile,'stage':'positive_closed'},'first_UI_v3':forwarded,'prior_actual_UI':13,'episodes':completed,'quality_evaluated':False}
            target=coord/'INDEPENDENT-CONTINUATION-v3-PROGRESS.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(progress,indent=2,sort_keys=True)+'\n');os.replace(tmp,target)
            print(json.dumps(progress),flush=True)
        need(forwarded==17,'Exact seventeen remaining first executions required')
        save(control/'END.json',{'version':3,'status':'closed',**clocks(),'entry_wall_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-entry['at_clock_gettime_monotonic'],
             'episodes':completed,'first_UI_v3':forwarded,'prior_actual_UI':13,'all_original_failures_retained':True,'quality_evaluated':False,'mapping_revealed':False})
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc)}
        if episode is not None and start is not None and start.exists() and not (episode/'END.json').exists():
            try:close_episode(episode/'END.json',start,outcomes,closures,'failed',failure)
            except BaseException as terminal:failure['terminal_record_error']={'type':type(terminal).__name__,'message':str(terminal)}
        save(control/'FAILED.json',{'version':3,**clocks(),'entry_wall_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-entry['at_clock_gettime_monotonic'],
             'error':failure,'traceback':traceback.format_exc(),'current_episode':str(episode) if episode else None,'outcomes':outcomes,'closures':closures,
             'completed':completed,'first_UI_v3':forwarded,'scope':'Stop without resampling any claimed/ambiguous execution; recover owned resources before stopping.'})
        raise

if __name__=='__main__':main()
