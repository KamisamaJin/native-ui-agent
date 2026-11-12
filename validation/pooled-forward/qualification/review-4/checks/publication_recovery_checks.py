from review3_support import *
from harness import check,assert_that,RESULTS
import signal,tarfile

def interrupted_request(base,stage):
 out=base/'evidence'/'interrupted-original-final';config=base/'ios'/'config.json';marker=ROOT/'raw'/(base.name+'-stopped-marker.json');token=uuid.uuid4().hex
 argv=[sys.executable,'-B',str(ROOT/'checks'/'publication_cli.py'),'native','--config',str(config),'--output',str(out),'--final']
 env=dict(os.environ,REVIEW_CANDIDATE=str(CANDIDATE),REVIEW_CONFIG=str(config),REVIEW_PUBLICATION_STAGE=stage,REVIEW_PUBLICATION_MARKER=str(marker),REVIEW_PUBLICATION_TOKEN=token,REVIEW_SIM_INVENTORY=str(ROOT/'work'/'simulated-inventory.json'),PATH=str(ROOT/'checks'/'bin')+os.pathsep+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1')
 before=attempts();wall=time.time();mono=time.monotonic();p=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
 process_output=[];snapshot=None
 try:
  deadline=time.monotonic()+12
  while not marker.exists()and p.poll()is None and time.monotonic()<deadline:time.sleep(.01)
  assert_that(marker.exists(),'owned publisher never reached requested observable boundary')
  stopped=d.load(marker);assert_that(stopped['pid']==p.pid and stopped['pgid']==p.pid and stopped['token']==token,'publisher stop marker is foreign')
  deadline=time.monotonic()+3;observed_stop=False
  ps_argv=['ps','-ww','-p',str(p.pid),'-o','pid=,pgid=,state=,lstart=,command=']
  while time.monotonic()<deadline:
   query=subprocess.run(ps_argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=3);process_output.append({'argv':ps_argv,'exit_code':query.returncode,'stdout':query.stdout,'stderr':query.stderr});fields=query.stdout.split()
   if len(fields)>=3 and fields[0]==str(p.pid)and fields[1]==str(p.pid)and fields[2].startswith('T')and str(ROOT/'checks'/'publication_cli.py')in query.stdout:observed_stop=True;break
   time.sleep(.02)
  assert_that(observed_stop,'publisher was not independently observed stopped in its own group')
  payload=out/'cycle-payload.json';cycle=out/'cycle.json';checkpoint=base/'workflow'/'ios.json';on_disk=d.load(checkpoint)if checkpoint.exists()else None;backup=base/'workflow'/'ios-backup.json';back=d.load(backup)if backup.exists()else None
  resource=d.load(out/'resources.json');capture=out/'capture'/'result.json';receipt=d.load(capture)
  snapshot={'evidence_class':'HOST observed filesystem/process at supplied fault point; collector SIMULATED','stage':stage,'stop':stopped,'raw_processes':process_output,'payload':{'path':str(payload),'sha256':sha(payload),'status':d.load(payload)['status']},'cycle_exists':cycle.exists(),'cycle_sha256':sha(cycle)if cycle.exists()else None,'checkpoint':on_disk,'backup':back,'capture':{'path':str(capture),'sha256':sha(capture)},'resource_receipt':{'path':str(out/'resources.json'),'sha256':sha(out/'resources.json'),'remaining_devices':resource['remaining_devices'],'remaining_directories':resource['remaining_directories'],'cleanup_errors':resource['cleanup_errors']},'source_file_sha256':sha(base/'production'/'ios'/'Component.swift')}
  save(ROOT/'raw'/(base.name+'-observed-before-sigkill.json'),snapshot)
  assert_that(resource['final']and not resource['remaining_devices']and not resource['remaining_directories']and not resource['cleanup_errors'],'accepted payload preceded required resource closure')
  assert_that(receipt['status']=='verified_capture'and snapshot['payload']['status']=='accepted','publication precondition is not a complete controlled final packet')
  if stage=='payload':assert_that(not cycle.exists()and not(on_disk or{}).get('pending_publish'),'cycle exposed before durable publish checkpoint')
  else:
   assert_that(on_disk and back and on_disk['pending_publish']==back['pending_publish'],'publish transaction was not durable in both checkpoints')
   transaction=on_disk['pending_publish'];assert_that(transaction['payload']['sha256']==sha(payload)and transaction['cycle']['sha256']==sha(payload),'transaction does not bind exact payload bytes')
   for ref in transaction['files']:assert_that(sha(Path(ref['path']))==ref['sha256'],'publication dependency is not actually pinned')
   assert_that(cycle.exists()==(stage=='cycle'),'cycle appeared at wrong observed publication stage')
   if cycle.exists():assert_that(sha(cycle)==sha(payload),'published bytes differ from staged payload')
 finally:
  if p.poll()is None:p.kill()
  stdout,stderr=p.communicate(timeout=6)
  save(ROOT/'raw'/(base.name+'--interrupted-publication.public-command.json'),{'evidence_class':'HOST SIGSTOP/SIGKILL at SIMULATED placement checkpoint; no native execution','argv':argv,'pid':p.pid,'pgid':p.pid,'token':token,'start_unix':wall,'end_unix':time.time(),'start_monotonic':mono,'end_monotonic':time.monotonic(),'exit_code':p.returncode,'termination':'SIGKILL of own positively identified stopped Popen child','stdout':stdout,'stderr':stderr,'boundary_attempts':attempts()-before,'raw_process_queries':process_output})
 return out,snapshot

def recover_stage(stage):
 base=project('r3-publication-'+stage);original,snapshot=interrupted_request(base,stage);payload_sha=snapshot['payload']['sha256'];capture_sha=snapshot['capture']['sha256'];component_sha=snapshot['source_file_sha256']
 before_files={str(p.relative_to(original)):sha(p)for p in original.rglob('*')if p.is_file()}
 value,raw,recovered=invoke(base,'normal-default-reentry',expect=0)
 assert_that((recovered/'cycle.json').exists(),'normal default did not publish its completed recovery result')
 if stage=='payload':
  assert_that(not(original/'cycle.json').exists()and raw['boundary_attempts']==1,'unregistered orphan payload was promoted or no new collection occurred')
 else:
  assert_that((original/'cycle.json').exists()and sha(original/'cycle.json')==payload_sha and raw['boundary_attempts']==0,'durable original transaction did not recover exact bytes without recollection')
  s=state(base);assert_that(not s.get('pending_publish'),'pending publish did not close')
  assert_that(sum(r['cycle']['path']==str(original/'cycle.json')for r in s['cycles'])==1,'original cycle row was duplicated during recovery')
 assert_that(sha(original/'capture'/'result.json')==capture_sha and sha(base/'production'/'ios'/'Component.swift')==component_sha,'recovery rewrote original capture or production bytes')
 for relative,digest in before_files.items():assert_that(sha(original/relative)==digest,'recovery altered original '+relative)
 value,raw,again=invoke(base,'idempotent-default-inspection',expect=0)
 assert_that(raw['boundary_attempts']==0,'repeated inspection recollected or re-ran publication work')
 value,raw,final=invoke(base,'ordinary-final-after-publication-recovery',extra=['--final'],expect=0)
 assert_that(value['status']=='accepted'and value['capture_reused']and raw['boundary_attempts']==0,'recovered complete current packet could not finish normal gates')
 return {'fault_stage':stage,'original_payload':str(original/'cycle-payload.json'),'original_payload_sha256':payload_sha,'original_cycle_exists_after_recovery':(original/'cycle.json').exists(),'original_capture_sha256':capture_sha,'recovery_command':str(ROOT/'raw'/(base.name+'--normal-default-reentry.public-command.json')),'recovery_attempts':d.load(ROOT/'raw'/(base.name+'--normal-default-reentry.public-command.json'))['boundary_attempts'],'final_cycle':str(final/'cycle.json'),'evidence_limit':'Actual owned-process termination, locks, checkpoint bytes and file publication; fault placement and native packet are SIMULATED.'}
check('R05-host-publication-before-checkpoint',lambda:recover_stage('payload'),'HOST/SIMULATED')
check('R06-host-publication-after-checkpoint',lambda:recover_stage('checkpoint'),'HOST/SIMULATED')
check('R07-host-publication-after-cycle-before-clear',lambda:recover_stage('cycle'),'HOST/SIMULATED')

def corrupt_pending():
 base=project('r3-publication-corrupt');original,snapshot=interrupted_request(base,'checkpoint');handoff=original/'handoff.json';old=handoff.read_bytes();original_pin=save(ROOT/'raw'/'publication-corrupt-original-handoff.json',d.load(handoff));before_state=(base/'workflow'/'ios.json').read_bytes();source_sha=sha(base/'production'/'ios'/'Component.swift');archive=ROOT/'raw'/'publication-corrupt-pristine-evidence.tar'
 with tarfile.open(archive,'x')as tf:tf.add(original,arcname='interrupted-original-final')
 altered=d.load(handoff);altered['capture']['sha256']='0'*64;save(handoff,altered);save(ROOT/'raw'/'publication-corrupt-mutation.json',{'path':str(handoff),'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':sha(handoff),'original_bytes':str(original_pin),'pristine_archive':str(archive),'pristine_archive_sha256':sha(archive)})
 value,raw,reentry=invoke(base,'normal-reentry-with-corrupt-handoff')
 assert_that(raw['exit_code']!=0 and raw['boundary_attempts']==0 and not(original/'cycle.json').exists()and not(reentry/'cycle.json').exists(),'corrupt publish transaction created accepted/public cycle or launched a collector')
 assert_that((base/'workflow'/'ios.json').read_bytes()==before_state and sha(base/'production'/'ios'/'Component.swift')==source_sha,'failed recovery mutated pending proof or production')
 invoke(base,'explicit-owned-resource-cleanup',action='cleanup-native-resources',expect=0)
 return {'reentry_command':str(ROOT/'raw'/(base.name+'--normal-reentry-with-corrupt-handoff.public-command.json')),'stderr':raw['stderr'],'mutation':'raw/publication-corrupt-mutation.json','cycle_still_absent':True,'pending_checkpoint_preserved':True,'evidence_limit':'HOST interruption/rejection with SIMULATED native packet; intentionally altered transaction preserved.'}
check('R08-host-publication-corruption-rejects',corrupt_pending,'HOST/SIMULATED')
save(ROOT/'raw'/'review-3-publication-results.json',RESULTS)
