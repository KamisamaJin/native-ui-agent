from harness import *

BASE=project('source-only-layer',source_duty=True)
config_path=BASE/'ios'/'config.json';config=d.load(config_path)
subject=BASE/'Integration.txt';subject.write_text('Ready\n')
facts_path=BASE/'ios'/'facts.json';facts=d.load(facts_path);facts['responsibilities'][0]['owner']='integration';save(facts_path,facts)
contract_path=BASE/'ios'/'contract.json';contract=d.load(contract_path);contract['sources'][0]['sha256']=sha(facts_path);save(contract_path,contract)
lock=d.seal(contract_path,BASE/'ios');save(BASE/'ios'/'lock.json',lock)
old_plan=d.load(BASE/'ios'/'plan.json');plan,_=d.compile_contract(lock,d.digest(lock),'neutral','ios',old_plan['design_contract']['bindings'],old_plan['design_contract']['base_actions']);save(BASE/'ios'/'plan.json',plan)
config.update(design_sha256=d.digest(lock),evidence_subjects={'production-label':[str(subject)]});save(config_path,config)
save(ROOT/'raw'/'source-only-layer-admission.json',{'evidence_class':'SIMULATED native; HOST source file','reason':'Integration file is predeclared source-review-only and outside all production/bridge roots. Its bytes must affect source duty, not native evidence.','source_path':str(subject),'source_sha256':sha(subject),'config_sha256':sha(config_path),'design_sha256':config['design_sha256'],'at_unix':time.time()})

def bind_observation(name):
 sub=save(BASE/(name+'.json'),{'version':1,'observations':[{'id':'source-duty','observed':True,'reason':'HOST current Integration.txt line 1 contains Ready.','citations':[{'path':str(subject),'line':1}]}]})
 return command(name,BASE,action='bind-source-review',extra=['--submission',sub])

def source_only():
 command('feedback',BASE);bind_observation('source-before-edit')
 v,r,o=command('first-final',BASE,extra=['--final'])
 assert_that(v['status']=='accepted' and v['capture_reused'],'initial source layer could not finalize')
 digest=sha(subject);subject.write_text('Ready\n// source-only integration responsibility note\n')
 v,r,o=command('final-source-duty-drift',BASE,extra=['--final'])
 assert_that(v['capture_reused'] and not v['native_executed'] and v['status']=='review_source','source-only edit invalidation crossed native boundary or stale source observation accepted')
 bind_observation('source-after-edit')
 cycle=o/'cycle.json';v,r,finished=command('finish-rebound-source',BASE,action='finish-native-review',extra=['--cycle',cycle,'--cycle-sha256',sha(cycle)])
 assert_that(v['status']=='accepted' and r['simulated_collection_count']==0,'rebound source duty did not close unchanged native proof')
 return {'before_sha256':digest,'after_sha256':sha(subject),'original_final':str(BASE/'evidence'/'first-final'/'cycle.json'),'source_drift_cycle':str(cycle),'completion':str(finished/'completion.json'),'native_collection_after_source_only_edit':0}
check('source-only-claim-edit-invalidates-only-source-layer',source_only)

def deleted_scoped_file():
 base=project('dependency-deleted-file');command('ios-original',base,'ios');command('android-original',base,'android')
 target=base/'production'/'ios'/'identity.txt';original=target.read_bytes();(ROOT/'raw'/'deleted-ios-identity.txt').write_bytes(original);target.unlink()
 result={}
 for p,expected in [('ios',True),('android',False)]:
  v,r,o=command(p+'-after-deletion',base,p,extra=['--final'])
  assert_that(v['native_executed']==expected and r['simulated_collection_count']==int(expected),'deleted source had incorrect invalidation scope '+p)
  result[p]={'cycle':str(o/'cycle.json'),'native_executed':v['native_executed']}
 return result
check('deleted-ios-source-invalidates-only-ios',deleted_scoped_file)

def symlink_unknown():
 base=project('dependency-symlink');command('original',base)
 target=base/'production'/'ios'/'alias.txt';target.symlink_to(base/'production'/'shared'/'Shared.txt')
 save(ROOT/'raw'/'symlink-dependency-admission.json',{'alias':str(target),'resolved':str(target.resolve()),'impact':'explicit unknown alias to relevant shared input; must not silently reuse current-code credit'})
 v,r,o=command('final-with-unknown-alias',base,extra=['--final'],expect=2)
 assert_that(not v and 'explicit dependency provider' in r['stderr'],'unknown alias did not reject current-code credit')
 cleanup(base,label='explicit-cleanup')
 return {'command':str(ROOT/'raw'/(base.name+'--final-with-unknown-alias.command.json')),'stderr':r['stderr'],'collector_count':0}
check('unknown-source-alias-rejects-current-credit',symlink_unknown)

save(ROOT/'raw'/'layer-results.json',RESULTS)
