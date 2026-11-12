from harness import *
import source_identity

# Additive neutral controls; no original-47 row or expectation is edited.
save(ROOT/'raw'/'new-controls-admission.json',{
 'version':1,'frozen_before_new_control_execution':True,'native':False,
 'protocol_interpretation_sha256':sha(ROOT/'raw'/'REPAIR-HANDOFF-INTERPRETATION.md'),
 'requirements':['default-owned measured completion is equivalent to explicit completion when exact task/context/diff is pinned and fresh retest is mandatory','open original failure cannot be cleared by changed oracle, bridge or environment without independent new-scope admission','a completed source-edit action with no native result still has pending native behavior obligations','kernel lease clock must be shared across processes; bounds use emitted row schema','idle retirement lock must be fully closed before reacquisition'],
 'new_row_ids':['N01-default-owned-valid-completion','N02-default-open-task-oracle-change','N03-default-open-task-bridge-change-with-source-edit','N04-default-open-task-environment-change-with-source-edit','N05-default-pending-retest-oracle-change','N06-default-pending-retest-bridge-change','N07-default-missing-original-task','N08-kernel-clock-shared-across-processes','N09-expiry-using-shared-lease-clock','N10-active-idle-expiry-after-durable-retirement']})

def reseal(base,*,expected=None,bridge=False):
 cp=base/'ios'/'config.json';config=d.load(cp);facts_path=base/'ios'/'facts.json';facts=d.load(facts_path)
 if expected is not None:facts['label']['value']=expected
 if bridge:
  path=Path(config['bridge']);path.write_text(path.read_text()+'SIMULATED independent bridge context v2\n');facts['launch']['bridge_sha256']=sha(path)
 save(facts_path,facts)
 contract_path=base/'ios'/'contract.json';contract=d.load(contract_path);contract['sources'][0]['sha256']=sha(facts_path);save(contract_path,contract)
 lock=d.seal(contract_path,base/'ios');save(Path(config['design_lock']),lock)
 old_plan=d.load(Path(config['plan']));plan,_=d.compile_contract(lock,d.digest(lock),'neutral','ios',old_plan['design_contract']['bindings'],old_plan['design_contract']['base_actions']);save(Path(config['plan']),plan)
 config['design_sha256']=d.digest(lock);save(cp,config)

def change_environment(base):
 cp=base/'ios'/'config.json';config=d.load(cp);path=Path(config['environment']);value=d.load(path);value['theme']='dark';save(path,value);config['environment_sha256']=d.digest(value);save(cp,config)

def open_failure(base):
 value,record,out=command('open-original-failure',base)
 task_path=out/'repair-task.json';task=d.load(task_path);ref={'path':str(task_path.resolve()),'sha256':sha(task_path)}
 assert_that(value['status']=='awaiting_source_repair' and len(task['failed_assertions'])==2,'precondition is not an original supported failure')
 save(base/'original-task-external-pin.json',{'task':ref,'original_failed_ids':[r['id']for r in task['failed_assertions']],'capture':task['capture'],'context_sha256':task['context_sha256'],'source_map':task['source_map']})
 return ref,task

def valid_default_completion():
 base=project('new-default-valid-completion',broken=True);ref,task=open_failure(base)
 config=d.load(base/'ios'/'config.json');path=base/'production'/'ios'/'Component.swift';before=sha(path);path.write_text('Ready\n')
 value,record,out=command('default-after-actual-patch',base)
 receipt=d.load(out/'patch-completion.json');state=d.load(base/'workflow'/'ios.json');durable_ref=state['completion'];durable=d.load(Path(durable_ref['path']))
 actual=source_identity.fingerprint(config,'ios')
 assert_that(receipt==durable and sha(Path(durable_ref['path']))==durable_ref['sha256'],'default completion is not durably pinned')
 assert_that(receipt['task']==ref and receipt['capture']==task['capture'] and receipt['context_sha256']==task['context_sha256'],'default proof lost original task/capture/context')
 assert_that(receipt['status']=='patched_needs_native_retest' and not receipt['explicit_worker_completion'],'default proof fabricates worker origin or handoff pass')
 assert_that(receipt['source_before_sha256']==d.digest(task['source_map']) and receipt['source_after_sha256']==d.digest(actual) and receipt['measured_changed_files']==['0/Component.swift'],'default proof did not measure actual namespace/diff')
 assert_that(value['native_executed'] and record['simulated_collection_count']==1 and value['status']!='accepted','source edit did not force fresh recheck before final acceptance')
 original_capture=Path(task['capture']['path']);new_capture=Path(value['capture_result'])
 assert_that(str(new_capture)!=str(original_capture) and d.load(new_capture.parent/'source-before.json')==actual,'recheck did not bind new current source')
 next_value,next_record,next_out=command('inspect-current-default-again',base)
 assert_that(not next_value['native_executed'] and next_record['simulated_collection_count']==0 and d.load(base/'workflow'/'ios.json')['completion']==durable_ref,'repeated unchanged default inspection created a new repair round or collection')
 final,fr,fo=command('ordinary-final-after-current-recheck',base,extra=['--final'])
 assert_that(final['status']=='accepted' and final['capture_reused'] and fr['simulated_collection_count']==0,'eligible new post-repair packet did not finalize')
 return {'task':ref,'completion':durable_ref,'source_before_file_sha256':before,'source_after_file_sha256':sha(path),'current_source_map':actual,'recheck_cycle':str(out/'cycle.json'),'final_cycle':str(fo/'cycle.json'),'separate_worker_cli_invocations':0}
