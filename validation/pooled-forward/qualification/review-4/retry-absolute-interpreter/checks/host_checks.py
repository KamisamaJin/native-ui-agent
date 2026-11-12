from harness import *
import signal,fcntl
import resource_manager as rm

def host_project(name):
 base=ROOT/'work'/name;base.mkdir(exist_ok=False)
 source=base/'production';source.mkdir();(source/'source.txt').write_text('protected production source\n')
 borrowed=base/'borrowed-build';borrowed.mkdir();(borrowed/'sentinel.txt').write_text('preserved borrowed host artifact\n')
 config={'source_roots':[str(source)],'native_options':{'build-cache':str(borrowed)},'resources':{'root':str(base/'scratch'),'min_free_bytes':0,'pool':False,'sample_seconds':.1}}
 save(base/'config.json',config)
 return base

def wait_path(path):
 deadline=time.monotonic()+8
 while not Path(path).exists() and time.monotonic()<deadline:time.sleep(.02)
 assert_that(Path(path).exists(),'private helper did not reach checkpoint '+str(path))

def host_cmd(base,label,mode,*,spawn=False,child_ready=None):
 out=base/'evidence'/label;out.parent.mkdir(parents=True,exist_ok=True)
 argv=[sys.executable,'-B',str(ROOT/'checks'/'host_helper.py'),mode,'--config',str(base/'config.json'),'--output',str(out),'--ready',str(base/(label+'.ready'))]
 if child_ready:argv+=['--child-ready',str(child_ready)]
 if spawn:
  p=subprocess.Popen(argv,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  return p,argv,out
 at=time.time();start=time.monotonic();p=subprocess.run(argv,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=12)
 save(ROOT/'raw'/(base.name+'--'+label+'.host.json'),{'evidence_class':'HOST','argv':argv,'start_unix':at,'end_unix':time.time(),'start_monotonic':start,'end_monotonic':time.monotonic(),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 return p,argv,out

def host_locks():
 base=host_project('host-locks');other=host_project('host-locks-other-owner')
 owner,argv,out=host_cmd(base,'owner','hold',spawn=True);wait_path(base/'owner.ready')
 try:
  contender,_,co=host_cmd(base,'contender','cleanup')
  assert_that(contender.returncode!=0 and 'lease is active' in contender.stderr,'same-root active lease did not refuse contender')
  separate,_,so=host_cmd(other,'other-owner','cleanup')
  assert_that(separate.returncode==0,'separate private owner was blocked')
  assert_that(owner.poll() is None,'contender or other owner killed live lease')
 finally:
  owner.kill();stdout,stderr=owner.communicate(timeout=6)
  save(ROOT/'raw'/'host-locks-owner-interruption.json',{'evidence_class':'HOST','argv':argv,'pid':owner.pid,'signal':'SIGKILL','exit_code':owner.returncode,'stdout':stdout,'stderr':stderr,'ready':d.load(base/'owner.ready')})
 r,_,ro=host_cmd(base,'reconcile','cleanup')
 assert_that(r.returncode==0,'stale host lease failed to reconcile')
 return {'same_root_contender_exit':contender.returncode,'separate_owner_exit':separate.returncode,'reconcile_receipt':str(ro/'resources.json')}
check('real-host-lock-exclusion-and-owner-independence',host_locks,'HOST')

def host_timeout():
 base=host_project('host-timeout');before=sha(base/'borrowed-build'/'sentinel.txt')
 p,argv,out=host_cmd(base,'timeout','timeout',child_ready=base/'child.ready')
 receipt=d.load(out/'resources.json')
 assert_that(p.returncode!=0 and receipt['primary_error']['type']=='TimeoutExpired','managed host timeout did not preserve primary error')
 assert_that(not receipt['remaining_devices'] and not receipt['remaining_directories'],'timeout left disposable resources')
 assert_that(before==sha(base/'borrowed-build'/'sentinel.txt'),'borrowed host path was deleted or modified')
 return {'receipt':str(out/'resources.json'),'primary_error':receipt['primary_error'],'borrowed_sha256':before}
check('owned-host-command-timeout-and-borrowed-preservation',host_timeout,'HOST')

def host_interruption():
 base=host_project('host-interruption');ready=base/'command-child.ready'
 owner,argv,out=host_cmd(base,'interrupted-manager','managed',spawn=True,child_ready=ready)
 wait_path(ready)
 journal=d.load(base/'scratch'/'journal.json');tracked=journal['process'];child_pid=int(ready.read_text())
 # Own helper launched this token-bearing group and its private child.
 assert_that(tracked['argv'][0]==sys.executable and str(ready) in tracked['argv'][-1],'not a positively identified private command')
 process_before=subprocess.run(['ps','-ww','-p',str(tracked['pid'])+','+str(child_pid),'-o','pid=,pgid=,lstart=,command='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 owner.kill();stdout,stderr=owner.communicate(timeout=6)
 save(ROOT/'raw'/'host-interrupted-original.json',{'evidence_class':'HOST','manager_argv':argv,'manager_pid':owner.pid,'signal':'SIGKILL','manager_exit':owner.returncode,'stdout':stdout,'stderr':stderr,'journal_process_before_kill':tracked,'raw_processes_before':process_before.stdout,'child_pid':child_pid})
 p,_,recovery=host_cmd(base,'recovery','cleanup')
 after=subprocess.run(['ps','-ww','-p',str(tracked['pid'])+','+str(child_pid),'-o','pid=,pgid=,state=,command='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 save(ROOT/'raw'/'host-interrupted-recovery-processes.json',{'evidence_class':'HOST','exit_code':after.returncode,'stdout':after.stdout,'stderr':after.stderr})
 assert_that(p.returncode==0,'private process reconciliation failed: '+p.stderr)
 rows=[line.split() for line in after.stdout.splitlines()]
 assert_that(all(len(r)>2 and r[2].startswith('Z') for r in rows),'a private command remains alive after reconciliation')
 receipt=d.load(recovery/'resources.json')
 assert_that(not receipt['remaining_directories'],'recovered private scratch remained')
 return {'recovery_receipt':str(recovery/'resources.json'),'event_log':str(recovery/'resource-events.jsonl'),'tracked_pid':tracked['pid'],'child_pid':child_pid,'post_process_output':after.stdout}
check('interrupted-private-host-command-reconciles',host_interruption,'HOST')

def copied_root():
 base=host_project('host-copied-root');p,_,out=host_cmd(base,'original','inspect')
 assert_that(p.returncode==0,'original root failed')
 copied=base/'copied-scratch';shutil.copytree(base/'scratch',copied)
 config=d.load(base/'config.json');config['resources']['root']=str(copied);save(base/'config.json',config)
 before=sha(copied/'owned-private'/'owned-sentinel.txt')
 p,_,out=host_cmd(base,'copied-root-cleanup','cleanup')
 assert_that(p.returncode!=0 and 'Owned root was replaced' in p.stderr,'copied resource journal was adopted')
 assert_that(before==sha(copied/'owned-private'/'owned-sentinel.txt'),'copied root was deleted after identity rejection')
 return {'raw':str(ROOT/'raw'/(base.name+'--copied-root-cleanup.host.json')),'preserved_sha256':before}
check('copied-resource-journal-root-rejected',copied_root,'HOST')

save(ROOT/'raw'/'host-results.json',RESULTS)
