# Fault placement is SIMULATED; pause/termination/files/locks are actual HOST behavior.
from review3_support import *
import signal,runpy
import resource_manager,workflow_state,feedback_loop
resource_manager.Resources.run=recording_collector
stage=os.environ['REVIEW_PUBLICATION_STAGE'];marker=Path(os.environ['REVIEW_PUBLICATION_MARKER']);token=os.environ['REVIEW_PUBLICATION_TOKEN'];seen={}
if not marker.is_relative_to(ROOT/'raw'):raise ValueError('Private marker root required')
def stop_here(point,metadata):
 save(marker,{'evidence_class':'HOST pause at SIMULATED fault-placement checkpoint','pid':os.getpid(),'pgid':os.getpgrp(),'token':token,'point':point,'metadata':metadata,'at_unix':time.time()})
 os.kill(os.getpid(),signal.SIGSTOP)
 # The qualification parent always SIGKILLs its positively identified stopped child.
 while True:time.sleep(1)
old_write=feedback_loop.write
def watched_write(path,value):
 result=old_write(path,value)
 if stage=='payload'and Path(path).name=='cycle-payload.json':stop_here('payload-written-before-durable-publish',{'payload_path':str(Path(path).resolve()),'payload_sha256':sha(path)})
 return result
feedback_loop.write=watched_write
old_checkpoint=workflow_state.Session.checkpoint
def watched_checkpoint(self):
 key=str(self.root)
 if stage=='cycle'and key in seen and not self.state.get('pending_publish'):
  transaction=seen[key];cycle=Path(transaction['cycle']['path'])
  if cycle.exists():stop_here('cycle-written-before-cleared-checkpoint',{'root':key,'cycle_path':str(cycle),'cycle_sha256':sha(cycle),'transaction':transaction})
 result=old_checkpoint(self)
 if self.state.get('pending_publish'):
  seen[key]=json.loads(json.dumps(self.state['pending_publish']))
  if stage=='checkpoint':stop_here('durable-publish-checkpoint-before-cycle',{'root':key,'generation':self.state['generation'],'transaction':self.state['pending_publish']})
 return result
workflow_state.Session.checkpoint=watched_checkpoint
sys.argv=[str(CANDIDATE/'scripts'/'ui_loop.py'),*sys.argv[1:]]
runpy.run_path(str(CANDIDATE/'scripts'/'ui_loop.py'),run_name='__main__')
