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

