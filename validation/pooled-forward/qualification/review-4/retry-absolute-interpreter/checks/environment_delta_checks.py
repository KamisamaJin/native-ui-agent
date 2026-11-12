from delta_support import *
from harness import check,assert_that,RESULTS
import capture_validity as cv
import ios_observe as observer
from types import SimpleNamespace
from unittest.mock import patch

# Synthetic secrets stay in process memory; persisted records contain fingerprints only.
canaries=['QUAL-CANARY-'+uuid.uuid4().hex for _ in range(12)]
BASE_ENV={'QUAL_IOS_INPUT':canaries[0],'QUAL_ANDROID_INPUT':canaries[1],'QUAL_SHARED_INPUT':canaries[2],'QUAL_PRESENCE_INPUT':canaries[3],'LANG':'C'}
save(ROOT/'raw'/'delta-admission.json',{'candidate_freeze_sha256':sha(ROOT/'raw'/'CANDIDATE-FREEZE-4.json'),'evidence_classes':['HOST','SIMULATED'],'native_runs':0,'scope':'additive environment/build-selector identity only; original 66 not rerun','input_fingerprints':fingerprints(BASE_ENV,BASE_ENV),'expectations':['changed relevant selector blocks original adoption','declared ios/android/shared scope is preserved','present empty differs from absent','effective native-option overrides suppress irrelevant ambient input changes','iOS actual controller command pins environment/dependency files while caller fixture changes retain compiled identity','prepare_build validates/reuses or rebuilds host artifacts under mocked toolchain','no raw canary in controller/cache artifacts'],'rows':['D01-declared-ios-scope','D02-declared-android-scope','D03-declared-shared-scope','D04-presence-empty-identity','D05-conventional-ios-selector','D06-gradle-project-selector','D07-conventional-shared-selector','D08-effective-native-overrides','D09-unrelated-selector-ignored','D10-invalid-declaration-rejected','D11-controller-and-prepare-build-cache-identity','D12-secret-canary-artifact-scan']})

def scoped(name,changed,ios,android):
 base=configure(project('delta-'+name));original={}
 for p in ['ios','android']:
  v,r,o=invoke(base,p,p+'-original',BASE_ENV,expect=0);assert_that(r['boundary_attempts']==1,'baseline collection not dispatched');emitted_build_digest(v);original[p]=(v,context_of(v))
 after=dict(BASE_ENV);after.update(changed);details={}
 for p,expected in [('ios',ios),('android',android)]:
  v,r,o=invoke(base,p,p+'-ordinary-final-after-selector',after,extra=['--final'],expect=0)
  assert_that(v['status']=='accepted'and v['native_executed']==expected and r['boundary_attempts']==int(expected)and v['capture_reused']==(not expected),'selector effect/adoption scope differs for '+p)
  current=context_of(v)
  if expected:assert_that(canonical_sha(current)!=canonical_sha(original[p][1]),'changed selector did not bind current capture context')
  else:assert_that(v['capture_sha256']==original[p][0]['capture_sha256'],'unaffected original packet identity changed')
  emitted_build_digest(v);details[p]={'cycle':str(o/'cycle.json'),'new_collection':v['native_executed'],'reused':v['capture_reused'],'dependency_environment':current['dependency_environment']}
 return details
check('D01-declared-ios-scope',lambda:scoped('ios',{'QUAL_IOS_INPUT':canaries[4]},True,False))
check('D02-declared-android-scope',lambda:scoped('android',{'QUAL_ANDROID_INPUT':canaries[5]},False,True))
check('D03-declared-shared-scope',lambda:scoped('shared',{'QUAL_SHARED_INPUT':canaries[6]},True,True))

