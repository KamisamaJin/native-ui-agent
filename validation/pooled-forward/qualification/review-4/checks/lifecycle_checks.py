from harness import *
import resource_manager as rm
from unittest.mock import patch

# All subprocesses inherit the non-forwarding simulated xcrun.
os.environ.update({k:v for k,v in ENV.items() if k in {'PATH','REVIEW_SIM_INVENTORY','PYTHONDONTWRITEBYTECODE'}})

def inventory():return d.load(Path(ENV['REVIEW_SIM_INVENTORY']))

def incompatible():
 base=project('pool-incompatible');v,r,o=command('runtime-one',base)
 first=d.load(o/'resources.json')['remaining_devices'][0]['udid']
 config_path=base/'ios'/'config.json';config=d.load(config_path);config['resources']['ios']['runtime']='SIMULATED.runtime2';save(config_path,config)
 v,r,o=command('runtime-two',base)
 row=d.load(o/'resources.json')['remaining_devices'][0]
 assert_that(row['udid']!=first,'incompatible runtime silently reused same device')
 inv=inventory();known=[x for x in inv['devices'] if x['udid'] in {first,row['udid']}]
 assert_that(len(known)==1 and known[0]['runtime']=='SIMULATED.runtime2','incompatible owned resource not retired first')
 cleanup(base,label='explicit-cleanup')
 return {'first_udid':first,'second_udid':row['udid'],'runtime':'SIMULATED.runtime2','resources':str(o/'resources.json')}
check('incompatible-runtime-retires-before-replacement',incompatible)

def expiry_boundaries():
 base=project('pool-boundaries',pool={'idle_seconds':1,'max_uses':2,'max_age_seconds':5})
 config=d.load(base/'ios'/'config.json');manager=rm.Resources(config,base/'evidence'/'unentered')
 wall=time.time();mono=time.monotonic();boot=rm.boot_identity()
 row={'pool_idle':True,'pool_key':'SIMULATED','boot_id':boot,'last_used_unix':wall,'last_used_monotonic':mono,'uses':1,'created_at_unix':wall,'created_monotonic':mono}
 outcomes={}
 for name,wd,md,uses,expected in [('before',.999,.999,1,True),('at-idle',1,1,1,False),('wall-backwards',-1,.1,1,False),('monotonic-backwards',.1,-1,1,False),('at-use-limit',.1,.1,2,False),('at-age',5,5,1,False)]:
  current=dict(row,uses=uses)
  with patch.object(rm.time,'time',return_value=wall+wd),patch.object(rm.time,'monotonic',return_value=mono+md):value=manager.reusable_device(current)
  outcomes[name]=value;assert_that(value is expected,'boundary differs '+name)
 return {'policy':{'idle_seconds':1,'max_uses':2,'max_age_seconds':5},'outcomes':outcomes}
check('pool-expiry-boundaries',expiry_boundaries)

def active_and_idle_expiry():
 base=project('pool-actual-clock-simulation',pool={'idle_seconds':1,'max_uses':12,'max_age_seconds':5})
 config=d.load(base/'ios'/'config.json');one=base/'evidence'/'lease-one'
 with rm.Resources(config,one) as manager:
  options=manager.native_options('ios');udid=options['simulator'];began=time.monotonic();time.sleep(1.25)
  assert_that(any(d['udid']==udid for d in inventory()['devices']),'guardian deleted active leased device after idle limit')
  assert_that(manager.native_options('ios')['simulator']==udid,'active repeated handle unexpectedly changed')
 active_seconds=time.monotonic()-began
 deadline=time.monotonic()+5
 while time.monotonic()<deadline and any(d['udid']==udid for d in inventory()['devices']):time.sleep(.05)
 assert_that(not any(d['udid']==udid for d in inventory()['devices']),'expired idle simulated device remained beyond bounded guardian sweep')
 two=base/'evidence'/'lease-two'
 with rm.Resources(config,two,final=True) as manager:new=manager.native_options('ios')['simulator']
 assert_that(new!=udid,'expired UUID was reacquired')
 assert_that(not any(d['udid']==new for d in inventory()['devices']),'final simulated device not removed')
 return {'first_udid':udid,'reacquired_udid':new,'active_crossing_seconds':active_seconds,'idle_retired':True,'lease_one_receipt':str(one/'resources.json'),'lease_two_receipt':str(two/'resources.json'),'limit':'Real host guardian/lock/clock; all inventory/create/delete replies SIMULATED'}
check('active-lease-crosses-expiry-idle-retirement-reacquires',active_and_idle_expiry)

def retire_failure():
 base=project('retirement-failure');command('original',base)
 v,r,o=command('final-delete-fails',base,extra=['--final'],expect=None,env_extra={'REVIEW_SIM_FAIL':'delete'})
 receipt=d.load(o/'resources.json')
 assert_that(r['exit_code']!=0 and not (o/'cycle.json').exists(),'cleanup failure published accepted cycle')
 assert_that(receipt['remaining_devices'] and receipt['cleanup_errors'],'required cleanup failure not retained')
 cleanup(base,label='bounded-cleanup-recovery')
 return {'resource_receipt':str(o/'resources.json'),'error':receipt['cleanup_errors'],'cycle_exists':False,'exit_code':r['exit_code']}
check('failed-retirement-blocks-acceptance',retire_failure)

def primary_and_cleanup():
 base=project('primary-cleanup-failure')
 v,r,o=command('primary-and-cleanup-fail',base,expect=None,env_extra={'REVIEW_SIM_FAIL':'delete','REVIEW_COLLECTOR_FAIL':'1'})
 receipt=d.load(o/'resources.json');error=d.load(o/'service-error.json')
 assert_that(receipt['primary_error']['message']=='SIMULATED primary collector failure' and receipt['cleanup_errors'],'primary/cleanup errors were not both retained')
 assert_that(error['message']=='SIMULATED primary collector failure' and not(o/'cycle.json').exists(),'primary failure hidden or accepted cycle published')
 cleanup(base,label='bounded-cleanup-recovery')
 return {'resource_receipt':str(o/'resources.json'),'service_error':error,'cleanup_errors':receipt['cleanup_errors']}
check('primary-error-and-cleanup-error-preserved',primary_and_cleanup)

def reuse_output():
 base=project('existing-output');command('first',base)
 first=base/'evidence'/'first';before={str(p.relative_to(first)):sha(p) for p in first.rglob('*') if p.is_file()}
 v,r,o=command('first',base,expect=2)
 after={str(p.relative_to(first)):sha(p) for p in first.rglob('*') if p.is_file()}
 assert_that(before==after,'reused output altered preserved original evidence')
 cleanup(base,label='explicit-cleanup')
 return {'original_files':len(before),'exit_code':r['exit_code']}
check('reused-output-preserves-evidence',reuse_output)

save(ROOT/'raw'/'lifecycle-results.json',RESULTS)
