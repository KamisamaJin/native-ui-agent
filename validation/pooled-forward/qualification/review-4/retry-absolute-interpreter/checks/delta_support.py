from support import *
import subprocess

IOS=['DEVELOPER_DIR','TOOLCHAINS','SWIFT_EXEC','XCODE_XCCONFIG_FILE','SDKROOT']
ANDROID=['JAVA_HOME','ANDROID_HOME','ANDROID_SDK_ROOT','COMPOSE_SNAPSHOT_ID','JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','GRADLE_OPTS','GRADLE_USER_HOME']
CUSTOM=['QUAL_IOS_INPUT','QUAL_ANDROID_INPUT','QUAL_SHARED_INPUT','QUAL_PRESENCE_INPUT','QUAL_UNRELATED_INPUT']
SELECTORS=IOS+ANDROID+CUSTOM+['LANG','LC_ALL','TZ','ORG_GRADLE_PROJECT_qualification']

def value_hash(v):return hashlib.sha256(v.encode()).hexdigest()
def fingerprints(env,names):return {n:{'present':n in env,'sha256':value_hash(env[n])if n in env else None}for n in sorted(set(names))}
def canonical_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def attempts():
 p=ROOT/'raw'/'delta-boundary.jsonl'
 return sum(json.loads(v)['event']=='begin'for v in p.read_text().splitlines())if p.exists()else 0

def delta_collector(self,argv,*,env,stdout,timeout=None):
 token=uuid.uuid4().hex;config=d.load(Path(os.environ['REVIEW_CONFIG']));names=set(SELECTORS)
 for values in config.get('dependency_environment',{}).values():names.update(values)
 common={'id':token,'evidence_class':'SIMULATED','argv':argv,'config':os.environ['REVIEW_CONFIG'],'pid':os.getpid()}
 def append(v):
  with(ROOT/'raw'/'delta-boundary.jsonl').open('a')as f:f.write(json.dumps(dict(common,**v))+'\n')
 append({'event':'begin','at_unix':time.time(),'inherited_selector_fingerprints':fingerprints(env,names)})
 try:code=simulated_collector(self,argv,env=env,stdout=stdout,timeout=timeout)
 except BaseException as e:append({'event':'raised','at_unix':time.time(),'type':type(e).__name__,'error':str(e)});raise
 append({'event':'end','at_unix':time.time(),'exit_code':code});return code

def invoke(base,platform,label,env_values,*,unset=(),extra=(),action='native',expect=None):
 config=base/platform/'config.json';out=base/'evidence'/label;argv=[sys.executable,'-B',str(ROOT/'checks'/'delta_cli.py'),action,'--config',str(config),'--output',str(out),*map(str,extra)]
 env=dict(os.environ,REVIEW_CANDIDATE=str(CANDIDATE),REVIEW_CONFIG=str(config),REVIEW_SIM_INVENTORY=str(ROOT/'work'/'simulated-inventory.json'),PATH=str(ROOT/'checks'/'bin')+os.pathsep+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1');env.update(env_values)
 for n in unset:env.pop(n,None)
 start=time.monotonic();wall=time.time();before=attempts();p=subprocess.run(argv,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35)
 record={'evidence_class':'HOST controller with SIMULATED native boundary','argv':argv,'candidate':str(CANDIDATE),'config':str(config),'selected_environment_fingerprints':fingerprints(env,set(SELECTORS)|set(env_values)|set(unset)),'started_at_unix':wall,'finished_at_unix':time.time(),'started_monotonic':start,'finished_monotonic':time.monotonic(),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'boundary_attempts':attempts()-before}
 save(ROOT/'raw'/(base.name+'--'+label+'.command.json'),record)
 value=d.load(out/'cycle.json')if(out/'cycle.json').exists()else None
 if expect is not None and p.returncode!=expect:raise AssertionError('public exit '+str(p.returncode)+' != '+str(expect)+'; '+p.stderr)
 return value,record,out

def configure(base):
 for platform in ['ios','android']:
  p=base/platform/'config.json';c=d.load(p);c['dependency_environment']={'ios':['QUAL_IOS_INPUT','QUAL_PRESENCE_INPUT'],'android':['QUAL_ANDROID_INPUT'],'shared':['QUAL_SHARED_INPUT']}
  if platform=='ios':c['native_options']['developer-dir']='/SIMULATED/Developer'
  else:
   java=base/'toolchain'/'java';java.mkdir(parents=True,exist_ok=True);(java/'release').write_text('SIMULATED_JAVA_VERSION=0\n');sdk=base/'toolchain'/'android';(sdk/'platforms'/'android-0').mkdir(parents=True,exist_ok=True);(sdk/'platforms'/'android-0'/'source.properties').write_text('SIMULATED_ANDROID_VERSION=0\n');c['native_options'].update({'java-home':str(java),'android-sdk':str(sdk)})
  save(p,c)
 return base

def context_of(cycle):return d.load(Path(cycle['capture_result']).parent/'capture-context.json')
def emitted_build_digest(cycle):
 capture=Path(cycle['capture_result']);receipt=d.load(capture);context=d.load(capture.parent/'capture-context.json');argv=receipt['argv']
 if context['platform']=='android':
  if '--build-context-sha256'in argv:raise AssertionError('Android received an iOS compilation flag')
  return None
 if argv.count('--build-context-sha256')!=1:raise AssertionError('Controller did not emit exactly one iOS build context')
 emitted=argv[argv.index('--build-context-sha256')+1]
 projection={k:context[k]for k in ['platform','native_options','tools','host_identity','build_dependencies','dependency_environment']};projection['bridge_sha256']=context['files']['bridge']
 if emitted!=canonical_sha(projection):raise AssertionError('Emitted compilation digest omits documented effective dependency inputs')
 return emitted

def reapprove_fixture(base):
 p=base/'ios'/'config.json';c=d.load(p);fixtures=d.load(Path(c['fixtures']));fixtures['fixtures'][0]['marker']='neutral-fixture-epoch-2';save(Path(c['fixtures']),fixtures)
 facts_path=base/'ios'/'facts.json';facts=d.load(facts_path);facts['launch']['fixtures_sha256']=d.digest(fixtures);save(facts_path,facts)
 contract_path=base/'ios'/'contract.json';contract=d.load(contract_path);contract['sources'][0]['sha256']=sha(facts_path);save(contract_path,contract);lock=d.seal(contract_path,base/'ios');save(Path(c['design_lock']),lock)
 old=d.load(Path(c['plan']));plan,_=d.compile_contract(lock,d.digest(lock),'neutral','ios',old['design_contract']['bindings'],old['design_contract']['base_actions']);save(Path(c['plan']),plan);c['design_sha256']=d.digest(lock);save(p,c)
