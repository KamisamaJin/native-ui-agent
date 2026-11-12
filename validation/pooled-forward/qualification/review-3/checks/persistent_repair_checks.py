from review3_support import *
from harness import check,assert_that,RESULTS

save(ROOT/'raw'/'review-3-additional-control-admission.json',{'native':False,'original_58_unchanged':True,'requirements':['actual source revisions and reverts remain append-only measured transitions','missing/failed current-source retest preserves original behavior obligations','pending context cannot be cleared by oracle/bridge/environment changes','only fresh original-obligation passes can close pending handoff','public cycle publication interruption must recover safely from observed staged bytes without extra collection where a durable transaction exists'], 'new_rows':['R01-multiple-patches-revert-and-retest','R02-pending-oracle-drift-current-state','R03-pending-bridge-drift-current-state','R04-pending-revert-environment-drift','R05-host-publication-before-checkpoint','R06-host-publication-after-checkpoint','R07-host-publication-after-cycle-before-clear','R08-host-publication-corruption-rejects'],'at_unix':time.time()})

def assert_pending(base,ref,expected_map,before_map,previous=None):
 s=state(base);p=s.get('completion');assert_that(bool(p),'measured revision has no pending proof');value=ref_value(p)
 assert_that(value['task']==ref and value['status']=='patched_needs_native_retest'and not value['explicit_worker_completion'],'pending proof lost task/origin/disposition')
 assert_that(value['source_after_map']==expected_map and value['source_after_sha256']==d.digest(expected_map)and value['source_before_sha256']==d.digest(before_map),'measured before/after maps differ from actual files')
 changed=sorted(k for k in set(before_map)|set(expected_map)if before_map.get(k)!=expected_map.get(k))
 assert_that(value['measured_changed_files']==changed,'measured paths differ from independent byte delta')
 assert_that(value['previous_completion']==previous,'revision chain skipped/replaced prior proof')
 return p,value

def multi_revision():
 base=project('r3-multiple-revisions',broken=True);task_ref,task=open_failure(base);config=d.load(base/'ios'/'config.json');origin_map=independent_map(config);origin_hash=sha(Path(task_ref['path']));proofs=[]
 def failed_revision(label,text,before,previous):
  source(base,text);actual=independent_map(config);value,raw,out=invoke(base,label,supplied={'REVIEW_COLLECTOR_FAIL':'1'})
  assert_that(raw['exit_code']!=0 and not(out/'cycle.json').exists()and raw['boundary_attempts']==1,'failed boundary did not preserve unaccepted one-attempt disposition')
  ref,proof=assert_pending(base,task_ref,actual,before,previous);proofs.append((ref,proof));return ref,actual,out
 a,map_a,ao=failed_revision('patch-A-boundary-error','Attempt-A',origin_map,None)
 before=state(base);count=len(list((base/'workflow'/'completions').glob('*.json')))
 value,raw,out=invoke(base,'same-source-boundary-error-again',supplied={'REVIEW_COLLECTOR_FAIL':'1'})
 assert_that(raw['exit_code']!=0 and raw['boundary_attempts']==1 and state(base)['completion']==a and len(list((base/'workflow'/'completions').glob('*.json')))==count,'unchanged retry created another measured revision or native pass')
 value,raw,out=invoke(base,'duplicate-explicit-completion',action='complete-native-repair',extra=['--task',task_ref['path'],'--task-sha256',task_ref['sha256']])
 assert_that(raw['exit_code']!=0 and state(base)['completion']==a and len(list((base/'workflow'/'completions').glob('*.json')))==count,'duplicate handoff was accepted or appended')
 b,map_b,bo=failed_revision('patch-B-boundary-error','Attempt-B',map_a,a)
 c,map_c,co=failed_revision('revert-to-origin-boundary-error','Broken',map_b,b)
 assert_that(map_c==origin_map and state(base)['completion']==c,'reversion erased pending native obligations')
 value,raw,failed=invoke(base,'reverted-code-real-controller-recheck',expect=0);report=d.load(failed/'capture'/'automatic.json')
 expected_ids={r['id']for r in task['failed_assertions']}
 assert_that(raw['boundary_attempts']==1 and value['status']!='accepted'and {r['id']for r in report['assertions']if r['status']=='failed'}==expected_ids and state(base)['completion']==c,'failed reverted retest closed or rewrote original F')
 assert_that(sha(Path(task_ref['path']))==origin_hash,'original task was rewritten')
 source(base,'Ready');actual=independent_map(config);value,raw,passed=invoke(base,'correct-patch-and-fresh-recheck',expect=0);report=d.load(passed/'capture'/'automatic.json');patch=d.load(passed/'patch-completion.json');closure=d.load(passed/'patch-retest.json');dref=closure['completion'];dproof=ref_value(dref)
 assert_that(patch==dproof and patch['previous_completion']==c and patch['source_after_map']==actual,'final patch proof is not append-only or measured')
 assert_that(raw['boundary_attempts']==1 and report['counts']=={'passed':2,'failed':0,'unassessed':0}and set(closure['assertion_ids'])==expected_ids,'closure lacked fresh original-obligation passes')
 assert_that(not state(base).get('completion')and not state(base).get('task'),'passed affected-row retest did not close pending handoff')
 proofs.append((dref,dproof));proof_count=len(list((base/'workflow'/'completions').glob('*.json')))
 value,raw,inspected=invoke(base,'unchanged-inspection-after-closure',expect=0)
 assert_that(raw['boundary_attempts']==0 and len(list((base/'workflow'/'completions').glob('*.json')))==proof_count,'inspection fabricated a repair round or recollected')
 value,raw,final=invoke(base,'ordinary-final-after-closure',extra=['--final'],expect=0)
 assert_that(value['status']=='accepted'and value['capture_reused']and raw['boundary_attempts']==0,'fresh full post-repair proof did not finalize through gates')
 for ref,proof in proofs:assert_that(ref_value(ref)==proof,'an earlier measured receipt was edited')
 return {'original_task':task_ref,'revision_receipts':[ref for ref,_ in proofs],'origin_map':origin_map,'revision_maps':[map_a,map_b,map_c,actual],'failed_retest_cycle':str(failed/'cycle.json'),'passed_retest_cycle':str(passed/'cycle.json'),'closure':str(passed/'patch-retest.json'),'final_cycle':str(final/'cycle.json'),'completed_native_tests':'SIMULATED only; all attempts logged including raised boundaries'}
