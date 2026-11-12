from harness import *
import resource_manager as rm

# Frozen addendum: characterize the first observed clock/lifecycle failure, do not alter the candidate.
save(ROOT/'raw'/'focused-probe-admission.json',{'reason':'Observed negative elapsed monotonic values across normal default CLI processes on host Python3.9; preserve original failure and independently demonstrate scope.','expected':'Consecutive compatible feedback requests share one live managed device before finite expiry; child monotonic epochs must be safely comparable if persisted across processes.','native_credit':False,'at_unix':time.time()})

def clock_epochs():
 argv=[sys.executable,'-B','-c','import json,time,sys; print(json.dumps({"executable":sys.executable,"version":sys.version,"monotonic":time.monotonic(),"wall":time.time(),"clock":str(time.get_clock_info("monotonic"))}))']
 parent_before=time.monotonic();time.sleep(.5);parent_after=time.monotonic()
 p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5);child=json.loads(p.stdout)
 record={'evidence_class':'HOST','argv':argv,'parent_executable':sys.executable,'parent_version':sys.version,'parent_before':parent_before,'parent_after_delay':parent_after,'child':child,'exit_code':p.returncode,'stderr':p.stderr}
 save(ROOT/'raw'/'host-monotonic-cross-process.json',record)
 assert_that(child['monotonic']>=parent_before,'fresh child monotonic '+str(child['monotonic'])+' is earlier than parent pre-delay '+str(parent_before)+'; stored elapsed values cannot be compared across these processes')
 return record
check('persisted-host-monotonic-epochs-comparable',clock_epochs,'HOST')

def compatible_reuse():
 base=project('pool-consecutive-compatible')
 v,r,o=command('compatible-first',base);first=d.load(o/'resources.json')['remaining_devices'][0]
 path=base/'production'/'ios'/'Component.swift';before=sha(path);path.write_text('Ready\n// deterministic source edit; runtime/type/owner unchanged\n')
 v,r,o=command('compatible-second',base);second=d.load(o/'resources.json')['remaining_devices'][0]
 events=[json.loads(line) for line in (o/'resource-events.jsonl').read_text().splitlines()]
 detail={'evidence_class':'SIMULATED','first':first,'second':second,'source_path':str(path),'source_before_sha256':before,'source_after_sha256':sha(path),'second_resource_events':str(o/'resource-events.jsonl'),'create_count':sum(e['kind']=='simulator_create_intent' for e in events),'removed_count':sum(e['kind']=='simulator_removed' for e in events),'first_receipt':str(base/'evidence'/'compatible-first'/'resources.json'),'second_receipt':str(o/'resources.json')}
 save(ROOT/'raw'/'pool-consecutive-compatible-repro.json',detail)
 cleanup(base,label='explicit-cleanup')
 assert_that(first['udid']==second['udid'] and detail['create_count']==1,'compatible feedback pool was recreated; '+json.dumps(detail))
 return detail
check('cross-process-default-compatible-pool-reuse',compatible_reuse)

def missing_cleanup_receipt_gate():
 base=ROOT/'work'/'retirement-failure';o=base/'evidence'/'final-delete-fails'
 raw=d.load(ROOT/'raw'/'retirement-failure--final-delete-fails.command.json')
 assert_that(raw['exit_code']!=0 and not(o/'cycle.json').exists(),'failed retirement was accepted')
 reason=d.load(o/'service-error.json')
 cleanup(base,label='bounded-cleanup-recovery')
 return {'acceptance_gate':'P','resource_receipt':'U: resources.json absent because cleanup failed in __enter__','service_error':reason,'original_first_assertion_failure':'retained in lifecycle-results.json; it expected a resource receipt instead of distinguishing the unavailable fact'}
check('failed-retirement-remains-unaccepted-entry-path',missing_cleanup_receipt_gate)

def raw_log_integrity():
 base=project('tamper-native-log');v,_,_=command('original',base)
 capture=Path(v['capture_result']).parent
 import tarfile
 archive=ROOT/'raw'/'pristine-native-log.tar'
 with tarfile.open(archive,'x') as tf:tf.add(capture,arcname='capture')
 target=capture/'native.log';before=sha(target);target.write_text('SIMULATED log substituted: native test execution failed\n')
 save(ROOT/'raw'/'tamper-native-log-mutation.json',{'path':str(target),'before_sha256':before,'after_sha256':sha(target),'original_archive':str(archive),'archive_sha256':sha(archive)})
 value,record,out=command('final-after-log-substitution',base,extra=['--final'],expect=None)
 cleanup(base,label='explicit-cleanup')
 assert_that(not(value and value['status']=='accepted'),'original raw native.log replaced but accepted with '+str(record['simulated_collection_count'])+' new collectors; '+str(out/'cycle.json'))
 return {'cycle':str(out/'cycle.json'),'status':value.get('status') if value else None}
check('canonical-native-log-tamper-rejected',raw_log_integrity)

def contradiction_coverage():
 base=project('tamper-contradictory-coverage');v,_,_=command('original',base)
 capture=Path(v['capture_result']).parent;target=capture/'execution-coverage.json';original=target.read_bytes();(ROOT/'raw'/'original-contradictory-execution-coverage.json').write_bytes(original)
 data=d.load(target);data['satisfied']=False;data['missing_states']=['opening','second']
 for row in data['required_states']:row.update(complete=False,satisfied=False,reason='SIMULATED required state unavailable')
 save(target,data)
 value,record,out=command('final-after-coverage-contradiction',base,extra=['--final'],expect=None)
 cleanup(base,label='explicit-cleanup')
 assert_that(not(value and value['status']=='accepted'),'inner execution coverage now declares every state missing but original packet accepted; '+str(out/'cycle.json'))
 return {'cycle':str(out/'cycle.json'),'status':value.get('status') if value else None}
check('contradictory-inner-coverage-tamper-rejected',contradiction_coverage)

save(ROOT/'raw'/'focused-results.json',RESULTS)