check('N01-default-owned-valid-completion',valid_default_completion)

def open_context(kind,source_edit):
 base=project('new-open-context-'+kind,broken=True);ref,task=open_failure(base)
 if source_edit:(base/'production'/'ios'/'Component.swift').write_text('Ready\n')
 if kind=='oracle':reseal(base,expected='Broken')
 elif kind=='bridge':reseal(base,bridge=True)
 else:change_environment(base)
 before_state=(base/'workflow'/'ios.json').read_bytes()
 value,record,out=command('default-with-changed-context',base,expect=None)
 state=d.load(base/'workflow'/'ios.json')
 accepted=bool(value and value['status']=='accepted')
 assert_that(not accepted and not(out/'patch-completion.json').exists() and state.get('task')==ref,'default changed-context continuation cleared or replaced original open task')
 assert_that((base/'workflow'/'ios.json').read_bytes()==before_state,'rejected context change mutated original handoff state')
 assert_that(record['simulated_collection_count']==0,'changed open context dispatched new evidence before independent scope admission')
 cleanup(base,label='explicit-cleanup')
 return {'raw_command':str(ROOT/'raw'/(base.name+'--default-with-changed-context.command.json')),'exit_code':record['exit_code'],'original_task':ref,'stderr':record['stderr'],'source_edit':source_edit}
check('N02-default-open-task-oracle-change',lambda:open_context('oracle',False))
check('N03-default-open-task-bridge-change-with-source-edit',lambda:open_context('bridge',True))
check('N04-default-open-task-environment-change-with-source-edit',lambda:open_context('environment',True))

def pending_context(kind):
 base=project('new-pending-context-'+kind,broken=True);ref,task=open_failure(base)
 # Actual changed bytes are deliberately not a demonstrated fix. The next native boundary fails.
 source=base/'production'/'ios'/'Component.swift';source.write_text('StillBroken\n' if kind=='oracle' else 'Ready\n')
 v,r,failed_out=command('default-patch-before-failed-native-retest',base,expect=None,env_extra={'REVIEW_COLLECTOR_FAIL':'1'})
 state=d.load(base/'workflow'/'ios.json');completion_ref=state.get('completion')
 assert_that(r['exit_code']!=0 and completion_ref and state.get('task') is None,'precondition missing durable default-generated pending-native receipt')
 completion=d.load(Path(completion_ref['path']))
 assert_that(completion['task']==ref and completion['status']=='patched_needs_native_retest' and not completion['explicit_worker_completion'],'precondition lost exact automatic handoff')
 save(base/'pending-native-handoff-external-pin.json',{'completion':completion_ref,'task':ref,'original_failed_assertions':task['failed_assertions'],'failed_default_command':str(ROOT/'raw'/(base.name+'--default-patch-before-failed-native-retest.command.json'))})
 if kind=='oracle':reseal(base,expected='StillBroken')
 else:reseal(base,bridge=True)
 value,record,out=command('default-after-pending-context-change',base,expect=None)
 final=final_record=final_out=None
 if value:
  final,final_record,final_out=command('ordinary-final-after-context-change',base,extra=['--final'],expect=None)
 final_accepted=bool(final and final['status']=='accepted')
 detail={'kind':kind,'original_task':ref,'completion':completion_ref,'failed_retest_command':str(ROOT/'raw'/(base.name+'--default-patch-before-failed-native-retest.command.json')),'next_command':str(ROOT/'raw'/(base.name+'--default-after-pending-context-change.command.json')),'next_status':value['status']if value else None,'next_exit_code':record['exit_code'],'next_collector_count':record['simulated_collection_count'],'final_status':final['status']if final else None,'final_command':str(ROOT/'raw'/(base.name+'--ordinary-final-after-context-change.command.json'))if final else None,'original_expected':'Ready','current_source':source.read_text().strip()}
 save(ROOT/'raw'/('pending-context-'+kind+'-repro.json'),detail)
 cleanup(base,label='explicit-cleanup')
 assert_that(not final_accepted,'pending original failure accepted after changed '+kind+' without successful original-context native retest or new-scope admission; '+json.dumps(detail))
 assert_that(record['simulated_collection_count']==0 or (value and value['status']!='accepted'),'changed pending repair collected current facts without retaining original obligations')
 return detail
check('N05-default-pending-retest-oracle-change',lambda:pending_context('oracle'))
check('N06-default-pending-retest-bridge-change',lambda:pending_context('bridge'))

def missing_task():
 base=project('new-default-missing-task',broken=True);ref,task=open_failure(base)
 task_path=Path(ref['path']);original=task_path.read_bytes();(base/'preserved-original-task.json').write_bytes(original);task_path.unlink()
 (base/'production'/'ios'/'Component.swift').write_text('Ready\n')
 value,record,out=command('default-with-missing-original-task',base,expect=None)
 assert_that(not value and record['exit_code']!=0 and record['simulated_collection_count']==0 and not(out/'patch-completion.json').exists(),'missing original task permitted handoff/native credit')
 cleanup(base,label='explicit-cleanup')
 return {'original_task_pin':ref,'retained_original_bytes':str(base/'preserved-original-task.json'),'stderr':record['stderr'],'native_credit':False}
check('N07-default-missing-original-task',missing_task)

save(ROOT/'raw'/'new-default-context-results.json',RESULTS)
