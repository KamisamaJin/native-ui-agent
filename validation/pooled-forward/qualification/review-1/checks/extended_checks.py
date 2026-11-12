from harness import *
import tarfile

def dep_case(name,group,expect_ios,expect_android):
 base=project(name)
 command('ios-original',base,'ios');command('android-original',base,'android')
 original={p:d.load(base/'evidence'/(p+'-original')/'cycle.json') for p in ['ios','android']}
 target=Path(d.load(base/'ios'/'config.json')['platform_source_roots'][group][0])/('Component.swift' if group=='ios' else 'Component.kt' if group=='android' else 'Shared.txt')
 before=sha(target);target.write_text(target.read_text()+'// controlled dependency edit\n')
 result={}
 try:
  for p,expected in [('ios',expect_ios),('android',expect_android)]:
   value,record,out=command(p+'-after-edit',base,p)
   assert_that(value['native_executed']==expected and record['simulated_collection_count']==int(expected),p+' invalidation differed')
   result[p]={'native_executed':value['native_executed'],'status':value['status'],'cycle':str(out/'cycle.json')}
 finally:
  cleanup(base,'ios','ios-cleanup');cleanup(base,'android','android-cleanup')
 return {'changed_path':str(target),'before_sha256':before,'after_sha256':sha(target),'platform_results':result}
check('source-ios-only-scoped-invalidation',lambda:dep_case('dependency-ios','ios',True,False))
check('source-android-only-scoped-invalidation',lambda:dep_case('dependency-android','android',False,True))
check('shared-source-invalidates-both',lambda:dep_case('dependency-shared','shared',True,True))

def unbound_output():
 base=project('dependency-irrelevant');command('original',base)
 (base/'unbound-output.txt').write_text('predeclared unrelated output\n')
 value,record,out=command('after-unbound-output',base,extra=['--final'])
 assert_that(value['capture_reused'] and record['simulated_collection_count']==0,'unbound output invalidated evidence')
 return {'cycle':str(out/'cycle.json'),'collector_count':0}
check('unbound-output-retains-evidence',unbound_output)

def build_change():
 base=project('dependency-build');command('ios-original',base,'ios');command('android-original',base,'android')
 path=base/'android-project'/'build.gradle.kts';path.write_text('// controlled build option v2\n')
 result={}
 try:
  for p,expected in [('ios',False),('android',True)]:
   v,r,o=command(p+'-after-build-change',base,p,extra=['--final'])
   assert_that(v['native_executed']==expected and r['simulated_collection_count']==int(expected),'build change scope differs for '+p)
   result[p]={'cycle':str(o/'cycle.json'),'native_executed':v['native_executed']}
 finally:
  cleanup(base,'ios','ios-cleanup');cleanup(base,'android','android-cleanup')
 return result
check('build-option-invalidates-only-android',build_change)

def tamper(kind,relative):
 base=project('tamper-'+kind);v,_,_=command('original',base)
 packet=Path(v['capture_result']).parent
 archive=ROOT/'raw'/('pristine-'+base.name+'.tar')
 with tarfile.open(archive,'x') as tf:tf.add(packet,arcname='capture')
 original_digest=sha(Path(v['capture_result']))
 target=packet/relative;before=sha(target)
 (ROOT/'raw'/('original-'+base.name+'-'+target.name)).write_bytes(target.read_bytes())
 if target.suffix=='.png':target.write_bytes(target.read_bytes()+b'SIMULATED TAMPER')
 elif target.suffix=='.json':
  data=d.load(target);data['SIMULATED_TAMPER']=True
  if target.name=='manifest.json':data.update(native_test_count=0,session='FOREIGN-SESSION',reset_contract='none')
  save(target,data)
 else:target.write_text('SIMULATED FOREIGN NATIVE RESULT; original removed in altered test copy\n')
 save(ROOT/'raw'/(base.name+'-mutation.json'),{'original_packet_archive':str(archive),'archive_sha256':sha(archive),'capture_receipt_sha256':original_digest,'altered_path':str(target),'before_sha256':before,'after_sha256':sha(target)})
 value,record,out=command('final-on-altered-packet',base,extra=['--final'],expect=None)
 cleanup(base,label='explicit-cleanup')
 accepted=bool(value and value.get('status')=='accepted')
 detail={'cycle':str(out/'cycle.json'),'exit_code':record['exit_code'],'accepted':accepted,'collector_count':record['simulated_collection_count'],'mutation':str(ROOT/'raw'/(base.name+'-mutation.json'))}
 assert_that(not accepted,'altered '+relative+' was accepted with collector_count='+str(record['simulated_collection_count'])+'; '+json.dumps(detail))
 return detail
check('capture-frame-tamper-rejected',lambda:tamper('frame','native/state-0.png'))
check('capture-manifest-tamper-rejected',lambda:tamper('manifest','native/manifest.json'))
check('capture-native-result-tamper-rejected',lambda:tamper('native-result','native/original-native-result.txt'))
check('capture-execution-coverage-tamper-rejected',lambda:tamper('coverage','execution-coverage.json'))