def presence():
 base=configure(project('delta-presence'));env=dict(BASE_ENV);env.pop('QUAL_PRESENCE_INPUT')
 v,r,o=invoke(base,'ios','absent-original',env,unset=['QUAL_PRESENCE_INPUT'],expect=0);first=context_of(v)['dependency_environment']['QUAL_PRESENCE_INPUT'];assert_that(first=={'present':False,'sha256':None},'absence not represented exactly')
 env['QUAL_PRESENCE_INPUT']='';v,r,o=invoke(base,'ios','empty-present-feedback',env,expect=0);empty=context_of(v)['dependency_environment']['QUAL_PRESENCE_INPUT'];assert_that(r['boundary_attempts']==1 and empty=={'present':True,'sha256':value_hash('')},'present-empty adopted absent evidence')
 v,r,o=invoke(base,'ios','absent-again-final',{},unset=['QUAL_PRESENCE_INPUT'],extra=['--final'],expect=0)
 assert_that(r['boundary_attempts']==1 and not v['capture_reused'],'presence removal did not invalidate')
 return {'absent':first,'empty':empty,'final_cycle':str(o/'cycle.json')}
check('D04-presence-empty-identity',presence)
check('D05-conventional-ios-selector',lambda:scoped('swift-exec',{'SWIFT_EXEC':canaries[7]},True,False))
check('D06-gradle-project-selector',lambda:scoped('gradle-project',{'ORG_GRADLE_PROJECT_qualification':canaries[8]},False,True))
check('D07-conventional-shared-selector',lambda:scoped('locale',{'LANG':'C.UTF-8'},True,True))

def effective():
 base=configure(project('delta-effective'));env=dict(BASE_ENV,DEVELOPER_DIR=canaries[8],JAVA_HOME=canaries[9],ANDROID_HOME=canaries[10]);original={}
 for p in ['ios','android']:
  v,r,o=invoke(base,p,p+'-original',env,expect=0);original[p]=v
 after=dict(BASE_ENV,DEVELOPER_DIR=canaries[9],JAVA_HOME=canaries[10],ANDROID_HOME=canaries[11]);out={}
 for p in ['ios','android']:
  v,r,o=invoke(base,p,p+'-same-effective-options-final',after,extra=['--final'],expect=0);ctx=context_of(v);c=d.load(base/p/'config.json')
  assert_that(v['capture_reused']and r['boundary_attempts']==0 and v['capture_sha256']==original[p]['capture_sha256'],'irrelevant overridden ambient selector invalidated '+p)
  overrides={'DEVELOPER_DIR':c['native_options']['developer-dir']}if p=='ios'else{'JAVA_HOME':c['native_options']['java-home'],'ANDROID_HOME':c['native_options']['android-sdk']}
  for key,value in overrides.items():assert_that(ctx['dependency_environment'][key]=={'present':True,'sha256':value_hash(value)},'effective native option not fingerprinted')
  out[p]={'cycle':str(o/'cycle.json'),'effective_selector_fingerprints':{key:ctx['dependency_environment'][key]for key in overrides}}
 return out
check('D08-effective-native-overrides',effective)
check('D09-unrelated-selector-ignored',lambda:scoped('unrelated',{'QUAL_UNRELATED_INPUT':canaries[11]},False,False))

def invalid():
 base=configure(project('delta-invalid'));cp=base/'ios'/'config.json';c=d.load(cp);cases=[]
 for i,value in enumerate([{'unknown':['QUAL_IOS_INPUT']},{'ios':'QUAL_IOS_INPUT'},{'shared':['BAD-NAME']},{'ios':[7]}]):
  c['dependency_environment']=value;save(cp,c);v,r,o=invoke(base,'ios','invalid-'+str(i),BASE_ENV)
  assert_that(r['exit_code']!=0 and r['boundary_attempts']==0 and not(o/'cycle.json').exists(),'invalid declaration reached native/adoption')
  cases.append({'exit':r['exit_code'],'stderr':r['stderr'],'output':str(o)})
 # Resources never acquired, but explicitly close this positive-owned root if created.
 c['dependency_environment']={'ios':['QUAL_IOS_INPUT']};save(cp,c);invoke(base,'ios','owned-cleanup',BASE_ENV,action='cleanup-native-resources',expect=0)
 return cases
check('D10-invalid-declaration-rejected',invalid)

