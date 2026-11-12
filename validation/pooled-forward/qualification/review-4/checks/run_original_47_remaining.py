from support import *
import subprocess
scripts=['extended_checks.py','host_checks.py','lifecycle_checks.py','source_checks.py','focused_checks.py','layer_checks.py','coverage_checks.py']
results=[]
for script in scripts:
 argv=[sys.executable,'-B',str(ROOT/'checks'/script)]
 at=time.time();start=time.monotonic();r=subprocess.run(argv,env=dict(os.environ,REVIEW_CANDIDATE=str(CANDIDATE),PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=80)
 value={'script':script,'argv':argv,'started_at_unix':at,'finished_at_unix':time.time(),'started_monotonic':start,'finished_monotonic':time.monotonic(),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 save(ROOT/'raw'/(script+'.stage-command.json'),value);results.append(value)
 print(script+': exit '+str(r.returncode)+'\n'+r.stdout+r.stderr,flush=True)
save(ROOT/'raw'/'original-47-stage-commands.json',results)