def drift(kind):
 base=project('drift-'+kind);command('original',base)
 config_path=base/'ios'/'config.json';config=d.load(config_path)
 if kind=='input':
  fixture_path=Path(config['fixtures']);fixture=d.load(fixture_path);fixture['fixtures'][0]['marker']='neutral-fixture-1';save(fixture_path,fixture)
 elif kind=='environment':
  env_path=Path(config['environment']);environment=d.load(env_path);environment['theme']='dark';save(env_path,environment);config['environment_sha256']=d.digest(environment);save(config_path,config)
 value,record,out=command('final-on-drift',base,extra=['--final'],expect=None)
 cleanup(base,label='explicit-cleanup')
 assert_that(not value or value['native_executed'] or value['status']!='accepted','drift reused stale accepted evidence')
 return {'cycle':str(out/'cycle.json'),'exit_code':record['exit_code'],'collector_count':record['simulated_collection_count'],'status':value.get('status') if value else None,'stderr':record['stderr']}
check('wrong-input-drift-reacquires-or-blocks',lambda:drift('input'))
check('wrong-environment-drift-reacquires-or-blocks',lambda:drift('environment'))

REPAIR=project('repair-handoff',broken=True)
def task_emitted():
 value,record,out=command('original-failure',REPAIR)
 task=d.load(out/'repair-task.json')
 assert_that(value['status']=='awaiting_source_repair' and len(task['failed_assertions'])==2,'supported failures missing default repair task')
 assert_that(task['capture']['sha256']==value['capture_sha256'],'repair capture is not original')
 assert_that(all(r['snapshot_indices'] for r in task['failed_assertions']),'repair task omitted original frame identities')
 return {'task':str(out/'repair-task.json'),'task_sha256':sha(out/'repair-task.json'),'failed_ids':[r['id'] for r in task['failed_assertions']]}
check('repair-default-task-emitted',task_emitted)
TASK=REPAIR/'evidence'/'original-failure'/'repair-task.json'
def no_change():
 _,r,o=command('false-completion',REPAIR,action='complete-native-repair',extra=['--task',TASK,'--task-sha256',sha(TASK)],expect=2)
 assert_that('no actual platform source change' in r['stderr'],'wrong no-change diagnostic')
 return {'command':str(ROOT/'raw'/(REPAIR.name+'--false-completion.command.json'))}
check('repair-no-change-completion-rejected',no_change)
def completion():
 path=REPAIR/'production'/'ios'/'Component.swift';before=sha(path);path.write_text('Ready\n')
 value,r,o=command('valid-completion',REPAIR,action='complete-native-repair',extra=['--task',TASK,'--task-sha256',sha(TASK)])
 assert_that(value['status']=='patched_needs_native_retest' and value['explicit_worker_completion'] and value['measured_changed_files']==['0/Component.swift'],'completion did not measure exact source edit')
 return {'receipt':str(o/'completion.json'),'before_sha256':before,'after_sha256':sha(path),'changed':value['measured_changed_files']}
check('repair-tool-completion-measures-patch',completion)
def duplicate():
 _,r,o=command('duplicate-completion',REPAIR,action='complete-native-repair',extra=['--task',TASK,'--task-sha256',sha(TASK)],expect=2)
 assert_that('foreign, stale or already completed' in r['stderr'],'duplicate completion diagnostic missing')
 return {'command':str(ROOT/'raw'/(REPAIR.name+'--duplicate-completion.command.json'))}
check('repair-duplicate-completion-rejected',duplicate)
def recheck():
 v,r,o=command('post-repair',REPAIR)
 assert_that(v['native_executed'] and r['simulated_collection_count']==1,'source repair did not require fresh collector')
 fv,fr,fo=command('final-post-repair',REPAIR,extra=['--final'])
 assert_that(fv['status']=='accepted' and fv['capture_reused'] and fr['simulated_collection_count']==0,'post-recheck full packet could not finalize without redundant collector')
 return {'recheck':str(o/'cycle.json'),'final':str(fo/'cycle.json'),'collector_count_after_repair':1}
check('repair-fresh-recheck-required',recheck)

def omitted_completion():
 base=project('repair-omitted-completion',broken=True);command('failure',base)
 path=base/'production'/'ios'/'Component.swift';path.write_text('Ready\n')
 v,r,o=command('post-edit-without-tool',base)
 completion=d.load(o/'patch-completion.json') if (o/'patch-completion.json').exists() else None
 fv,fr,fo=command('ordinary-final',base,extra=['--final'])
 assert_that(not (fv['status']=='accepted' and completion and not completion['explicit_worker_completion']), 'omitted completion tool was automatically recorded as patched, fresh simulated recheck ran, and final accepted; '+str(o/'patch-completion.json'))
 return {'cycle':str(o/'cycle.json'),'final':str(fo/'cycle.json'),'status':fv['status'],'automatic_completion':completion}
check('repair-without-explicit-tool-completion',omitted_completion)

save(ROOT/'raw'/'extended-results.json',RESULTS)