cache_info={}
def cache_identity():
 global cache_info
 base=configure(project('delta-build-sequence'));dep=base/'dependency-input.txt';dep.write_text('independent dependency epoch 1\n')
 cp=base/'ios'/'config.json';c=d.load(cp);c['dependency_files']={'ios':[str(dep)]};save(cp,c)
 env=dict(BASE_ENV);captures=[];prepare=[];calls=[];cache=base/'private-mock-cache';cache.mkdir();marker=save(cache/'.review4-owner.json',{'owner':'review-4','token':uuid.uuid4().hex,'root':str(cache)})
 args=SimpleNamespace(build_cache=str(cache),sdk='iphonesimulator',product='NeutralProduct',simulator='SIMULATED-ONLY',developer_dir='/SIMULATED/Developer',build_context_sha256=None)
 bridge=Path(c['bridge']);manifest_sources={str(p):sha(p)for p in [bridge,CANDIDATE/'assets/ios-observer/ObserverApp.swift',CANDIDATE/'assets/ios-observer/ObserverTests.swift',CANDIDATE/'scripts/ios_observe.py',CANDIDATE/'scripts/observation_contract.py']}
 def mock_command(argv,tool_env,log=None):
  row={'evidence_class':'SIMULATED toolchain response / HOST cache files','argv':argv,'environment_fingerprints':fingerprints(tool_env,SELECTORS),'log':str(log)if log else None}
  if argv==['xcodebuild','-version']:text='SIMULATED Xcode 0\nBuild version QUALIFICATION\n'
  elif argv[:2]==['xcrun','--sdk']:text='/SIMULATED/SDK\n'if argv[-1]=='--show-sdk-path'else'0\n'
  elif argv[:2]==['xcodebuild','build-for-testing']:
   derived=Path(argv[argv.index('-derivedDataPath')+1]);products=derived/'Build'/'Products';products.mkdir(parents=True);(products/'Observer.xctestrun').write_text('SIMULATED compiled test plan\n');(products/'ObserverApp.app').mkdir();(products/'ObserverApp.app'/'executable').write_bytes(b'SIMULATED compiled bytes\n');text='SIMULATED build-for-testing; no SDK executed\n'
  else:raise AssertionError('unexpected tool command')
  row['response_sha256']=value_hash(text);calls.append(row)
  if log:Path(log).write_text(text)
  return subprocess.CompletedProcess(argv,0,stdout=text)
 def collect(label):
  v,r,o=invoke(base,'ios',label,env,expect=0);digest=emitted_build_digest(v);ctx=context_of(v);captures.append({'label':label,'cycle':str(o/'cycle.json'),'context_sha256':canonical_sha(ctx),'compile_sha256':digest,'capture_sha256':v['capture_sha256'],'boundary_attempts':r['boundary_attempts'],'dependency_environment':ctx['dependency_environment'],'build_dependencies':ctx['build_dependencies']});return digest
 def build(label,digest):
  output=base/'mock-build-output'/label;output.mkdir(parents=True);args.build_context_sha256=digest;manifest={'source_hashes':manifest_sources};tool_env=dict(os.environ,**env,DEVELOPER_DIR=args.developer_dir)
  with patch.object(observer,'command',mock_command):runfile=observer.prepare_build(args,output,bridge,None,tool_env,manifest)
  save(output/'mock-manifest.json',dict(manifest,evidence_class='SIMULATED toolchain, actual HOST cache'))
  before=len([v for v in calls if v['argv'][:2]==['xcodebuild','build-for-testing']]);prepare.append({'label':label,'runfile':str(runfile),'manifest':str(output/'mock-manifest.json'),'signature':manifest['build_cache']['signature'],'hit':manifest['build_cache']['hit'],'build_count_so_far':before,'compiled_artifacts':manifest['build_cache']['artifacts']});return manifest
 digest0=collect('original-feedback');m0=build('initial-build',digest0);assert_that(not m0['build_cache']['hit'],'first private cache was warm')
 reapprove_fixture(base);digest_fixture=collect('fixture-only-feedback');mf=build('fixture-only-build',digest_fixture)
 assert_that(digest_fixture==digest0 and mf['build_cache']['hit']and captures[0]['context_sha256']!=captures[1]['context_sha256']and captures[1]['boundary_attempts']==1,'fixture identity either reused stale evidence or forced compiled key drift')
 env['QUAL_IOS_INPUT']=canaries[4];digest_env=collect('declared-environment-feedback');me=build('declared-environment-build',digest_env)
 assert_that(digest_env!=digest_fixture and not me['build_cache']['hit'],'declared env did not bind actual controller/cache identity')
 (ROOT/'raw'/'build-sequence-original-dependency.txt').write_bytes(dep.read_bytes());dep.write_text('independent dependency epoch 2\n');digest_dep=collect('dependency-file-feedback');md=build('dependency-file-build',digest_dep)
 assert_that(digest_dep!=digest_env and not md['build_cache']['hit'],'explicit dependency file did not bind controller/cache identity')
 env['QUAL_ANDROID_INPUT']=canaries[5];v,r,o=invoke(base,'ios','android-only-environment-inspection',env,expect=0);ma=build('android-only-environment-build',digest_dep)
 assert_that(r['boundary_attempts']==0 and ma['build_cache']['hit'],'Android-only env cross-invalidated iOS compilation/evidence')
 env['SWIFT_EXEC']=canaries[7];digest_swift=collect('conventional-environment-feedback');ms=build('conventional-environment-build',digest_swift)
 assert_that(digest_swift!=digest_dep and not ms['build_cache']['hit'],'conventional selector not pinned by actual compiled key')
 output=base/'mock-build-output'/'invalid-controller-digest';output.mkdir();args.build_context_sha256='invalid';count=len([v for v in calls if v['argv'][:2]==['xcodebuild','build-for-testing']]);error=None
 try:
  with patch.object(observer,'command',mock_command):observer.prepare_build(args,output,bridge,None,dict(os.environ,**env,DEVELOPER_DIR=args.developer_dir),{'source_hashes':manifest_sources})
 except ValueError as e:error=str(e)
 assert_that(error is not None and len([v for v in calls if v['argv'][:2]==['xcodebuild','build-for-testing']])==count,'invalid controller digest reached a build/cache success')
 save(ROOT/'raw'/'mock-toolchain-commands.json',calls);save(ROOT/'raw'/'mock-cache-results.json',{'captures':captures,'prepare_build':prepare,'invalid_digest_error':error,'private_cache':{'path':str(cache),'marker_sha256':sha(marker)}})
 v,r,o=invoke(base,'ios','ordinary-final-current-epoch',env,extra=['--final'],expect=0);assert_that(v['status']=='accepted'and v['capture_reused']and r['boundary_attempts']==0,'current capture did not finalize')
 cache_info={'cache':str(cache),'marker_sha256':sha(marker),'commands':'raw/mock-toolchain-commands.json','results':'raw/mock-cache-results.json'}
 return {'captures':captures,'prepare_build':prepare,'build_commands':count,'invalid_digest_rejected':True,'final_cycle':str(o/'cycle.json'),'actual_native_commands':0,'cache':cache_info}
