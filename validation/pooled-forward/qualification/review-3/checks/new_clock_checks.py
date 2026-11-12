from harness import *
import resource_manager as rm
import fcntl
from unittest.mock import patch
os.environ.update(PATH=str(ROOT/'checks'/'bin')+os.pathsep+os.environ['PATH'],REVIEW_SIM_INVENTORY=str(ROOT/'work'/'simulated-inventory.json'),PYTHONDONTWRITEBYTECODE='1')

def locked_inventory():
 path=Path(ENV['REVIEW_SIM_INVENTORY'])
 with path.with_suffix('.lock').open('a')as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_SH)
  return d.load(path)

def kernel_shared():
 argv=[sys.executable,'-B','-c','import sys,json,time; sys.path.insert(0,'+repr(str(CANDIDATE/'scripts'))+'); import resource_manager as r; print(json.dumps({"lease_clock":r.lease_clock(),"boot_id":r.boot_identity(),"python_monotonic":time.monotonic(),"version":sys.version}))']
 before=rm.lease_clock();time.sleep(.2);r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5);after=rm.lease_clock();child=json.loads(r.stdout)
 detail={'evidence_class':'HOST','argv':argv,'before':before,'after':after,'child':child,'exit_code':r.returncode,'stderr':r.stderr,'host_boot_id':rm.boot_identity()}
 save(ROOT/'raw'/'kernel-clock-cross-process.json',detail)
 assert_that(before<=child['lease_clock']<=after and child['boot_id']==detail['host_boot_id'],'lease clock/provider is not shared across independent processes')
 return detail
check('N08-kernel-clock-shared-across-processes',kernel_shared,'HOST')

def expiry():
 base=project('new-kernel-boundaries',pool={'idle_seconds':1,'max_uses':2,'max_age_seconds':5});config=d.load(base/'ios'/'config.json');m=rm.Resources(config,base/'evidence'/'unentered')
 wall=time.time();kernel=rm.lease_clock();row={'pool_idle':True,'pool_key':'SIMULATED','boot_id':rm.boot_identity(),'last_used_unix':wall,'last_used_monotonic':kernel,'uses':1,'created_at_unix':wall,'created_monotonic':kernel}
 outcomes={}
 for name,wd,kd,uses,expected in [('before',.999,.999,1,True),('at-idle',1,1,1,False),('wall-backwards',-1,.1,1,False),('kernel-backwards',.1,-1,1,False),('at-use-limit',.1,.1,2,False),('at-age',5,5,1,False)]:
  with patch.object(rm.time,'time',return_value=wall+wd),patch.object(rm,'lease_clock',return_value=kernel+kd):actual=m.reusable_device(dict(row,uses=uses))
  outcomes[name]=actual;assert_that(actual is expected,'shared-clock boundary differs '+name)
 return {'outcomes':outcomes,'clock_provider':'actual emitted journal timestamps use resource_manager.lease_clock; this supplied decision control mocks that same provider','policy':{'idle_seconds':1,'max_uses':2,'max_age_seconds':5}}
check('N09-expiry-using-shared-lease-clock',expiry)

def active_idle_durable():
 base=project('new-active-idle-clock',pool={'idle_seconds':1,'max_uses':12,'max_age_seconds':5});config=d.load(base/'ios'/'config.json');one=base/'evidence'/'lease-one'
 with rm.Resources(config,one)as m:
  udid=m.native_options('ios')['simulator'];start={'wall':time.time(),'lease_clock':rm.lease_clock()};time.sleep(1.25)
  held={'wall':time.time(),'lease_clock':rm.lease_clock(),'simulated_inventory':locked_inventory()['devices']}
  assert_that(any(r['udid']==udid for r in held['simulated_inventory']),'guardian deleted active lease')
  assert_that(m.native_options('ios')['simulator']==udid,'active handle was replaced')
 save(ROOT/'raw'/'active-lease-clock-crossing.json',{'evidence_class':'HOST clock/lock with SIMULATED inventory','start':start,'after_crossing':held,'udid':udid})
 root=Path(config['resources']['root']);deadline=time.monotonic()+6;retirement=None;journal=None
 while time.monotonic()<deadline:
  receipts=list(one.glob('pool-retirement-*/resources.json'))
  with (root/'lease.lock').open('a')as stream:
   try:fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:pass
   else:
    state=d.load(root/'journal.json')
    if receipts and not state.get('devices')and not state.get('pool_watch')and not state.get('lease'):
     retirement=receipts[0];journal=state
    fcntl.flock(stream.fileno(),fcntl.LOCK_UN)
  if retirement:break
  time.sleep(.05)
 assert_that(retirement is not None,'idle guardian did not durably retire within bound')
 two=base/'evidence'/'lease-two'
 with rm.Resources(config,two,final=True)as m:new_udid=m.native_options('ios')['simulator']
 assert_that(new_udid!=udid and not any(r['udid']in{udid,new_udid}for r in locked_inventory()['devices']),'expired identity reused or final retirement incomplete')
 return {'first_udid':udid,'new_udid':new_udid,'active_crossing_seconds':held['lease_clock']-start['lease_clock'],'retirement_receipt':str(retirement),'retirement_generation':journal['generation'],'new_final_receipt':str(two/'resources.json'),'limit':'All device replies SIMULATED; actual HOST guardian lock and kernel clock were exercised.'}
check('N10-active-idle-expiry-after-durable-retirement',active_idle_durable)

def fresh_intake():
 base=project('new-fresh-intake')
 value,record,out=command('incompatible-fresh-intake',base,extra=['--fresh','--intake'],expect=2)
 assert_that(not value and record['simulated_collection_count']==0,'fresh/intake combination was silently allowed')
 cleanup(base,label='explicit-cleanup')
 return {'command':str(ROOT/'raw'/(base.name+'--incompatible-fresh-intake.command.json')),'stderr':record['stderr'],'collector_count':0}
check('N11-explicit-fresh-rejects-diagnostic-intake',fresh_intake)
save(ROOT/'raw'/'new-clock-results.json',RESULTS)
