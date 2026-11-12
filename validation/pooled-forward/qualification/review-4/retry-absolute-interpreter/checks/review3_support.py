from support import *
import subprocess

def attempts():
 p=ROOT/'raw'/'recorded-boundary-attempts.jsonl'
 return sum(json.loads(line)['event']=='begin'for line in p.read_text().splitlines())if p.exists()else 0

def recording_collector(self,argv,*,env,stdout,timeout=None):
 token=uuid.uuid4().hex;started=time.time();common={'id':token,'evidence_class':'SIMULATED','argv':argv,'controller_pid':os.getpid(),'config':os.environ.get('REVIEW_CONFIG')}
 def append(row):
  with(ROOT/'raw'/'recorded-boundary-attempts.jsonl').open('a')as f:f.write(json.dumps(dict(common,**row))+'\n')
 append({'event':'begin','at_unix':started,'supplied_failure':bool(os.environ.get('REVIEW_COLLECTOR_FAIL'))})
 try:
  code=simulated_collector(self,argv,env=env,stdout=stdout,timeout=timeout)
 except BaseException as e:
  append({'event':'raised','at_unix':time.time(),'error_type':type(e).__name__,'error':str(e)});raise
 append({'event':'end','at_unix':time.time(),'exit_code':code});return code

def invoke(base,label,*,action='native',extra=(),supplied=None,expect=None,wrapper='lifecycle_cli.py'):
 config=base/'ios'/'config.json';out=base/'evidence'/label
 argv=[sys.executable,'-B',str(ROOT/'checks'/wrapper),action,'--config',str(config),'--output',str(out),*map(str,extra)]
 env=dict(os.environ,PATH=str(ROOT/'checks'/'bin')+os.pathsep+os.environ['PATH'],REVIEW_CONFIG=str(config),REVIEW_CANDIDATE=str(CANDIDATE),REVIEW_SIM_INVENTORY=str(ROOT/'work'/'simulated-inventory.json'),PYTHONDONTWRITEBYTECODE='1');env.update(supplied or {})
 before=attempts();wall=time.time();mono=time.monotonic();p=subprocess.run(argv,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35)
 raw={'evidence_class':'HOST controller with SIMULATED SDK boundary','argv':argv,'environment_selection':{'REVIEW_CANDIDATE':str(CANDIDATE),'REVIEW_CONFIG':str(config),'PATH_first':str(ROOT/'checks'/'bin'),**(supplied or {})},'start_unix':wall,'end_unix':time.time(),'start_monotonic':mono,'end_monotonic':time.monotonic(),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'boundary_attempts':attempts()-before}
 save(ROOT/'raw'/(base.name+'--'+label+'.public-command.json'),raw)
 value=d.load(out/'cycle.json')if(out/'cycle.json').exists()else d.load(out/'completion.json')if(out/'completion.json').exists()else None
 if expect is not None and p.returncode!=expect:raise AssertionError('unexpected public exit '+str(p.returncode)+'; '+p.stderr)
 return value,raw,out

def independent_map(config):
 roots=[Path(p).resolve()for p in config['source_roots']];groups=config.get('platform_source_roots',{});assigned={Path(p).resolve()for values in groups.values()for p in values};wanted={Path(p).resolve()for p in groups.get('ios',[])+groups.get('shared',[])}|(set(roots)-assigned);out={}
 for i,root in enumerate(roots):
  if root not in wanted:continue
  for p in sorted(root.rglob('*'))if root.is_dir()else[root]:
   if p.is_file()and '__pycache__'not in p.parts and p.suffix!='.pyc':out[str(i)+'/'+(str(p.relative_to(root))if root.is_dir()else p.name)]=sha(p)
 return out

def state(base):return d.load(base/'workflow'/'ios.json')
def ref_value(ref):
 p=Path(ref['path'])
 if sha(p)!=ref['sha256']:raise AssertionError('raw pinned reference changed')
 return d.load(p)
def source(base,text):
 p=base/'production'/'ios'/'Component.swift';p.write_text(text+'\n');return p

def open_failure(base):
 value,record,out=invoke(base,'original-failure',expect=0);task_path=out/'repair-task.json';task=d.load(task_path);ref={'path':str(task_path.resolve()),'sha256':sha(task_path)}
 if value['status']!='awaiting_source_repair'or len(task['failed_assertions'])!=2:raise AssertionError('not an original supported neutral failure')
 config=d.load(base/'ios'/'config.json')
 if task['source_map']!=independent_map(config):raise AssertionError('task before map differs from actual files')
 save(base/'origin-external-pin.json',{'task':ref,'capture':task['capture'],'context_sha256':task['context_sha256'],'source_map':task['source_map'],'failed_assertions':task['failed_assertions']})
 return ref,task

def reseal(base,*,expected=None,bridge=False):
 cp=base/'ios'/'config.json';config=d.load(cp);facts_path=base/'ios'/'facts.json';facts=d.load(facts_path)
 if expected is not None:facts['label']['value']=expected
 if bridge:
  path=Path(config['bridge']);path.write_text(path.read_text()+'SIMULATED bridge context revision\n');facts['launch']['bridge_sha256']=sha(path)
 save(facts_path,facts);contract_path=base/'ios'/'contract.json';contract=d.load(contract_path);contract['sources'][0]['sha256']=sha(facts_path);save(contract_path,contract)
 lock=d.seal(contract_path,base/'ios');save(Path(config['design_lock']),lock);old=d.load(Path(config['plan']));plan,_=d.compile_contract(lock,d.digest(lock),'neutral','ios',old['design_contract']['bindings'],old['design_contract']['base_actions']);save(Path(config['plan']),plan);config['design_sha256']=d.digest(lock);save(cp,config)