check('D11-controller-and-prepare-build-cache-identity',cache_identity)

# Scan all produced artifact bytes, not just context headers. Never print canary values.
def secret_scan():
 needles=[v.encode()for v in canaries];hits=[];scanned=0
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file()or p.is_symlink():continue
  data=p.read_bytes();scanned+=1
  matches=[i for i,n in enumerate(needles)if n in data]
  if matches:hits.append({'path':str(p.relative_to(ROOT)),'canary_indices':matches,'file_sha256':sha(p)})
 save(ROOT/'raw'/'secret-canary-scan.json',{'evidence_class':'HOST artifact bytes under supplied selectors','canary_fingerprints':[value_hash(v)for v in canaries],'files_scanned':scanned,'raw_canary_matches':hits,'values_persisted':False,'limit':'No real SDK/tool stdout was produced; the mock toolchain emits fixed synthetic output.'})
 assert_that(not hits,'raw selector canary leaked into '+str(len(hits))+' artifacts; see fingerprint-only scan receipt')
 return {'files_scanned':scanned,'matches':0,'fingerprints_only':True,'scan':'raw/secret-canary-scan.json'}
check('D12-secret-canary-artifact-scan',secret_scan,'HOST')
save(ROOT/'raw'/'environment-delta-results.json',RESULTS)
save(ROOT/'raw'/'private-mock-cache-cleanup-handle.json',cache_info)
