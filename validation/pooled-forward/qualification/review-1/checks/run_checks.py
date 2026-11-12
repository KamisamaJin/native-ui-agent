from support import *
import subprocess, traceback, shutil
RESULTS=[]
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PATH=str(ROOT/'checks'/'bin')+os.pathsep+os.environ['PATH'],REVIEW_SIM_INVENTORY=str(ROOT/'work'/'simulated-inventory.json'))

def calls():
 p=ROOT/'raw'/'simulated-collector-calls.jsonl'
 return len(p.read_text().splitlines()) if p.exists() else 0

def command(label,base,platform='ios',action='native',extra=(),*,expect=0,env_extra=None):
 config=base/platform/'config.json';out=base/'evidence'/label
 argv=[sys.executable,'-B',str(ROOT/'checks'/'default_cli.py'),action,'--config',str(config),'--output',str(out),*map(str,extra)]
 env=dict(ENV,REVIEW_CONFIG=str(config));env.update(env_extra or {})
 start=time.monotonic();at=time.time();n=calls()
 p=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=35)
 record={'label':label,'evidence_class':'SIMULATED','argv':argv,'environment':{'PATH_first':str(ROOT/'checks'/'bin'),'REVIEW_CONFIG':str(config),'REVIEW_SIM_INVENTORY':ENV['REVIEW_SIM_INVENTORY'],**(env_extra or {})},'started_at_unix':at,'finished_at_unix':time.time(),'monotonic_start':start,'monotonic_end':time.monotonic(),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'simulated_collection_count':calls()-n}
 save(ROOT/'raw'/(base.name+'--'+label+'.command.json'),record)
 value=None
 if (out/'cycle.json').exists():value=d.load(out/'cycle.json')
 elif (out/'completion.json').exists():value=d.load(out/'completion.json')
 if expect is not None and p.returncode!=expect:raise AssertionError('exit '+str(p.returncode)+' != '+str(expect)+'; '+p.stderr[-1000:])
 return value,record,out

def check(name,fn,evidence='SIMULATED'):
 try:
  detail=fn();r={'id':name,'status':'P','evidence_class':evidence,'detail':detail}
 except Exception as e:
  r={'id':name,'status':'F','evidence_class':evidence,'error':repr(e),'traceback':traceback.format_exc()}
  save(ROOT/'first-failures'/(name+'-'+str(time.time_ns())+'.json'),r)
 RESULTS.append(r);save(ROOT/'raw'/'results-progress.json',RESULTS);print(name+': '+r['status'],flush=True)
 return r

def assert_that(v,reason):
 if not v:raise AssertionError(reason)

def cleanup(base,platform='ios',label='cleanup'):
 return command(label,base,platform,'cleanup-native-resources')

BASE=project(os.environ.get('REVIEW_RUN_NAME','default-path-v2'))
def first():
 value,record,out=command('first',BASE)
 resource=d.load(out/'resources.json')
 assert_that(value['native_executed'] and resource['pool']['enabled'],'default did not collect/enable pool')
 assert_that(resource['pool']['disposition']=='idle_owned_pool' and len(resource['remaining_devices'])==1,'default did not retain one owned device')
 return {'cycle':str(out/'cycle.json'),'status':value['status'],'pool':resource['pool'],'simulated_collection_count':record['simulated_collection_count']}
check('default-feedback-retains-bounded-pool',first)
def unchanged():
 value,record,out=command('unchanged',BASE)
 assert_that(not value['native_executed'] and record['simulated_collection_count']==0,'unchanged routing launched a collector')
 return {'cycle':str(out/'cycle.json'),'status':value['status'],'collector_count':0}
check('unchanged-default-routes-without-collector',unchanged)
def final_reuse():
 before=d.load(BASE/'evidence'/'first'/'cycle.json');path=Path(before['capture_result']);digest=sha(path)
 value,record,out=command('final-adopt',BASE,extra=['--final'])
 resource=d.load(out/'resources.json')
 assert_that(value['status']=='accepted' and value['capture_reused'] and not value['native_executed'],'ordinary final did not adopt original feedback packet')
 assert_that(value['capture_result']==str(path) and digest==sha(path),'original packet identity changed')
 assert_that(not resource['remaining_devices'] and not resource['remaining_directories'],'final did not retire resources')
 return {'cycle':str(out/'cycle.json'),'original_sha256':digest,'collector_count':record['simulated_collection_count'],'cleanup':str(out/'resources.json')}
check('ordinary-final-adopts-original-full-feedback-and-retires',final_reuse)
def fresh():
 value,record,out=command('explicit-final-fresh',BASE,extra=['--final','--fresh'])
 assert_that(value['native_executed'] and not value['capture_reused'] and record['simulated_collection_count']==1,'explicit fresh final did not execute collector')
 return {'cycle':str(out/'cycle.json'),'collector_count':1}
check('explicit-final-fresh-forces-new-packet',fresh)
def fresh_nonfinal():
 value,record,out=command('explicit-fresh-nonfinal',BASE,extra=['--fresh'])
 assert_that(value['native_executed'] and record['simulated_collection_count']==1,'documented --fresh request returned '+value['status']+' with no new packet')
 return {'cycle':str(out/'cycle.json'),'collector_count':record['simulated_collection_count']}
check('explicit-fresh-without-final',fresh_nonfinal)
cleanup(BASE)
save(ROOT/'raw'/'initial-results.json',RESULTS)
