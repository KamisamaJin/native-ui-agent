from support import *
import argparse,subprocess
import resource_manager as rm
p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--ready');p.add_argument('--child-ready');a=p.parse_args()
config=d.load(Path(a.config));output=Path(a.output)
with rm.Resources(config,output,final=a.mode in {'cleanup','timeout','managed'}) as manager:
 scratch=manager.directory('owned-private')
 (scratch/'owned-sentinel.txt').write_text('private disposable host sentinel\n')
 if a.ready:Path(a.ready).write_text(json.dumps({'manager_pid':os.getpid(),'root':str(manager.root),'owner_token':manager.identity['token']})+'\n')
 if a.mode=='hold':time.sleep(120)
 elif a.mode in {'managed','timeout'}:
  raw='from pathlib import Path; import os,time; Path('+repr(a.child_ready)+').write_text(str(os.getpid())); time.sleep(120)'
  with (output.parent/(output.name+'-host-command.log')).open('w') as stream:
   manager.run([sys.executable,'-B','-c',raw],env=dict(os.environ),stdout=stream,timeout=.6 if a.mode=='timeout' else 120)
