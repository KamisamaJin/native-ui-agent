#!/usr/bin/env python3
"""Sealed experiment operations. No task-specific selectors, expectations or repairs."""
import concurrent.futures,fcntl,hashlib,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
sys.path.insert(0,str((R/'candidate-v10' if (R/'candidate-v10').exists() else REPO/'native-ui-agent')/'scripts'))
import cohort_gate as gate,design_contract as d,execution_plan as xp,requirement_routes as rr,feedback_loop as feedback
DEV='/Applications/Xcode.app/Contents/Developer';JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home';SDK='/Users/rex/Library/Android/sdk'
ROOTS=['alerttoast/Sources','reply/Reply/app/src/main']
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def table(root):return{str(p.relative_to(root)):sha(p)for p in sorted(root.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.name not in {'SEAL.json','seal.json'}}
def seal_dir(root):save(root/'SEAL.json',{'sealedAtUnix':time.time(),'files':table(root)})
def verify_dir(root):assert read(root/'SEAL.json')['files']==table(root),str(root)
def fingerprint(w):return{str(p.relative_to(w)):sha(p)for rel in ROOTS for p in sorted((w/rel).rglob('*'))if p.is_file()}
def capsule(w,out):
 assert not out.exists();out.mkdir(parents=True);files=fingerprint(w)
 for rel in files:
  dest=out/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/rel,dest)
 for name in ['alerttoast','reply']:
  for license in ['LICENSE','LICENSE.md','LICENSE.txt','NOTICE']:
   path=w/name/license
   if path.is_file():dest=out/'licenses'/(name+'-'+license);dest.parent.mkdir(exist_ok=True);shutil.copy2(path,dest)
 save(out/'seal.json',{'sealedAtUnix':time.time(),'files':files});return files
def cohort(stage,members):
 paths={k:[str(p.relative_to(R))for folder in values for p in ([folder]if folder.is_file()else sorted(folder.rglob('*')))if p.is_file()and'__pycache__'not in p.parts]for k,values in members.items()}
 return gate.seal(R/'gates',stage,paths,R)
def tool_verify():
 for rel,h in read(R/'RELEASE.json')['files'].items():assert sha(R/rel)==h,rel
 for rel,h in read(R/'RELEASE.json')['repository_files'].items():assert sha(REPO/rel)==h,rel
def host_verify(w):
 for rel,h in read(w/'HOST-SEAL.json')['files'].items():assert sha(w/rel)==h,rel

def archive(source,destination):
 subprocess.run([sys.executable,'-B',str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(source),str(destination)],check=True)

def configuration(w,scope,case,pl,simulator):
 approval=read(scope/'approval.json');compiled=scope/'compiled'/case/pl
 return {'plan':str(compiled/'plan.json'),'design_lock':str(scope/'design-lock.json'),'design_sha256':approval['design_lock_sha256'],
         'routes':str(scope/'routes.json'),'routes_sha256':approval['routes_sha256'],
         'fixtures':str(scope/'cases'/case/'fixtures.json'),'bridge':str(scope/('Bridge.swift'if pl=='ios'else'ObserverBridge.kt')),
         'launch_ref':{'source':'reference','pointer':'/launch/'+case+'/'+pl},'source_roots':[str(w/rel)for rel in ROOTS],
         'native_options':{'package':str(w/'alerttoast'),'simulator':simulator,'developer-dir':DEV,'build-cache':str(w/'ios-build-cache')}if pl=='ios'else{'project':str(w/'reply/Reply'),'java-home':JAVA,'android-sdk':SDK},
         'policy':str(scope/'policy.json'),'policy_sha256':approval['policy_sha256'],
         'environment':str(scope/'cases'/case/('environment.'+pl+'.json')),'environment_sha256':approval['environment_sha256'][case][pl]}

def collect(w,scope,out,simulator,*,required_stage,source_seal,phase,mode='manual',cases=None,states=None,previous=None,history=None,final=False,adoptions=None):
 tool_verify();host_verify(w);authorization=gate.authorize(R/'gates',required_stage,R);verify_dir(scope)
 initial=fingerprint(w);assert initial==read(source_seal)['files'];out.mkdir(parents=True,exist_ok=False);started=time.time()
 save(out/'started.json',{'startedAtUnix':started,'phase':phase,'authorization':authorization,'sourceSealSHA256':sha(source_seal),'mode':mode})
 def platform(pl):
  outputs=[]
  for case in cases or [p.name for p in sorted((scope/'cases').iterdir())]:
   config=configuration(w,scope,case,pl,simulator)
   queue=time.time();slot=R/'cache'/('slot-ios-'+simulator if pl=='ios'else'slot-android');slot.parent.mkdir(parents=True,exist_ok=True)
   with slot.open('a')as stream:
    fcntl.flock(stream,fcntl.LOCK_EX);queue_seconds=time.time()-queue
    gate.authorize(R/'gates',required_stage,R);verify_dir(scope);tool_verify();host_verify(w);assert fingerprint(w)==initial
    requested=time.time();target=out/pl/case
    try:
     if mode=='default':
      if states:raise ValueError('Default service does not accept agent-selected states')
      prior=(previous or {}).get(pl,{}).get(case)
      if (adoptions or {}).get(pl,{}).get(case):config['adoption']=adoptions[pl][case]
      result=feedback.run_cycle(config,target,previous=prior['path']if prior else None,previous_sha=prior['sha256']if prior else None,
                                final=final,history=(history or {}).get(pl,{}).get(case,[]))
      result=dict(result,capture_result=read(target/'capture/result.json')if(target/'capture/result.json').is_file()else None)
     else:
      plan=read(config['plan']);lock=read(config['design_lock']);fixtures=read(config['fixtures']);bridge=Path(config['bridge'])
      value=xp.compile_execution(plan,lock,config['design_sha256'],fixtures,sha(bridge),launch_ref=config['launch_ref'],states=states)
      result=xp.run_execution(value,plan,lock,config['design_sha256'],fixtures,bridge,target,[w/rel for rel in ROOTS],config['native_options'],
                              policy=read(config['policy']),policy_sha=config['policy_sha256'],expected_environment=read(config['environment']),environment_sha=config['environment_sha256'])
    except Exception as error:
     result={'status':'wrapper_failure','startedAtUnix':requested,'finishedAtUnix':time.time(),'error':str(error),'traceback':traceback.format_exc()}
     save(target/'wrapper-failure.json',result)
   result=dict(result,case=case,platform=pl,queueSeconds=queue_seconds);outputs.append(result);save(out/pl/(case+'-result.json'),result)
   print(json.dumps({'phase':phase,'platform':pl,'case':case,'status':result['status'],'wall':result['finishedAtUnix']-result['startedAtUnix'],'queue':queue_seconds}),flush=True)
  return outputs
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:groups=list(pool.map(platform,['ios','android']))
 assert fingerprint(w)==initial
 result={'phase':phase,'startedAtUnix':started,'finishedAtUnix':time.time(),'runs':[r for group in groups for r in group]};save(out/'corpus.json',result);return result
