#!/usr/bin/env python3
"""Small synthetic operator controls, no real RUN/SDK/source inputs."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

BASE=Path(__file__).resolve().parent;COORD=BASE.parent
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rm=module(COORD/'independent_native_v3.py','tested_v3_runner')
cm=module(COORD/'collect_independent_v3.py','tested_v3_collector')
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True)+'\n')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
helper=SimpleNamespace(digest=digest,domain=SimpleNamespace(platform=lambda c:c['platform']))
def rejected(fn):
    try:fn()
    except (ValueError,FileNotFoundError,KeyError):return
    raise AssertionError('Invalid metadata was accepted')

def context_fixture(p):
    root=p/'root';e=root/'cache/business/independent-evaluation';wf=root/'workflow';wf.mkdir(parents=True)
    config={'review_store':str(root/'reviews/android'),'source_review_store':str(root/'sources/android'),'workflow':{'root':str(wf)},'source_roots':[str(root/'production')],'platform':'android'}
    sibling=copy.deepcopy(config);sibling.update(platform='ios',review_store=str(root/'reviews/ios'),source_review_store=str(root/'sources/ios'))
    cp=root/'ios-config.json';put(cp,sibling);caps={'path':str(root/'capsule.json'),'sha256':'source'}
    native_dir=e/'continuations/T1/B/ios/native';service=native_dir/'service';context={'native':'same original context'};put(service/'workflow-context.json',context)
    cycle={'path':str(service/'cycle.json'),'sha256':'cycle'};capture={'path':str(service/'capture.json'),'sha256':'capture'}
    owner=digest(config['source_roots']);snap={'owner':owner,'platform':'ios','generation':0,'cycles':[{'cycle':cycle,'context_sha256':digest(context)}],
        'capture':{'cycle':cycle,'context_sha256':digest(context),'capture':capture,'context':rm.ref(service/'workflow-context.json')},'task':None}
    put(service/'workflow-state.json',snap)
    inventory={str(service/n):{'sha256':rm.sha(service/n),'bytes':(service/n).stat().st_size} for n in ['workflow-state.json','workflow-context.json']}
    put(native_dir/'original-inventory.json',inventory)
    native={'config':rm.ref(cp),'source_capsule':caps,'service_output':str(service),'inventory':rm.ref(native_dir/'original-inventory.json'),'cycle':cycle,'capture':capture}
    put(native_dir/'outcome.json',native);put(rm.continuation_claim_path(e,'T1','B','ios'),{'record':str(native_dir)})
    put(wf/'owner.json',{'format':'native-ui-workflow-v1','owner':owner,'root_identity':{'device':wf.stat().st_dev,'inode':wf.stat().st_ino}})
    final=copy.deepcopy(snap);final['generation']=2
    put(wf/'ios.json',final);put(wf/'ios-backup.json',final);(wf/'ios.lock').touch()
    return root,e,config,caps,wf,native_dir

def context_test(p,mutation=None,accept=False):
    root,e,cfg,caps,wf,nd=context_fixture(p)
    if mutation:mutation(root,e,cfg,caps,wf,nd)
    with patch.object(rm,'native_reference',return_value=({},{})) as bound:
        call=lambda:rm.fresh_platform_context(root,e,'T1','B','android',cfg,caps,helper)
        if accept:
            assert call()['workflow']=='registered_same_arm_sibling_only';assert bound.call_count==1
        else:rejected(call)

def entry_fixture(p):
    root=p/'root';e=root/'cache/business/independent-evaluation';record=e/'continuations/T1/B/android/native';record.mkdir(parents=True)
    old=root/'original-outcome.json';put(old,{'task':'T1','arm':'B','profile':'android'})
    config={'path':str(root/'config.json'),'sha256':'config'};caps={'path':str(root/'capsule.json'),'sha256':'source'}
    put(record/'ENTRY.json',{'never':'forwarded'});put(record/'failure.json',{'type':'ValueError'})
    put(record/'outcome.json',{'error':{'type':'ValueError','message':'Original fresh independent context is no longer empty before first native UI'},'source_unchanged':True,'config':config,'source_capsule':caps})
    row={'record':str(record),'original':{'original_outcome':rm.ref(old),'original_config':config,'original_source_capsule':caps}}
    base={'path':str(root/'base-authority.json'),'sha256':'immutable'};put(e/'NATIVE-CONTINUATION-AUTHORITY.json',base)
    resumed=e/'entry-resumptions/T1/B/android/native';permit=root/'operators/cohort2/coordination/UNCLAIMED-ENTRY-v3-ADMISSION.json'
    value={'kind':'explicit-unclaimed-pre-forward-entry-admission','operator_review_completed':True,'base_authority':base,
        'entry_resume':{'scope':'T1/B/android','licensed_record':str(record),'resumed_record':str(resumed),'failed_record_files':{n:rm.ref(record/n) for n in ['ENTRY.json','outcome.json','failure.json']}}}
    put(permit,value);return root,e,row,resumed,permit,value

def entry_test(p,mutation=None,accept=False):
    root,e,row,resumed,permit,value=entry_fixture(p)
    if mutation:mutation(root,e,row,resumed,permit,value)
    call=lambda:rm.entry_resume(root,row,resumed,permit,rm.sha(permit))
    if accept:assert call()[0]==rm.ref(permit)
    else:rejected(call)

def alternate_binding_test(p):
    root,e,row,resumed,permit,value=entry_fixture(p);claim=rm.continuation_claim_path(e,'T1','B','android')
    # No permit on a record different from the authority's exact record.
    authority={'scopes':{'T1/B/android':row}};pin=value['base_authority']
    v={'task':'T1','arm':'B','profile':'android','action':'native','record':str(resumed),'config':row['original']['original_config'],'source_capsule':row['original']['original_source_capsule'],
       'original_claim':{'path':'/original','sha256':'old'},'original_outcome':row['original']['original_outcome'],'authority':pin}
    row['original']['original_claim']=v['original_claim'];put(claim,v)
    with patch.object(rm,'continuation_authority',return_value=(authority,pin)),patch.object(rm,'verify_unforwarded',return_value=(None,None)):
        rejected(lambda:rm.native_reference(e,'T1','B','android',v['config'],v['source_capsule'],resumed/'outcome.json','unknown'))

def permitted_binding_test(p,break_chain=False):
    root,e,row,resumed,permit,value=entry_fixture(p);claim=rm.continuation_claim_path(e,'T1','B','android')
    authority={'scopes':{'T1/B/android':row}};pin=value['base_authority'];row['original']['original_claim']={'path':'/original','sha256':'old'}
    v={'version':1,'task':'T1','arm':'B','profile':'android','action':'native','record':str(resumed),'config':row['original']['original_config'],'source_capsule':row['original']['original_source_capsule'],
       'original_claim':row['original']['original_claim'],'original_outcome':row['original']['original_outcome'],'authority':pin,
       'entry_resume_permit':rm.ref(permit),'failed_preclaim_entry':value['entry_resume']['failed_record_files']['outcome.json'],'licensed_original_record':row['record']}
    if break_chain:v['failed_preclaim_entry']={'path':'/foreign','sha256':'foreign'}
    put(claim,v);put(resumed/'cycle.json',{});put(resumed/'capture.json',{})
    outcome={'task':'T1','arm':'B','profile':'android','action':'native','config':v['config'],'source_capsule':v['source_capsule'],
       'native_continuation_claim':rm.ref(claim),'original_zero_forwarding_outcome':v['original_outcome'],'source_unchanged':True,'new_ui_acquisition':True,'capture_reused':False,
       'capture':rm.ref(resumed/'capture.json'),'cycle':rm.ref(resumed/'cycle.json')}
    put(resumed/'outcome.json',outcome)
    with patch.object(rm,'continuation_authority',return_value=(authority,pin)),patch.object(rm,'verify_unforwarded',return_value=(None,None)):
        call=lambda:rm.native_reference(e,'T1','B','android',v['config'],v['source_capsule'],resumed/'outcome.json',rm.sha(resumed/'outcome.json'))
        if break_chain:rejected(call)
        else:assert call()[0]==outcome

def collector_plan(p,mutation=None):
    order=[{'task':'T'+str(n),'scope':a,'profiles':['ios','android']} for n in range(1,6) for a in (['I','A','B'] if n%2 else ['I','B','A'])]
    flat=[(i['task'],i['scope'],profile) for i in order if (i['task'],i['scope'])!=('T1','I') for profile in i['profiles']]
    # Actual order has all initial references first, then case/arm order.
    order=[i for i in order if i['scope']=='I']+[i for i in order if i['scope']!='I']
    flat=[(i['task'],i['scope'],profile) for i in order if (i['task'],i['scope'])!=('T1','I') for profile in i['profiles']]
    authority={'scopes':{'/'.join(v):{'record':str(p/'native'/('/'.join(v)))} for v in flat}}
    rows=[{'scope':'/'.join(v),'licensed_record':authority['scopes']['/'.join(v)]['record'],'record':authority['scopes']['/'.join(v)]['record']} for v in flat[11:]]
    rows[0]['record']=str(p/'entry-resumed');plan={'kind':'remaining-unexecuted-native-scopes-v3','entry_resumption_record':rows[0]['record'],'remaining':rows}
    if mutation:mutation(plan);rejected(lambda:cm.validate_plan(plan,order,authority))
    else:assert len(cm.validate_plan(plan,order,authority))==17

def halted_cleanup(p):
    root=p/'root';runner=p/'runner.py';runner.write_text('# synthetic runner\n');record=root/'native';episode=root/'episode';episode.mkdir(parents=True)
    key='T1/B/android';row={'scope':key,'record':str(record),'licensed_record':str(record)}
    authority={'scopes':{key:{'original':{'original_config':{'path':str(root/'config.json')}}}}}
    permit={'base_authority':{'path':str(root/'authority.json')},'_path':str(root/'permit.json')};calls=[]
    def run(argv,**kwargs):
        calls.append(argv);out=Path(argv[argv.index('--record')+1]);out.mkdir(parents=True)
        if argv[argv.index('--action')+1]=='native':
            put(out/'outcome.json',{'source_unchanged':True,'error':{'message':'original error'}});put(root/'operators/RESOURCE-HALT.json',{'halt':True})
        else:put(out/'service/resources.json',{'final':True,'cleanup_errors':[],'remaining_directories':[],'remaining_devices':[]})
        return SimpleNamespace(returncode=1)
    old=SimpleNamespace(positive=lambda q:q.is_file() and json.loads(q.read_text()).get('final') is True)
    with patch.object(cm.subprocess,'run',side_effect=run):
        op,out,closure=cm.execute_one(root,runner,cm.sha(runner),rm,old,row,authority,'authority-sha',permit,'permit-sha',episode)
    assert len(calls)==2 and closure and 'cleanup-native-resources' in calls[1]
    rejected(lambda:cm.check_halt(root))
    # Existing failed record is retained; there can be no automatic same-scope retry.
    rejected(lambda:cm.execute_one(root,runner,cm.sha(runner),rm,old,row,authority,'sha',permit,'sha',episode))

def no_facts(p):
    closure=p/'closure.json';put(closure,{'final':True});out=p/'outcome.json';put(out,{'source_unchanged':True})
    fake=SimpleNamespace(native_reference=lambda *a:(_ for _ in ()).throw(ValueError('No fresh original facts')))
    authority={'scopes':{'T1/B/android':{'original':{'original_config':{},'original_source_capsule':{}}}}}
    rejected(lambda:cm.validate_facts(fake,p,{'scope':'T1/B/android'},out,{'source_unchanged':True},closure,authority))

def unclosed_initial_gate(p):
    monitor=p/'monitor';monitor.mkdir()
    fake=SimpleNamespace(monitor_gate=lambda *a:None)
    rejected(lambda:cm.closed_initial_gate(p,monitor,fake))
    put(monitor/'CLOSED.json',{'status':'failed','positive_idle':{'all_clear':False}})
    rejected(lambda:cm.closed_initial_gate(p,monitor,rm))

def entry_failure_terminal(p):
    root=p/'root';record=root/'cache/business/independent-evaluation/operation';root.mkdir(parents=True)
    command=[sys.executable,'-B',str(COORD/'independent_native_v3.py'),'--root',str(root),'--task','T1','--arm','B','--profile','android','--config',str(root/'none.json'),'--record',str(record),'--action','native']
    proc=subprocess.run(command,capture_output=True,text=True);(p/'process.log').write_text(proc.stdout+proc.stderr)
    assert proc.returncode==1
    entry=rm.load(record/'ENTRY.json');out=rm.load(record/'outcome.json')
    assert entry['started_at_clock_gettime_monotonic']<=out['finished_at_clock_gettime_monotonic'] and out['error'] and out['wall_seconds']>=0

def main():
    dest=Path(sys.argv[1]).resolve();dest.mkdir(parents=True,exist_ok=False);results=[]
    tests=[
      ('strict-sibling-valid',lambda p:context_test(p,accept=True)),
      ('reject-current-review',lambda p:context_test(p,lambda r,e,c,a,w,n:put(Path(c['review_store'])/'used.json',{}))),
      ('reject-current-source-review',lambda p:context_test(p,lambda r,e,c,a,w,n:put(Path(c['source_review_store'])/'used.json',{}))),
      ('reject-current-workflow',lambda p:context_test(p,lambda r,e,c,a,w,n:put(w/'android.json',{}))),
      ('reject-foreign-owner',lambda p:context_test(p,lambda r,e,c,a,w,n:put(w/'owner.json',{'format':'native-ui-workflow-v1','owner':'foreign'}))),
      ('reject-sibling-extra-cycle',lambda p:context_test(p,lambda r,e,c,a,w,n:put(w/'ios.json',{'cycles':[]}))),
      ('reject-sibling-backup-drift',lambda p:context_test(p,lambda r,e,c,a,w,n:put(w/'ios-backup.json',{'generation':3}))),
      ('reject-unpinned-sibling-output',lambda p:context_test(p,lambda r,e,c,a,w,n:put(n/'service/workflow-state.json',{'forged':True}))),
      ('reject-lock-payload',lambda p:context_test(p,lambda r,e,c,a,w,n:(w/'ios.lock').write_text('unexpected'))),
      ('preclaim-valid',lambda p:entry_test(p,accept=True)),
      ('reject-unreviewed-permit',lambda p:entry_test(p,lambda r,e,row,n,permit,v:put(permit,{**v,'operator_review_completed':False}))),
      ('reject-extra-entry-evidence',lambda p:entry_test(p,lambda r,e,row,n,permit,v:put(Path(row['record'])/'command.json',{}))),
      ('reject-existing-claim',lambda p:entry_test(p,lambda r,e,row,n,permit,v:put(rm.continuation_claim_path(e,'T1','B','android'),{'record':str(n)}))),
      ('reject-alternate-record-without-permit',alternate_binding_test),
      ('explicit-permitted-record-binds',permitted_binding_test),
      ('reject-permitted-record-failure-chain-drift',lambda p:permitted_binding_test(p,True)),
      ('remaining-exact17',collector_plan),
      ('reject-schedule-reorder',lambda p:collector_plan(p,lambda v:v['remaining'].reverse())),
      ('halt-still-closes-no-retry',halted_cleanup),
      ('missing-facts-stop',no_facts),
      ('unclosed-initial-monitor-prohibits-final',unclosed_initial_gate),
      ('early-failure-has-entry-terminal-clock',entry_failure_terminal),
    ]
    for name,fn in tests:
        p=dest/name;p.mkdir();start=time.time()
        try:fn(p);result={'name':name,'status':'passed','wall_seconds':time.time()-start}
        except BaseException as exc:result={'name':name,'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
        put(p/'RESULT.json',result);results.append(result)
    put(dest/'RESULT.json',{'version':1,'scope':'Synthetic operator metadata; no SDK, actual RUN, product verdict or treatment benefit','tests':results,'passed':sum(v['status']=='passed' for v in results),'failed':sum(v['status']=='failed' for v in results)})
    print(json.dumps({'passed':sum(v['status']=='passed' for v in results),'failed':sum(v['status']=='failed' for v in results)}))
    if any(v['status']=='failed' for v in results):raise SystemExit(1)

if __name__=='__main__':main()
