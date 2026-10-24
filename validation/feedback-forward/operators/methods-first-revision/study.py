#!/usr/bin/env python3
"""Source capsules, complete cohort gates and guarded shared native collection."""
import concurrent.futures,fcntl,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
sys.path.insert(0,str((R/'candidate-v9' if (R/'candidate-v9').exists() else REPO/'native-ui-agent')/'scripts'))
import cohort_gate as gate,design_contract as d,execution_plan as xp,requirement_routes as rr
DEV='/Applications/Xcode.app/Contents/Developer';JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home';SDK='/Users/rex/Library/Android/sdk'
ROOTS=['alerttoast/Sources','reply/Reply/app/src/main']
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def table(root):return{str(p.relative_to(root)):sha(p)for p in sorted(root.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.name!='SEAL.json'}
def seal_dir(root):save(root/'SEAL.json',{'sealedAtUnix':time.time(),'files':table(root)})
def verify_dir(root):
 for rel,h in read(root/'SEAL.json')['files'].items():assert sha(root/rel)==h,rel

def fingerprint(w):return{str(p.relative_to(w)):sha(p)for rel in ROOTS for p in sorted((w/rel).rglob('*'))if p.is_file()}
def capsule(w,out):
 assert not out.exists();out.mkdir(parents=True);files=fingerprint(w)
 for rel,h in files.items():
  dest=out/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/rel,dest)
 save(out/'seal.json',{'sealedAtUnix':time.time(),'files':files})
 return files

def cohort(stage,members):
 paths={k:[str(p.relative_to(R))for folder in values for p in ([folder]if folder.is_file()else sorted(folder.rglob('*')))if p.is_file()and'__pycache__'not in p.parts]for k,values in members.items()}
 return gate.seal(R/'gates',stage,paths,R)
def tool_verify():
 for rel,h in read(R/'candidate-v9-freeze.json')['files'].items():assert sha(R/'candidate-v9'/rel)==h,rel

def host_verify(w):
 for rel,h in read(w/'HOST-SEAL.json')['files'].items():assert sha(w/rel)==h,rel

def archive(source,destination):
 # Only portable evidence enters cohort seals. Original SDK bundles stay in the
 # explicitly ignored cache and are never referenced by a published gate.
 subprocess.run([sys.executable,'-B',str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(source),str(destination)],check=True)

def collect(w,scope,out,simulator,*,states=None,cases=None,required_stage,source_seal,phase):
 tool_verify();host_verify(w);authorization=gate.authorize(R/'gates',required_stage,R)
 verify_dir(scope)
 initial=fingerprint(w);assert initial==read(source_seal)['files']
 approval=read(scope/'approval.json');lock=read(scope/'design-lock.json');policy=read(scope/'policy.json')
 assert d.digest(lock)==approval['design_lock_sha256']and d.digest(policy)==approval['policy_sha256']
 out.mkdir(parents=True,exist_ok=False);started=time.time()
 save(out/'started.json',{'startedAtUnix':started,'phase':phase,'authorization':authorization,'source':initial,'sourceSealSHA256':sha(source_seal)})
 def platform(pl):
  outputs=[]
  for case in cases or ['P1','P2']:
   c=scope/'compiled'/case/pl;plan=read(c/'plan.json');fixture=read(scope/'cases'/case/'fixtures.json');bridge=scope/('Bridge.swift'if pl=='ios'else'ObserverBridge.kt')
   value=xp.compile_execution(plan,lock,approval['design_lock_sha256'],fixture,sha(bridge),launch_ref={'source':'reference','pointer':'/launch/'+case+'/'+pl},states=states,strategy='coalesced')
   native={'package':w/'alerttoast','simulator':simulator,'developer-dir':DEV,'build-cache':w/'ios-build-cache'}if pl=='ios'else{'project':w/'reply/Reply','java-home':JAVA,'android-sdk':SDK}
   assert fingerprint(w)==initial,'Changed source before native launch'
   queue=time.time();slot=R/'cache'/('slot-ios-'+simulator if pl=='ios'else'slot-android')
   slot.parent.mkdir(exist_ok=True,parents=True)
   with slot.open('a')as stream:
    fcntl.flock(stream,fcntl.LOCK_EX);queue_seconds=time.time()-queue
    gate.authorize(R/'gates',required_stage,R);verify_dir(scope);tool_verify();host_verify(w);assert fingerprint(w)==initial
    result=xp.run_execution(value,plan,lock,approval['design_lock_sha256'],fixture,bridge,out/pl/case,[w/rel for rel in ROOTS],native,policy=policy,policy_sha=approval['policy_sha256'])
   result=dict(result,case=case,platform=pl,queueSeconds=queue_seconds);outputs.append(result)
   save(out/pl/(case+'-result.json'),result)
   print(json.dumps({'phase':phase,'platform':pl,'case':case,'status':result['status'],'wall':result['finishedAtUnix']-result['startedAtUnix'],'queue':queue_seconds}),flush=True)
  return outputs
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(platform,['ios','android']))
 assert fingerprint(w)==initial,'Changed source during native acquisition'
 result={'phase':phase,'startedAtUnix':started,'finishedAtUnix':time.time(),'source':initial,'runs':[r for group in results for r in group]}
 save(out/'corpus.json',result);return result