check('R01-multiple-patches-revert-and-retest',multi_revision)

def context_drift(kind):
 base=project('r3-pending-context-'+kind,broken=True);task_ref,task=open_failure(base);config=d.load(base/'ios'/'config.json');origin=independent_map(config);source(base,'StillBroken'if kind=='oracle'else'Ready');current=independent_map(config)
 value,raw,failed=invoke(base,'measured-patch-with-failed-recheck',supplied={'REVIEW_COLLECTOR_FAIL':'1'});pending,proof=assert_pending(base,task_ref,current,origin,None)
 assert_that(raw['exit_code']!=0 and raw['boundary_attempts']==1,'pending setup did not fail actual controlled boundary')
 original_task_sha=sha(Path(task_ref['path']))
 reseal(base,expected='StillBroken')if kind=='oracle'else reseal(base,bridge=True)
 before=(base/'workflow'/'ios.json').read_bytes();value,raw,out=invoke(base,'default-after-context-drift');final=None
 if value:final,fr,fo=invoke(base,'ordinary-final-after-context-drift',extra=['--final'])
 now=state(base)
 assert_that(not(final and final['status']=='accepted')and not(value and value['status']=='accepted'),'pending original failure accepted under changed '+kind)
 assert_that(now.get('completion')==pending and ref_value(pending)==proof and sha(Path(task_ref['path']))==original_task_sha,'pending source/native obligation lost on context drift')
 assert_that(not(out/'patch-retest.json').exists(),'context drift fabricated original-obligation retest closure')
 save(ROOT/'raw'/('v13.2-pending-'+kind+'-continuation.json'),{'original_task':task_ref,'pending_completion':pending,'observed_task_before_drift':d.load(base/'origin-external-pin.json')['task'],'next_exit':raw['exit_code'],'next_boundary_attempts':raw['boundary_attempts'],'next_status':value['status']if value else None,'final_status':final['status']if final else None,'state_bytes_unchanged_on_rejection':(base/'workflow'/'ios.json').read_bytes()==before,'command':str(ROOT/'raw'/(base.name+'--default-after-context-drift.public-command.json'))})
 invoke(base,'explicit-owned-resource-cleanup',action='cleanup-native-resources',expect=0)
 return {'original_task':task_ref,'pending_completion':pending,'next_exit':raw['exit_code'],'boundary_attempts':raw['boundary_attempts'],'stderr':raw['stderr'],'final_status':final['status']if final else None}
check('R02-pending-oracle-drift-current-state',lambda:context_drift('oracle'))
check('R03-pending-bridge-drift-current-state',lambda:context_drift('bridge'))

def revert_context():
 base=project('r3-revert-context',broken=True);task_ref,task=open_failure(base);config_path=base/'ios'/'config.json';config=d.load(config_path);origin=independent_map(config);source(base,'Attempt-A');map_a=independent_map(config)
 value,raw,out=invoke(base,'patch-before-boundary-error',supplied={'REVIEW_COLLECTOR_FAIL':'1'});a,ap=assert_pending(base,task_ref,map_a,origin,None)
 source(base,'Broken');environment=Path(config['environment']);old_env=environment.read_bytes();old_config=config_path.read_bytes();changed=d.load(environment);changed['theme']='dark';save(environment,changed);config['environment_sha256']=d.digest(changed);save(config_path,config)
 value,raw,out=invoke(base,'revert-with-environment-drift')
 assert_that(raw['exit_code']!=0 and state(base)['completion']==a and not(out/'cycle.json').exists(),'origin-byte revert bypassed pending context gate')
 environment.write_bytes(old_env);config_path.write_bytes(old_config);config=d.load(config_path)
 value,raw,out=invoke(base,'restored-context-revert-boundary-error',supplied={'REVIEW_COLLECTOR_FAIL':'1'});b,bp=assert_pending(base,task_ref,independent_map(config),map_a,a)
 assert_that(bp['source_after_sha256']==d.digest(origin),'revert is not bound to actual original bytes')
 value,raw,final=invoke(base,'ordinary-final-of-still-failing-revert',extra=['--final'],expect=0);report=d.load(final/'capture'/'automatic.json')
 assert_that(value['status']!='accepted'and raw['boundary_attempts']==1 and report['counts']=={'passed':0,'failed':2,'unassessed':0}and state(base)['completion']==b,'reverted failing code was accepted or pending proof erased')
 return {'original_task':task_ref,'first_revision':a,'revert_revision':b,'context_error_command':str(ROOT/'raw'/(base.name+'--revert-with-environment-drift.public-command.json')),'failed_final':str(final/'cycle.json'),'final_status':value['status'],'counts':report['counts']}
check('R04-pending-revert-environment-drift',revert_context)

save(ROOT/'raw'/'review-3-persistent-results.json',RESULTS)
