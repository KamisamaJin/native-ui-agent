from support import *
import subprocess
scripts=['run_checks.py','extended_checks.py','host_checks.py','lifecycle_checks.py','source_checks.py','focused_checks.py','layer_checks.py','coverage_checks.py','new_default_context_checks.py','new_clock_checks.py']
rows=[]
for script in scripts:
 argv=[sys.executable,'-B',str(ROOT/'checks'/script)];wall=time.time();mono=time.monotonic()
 p=subprocess.run(argv,env=dict(os.environ,REVIEW_CANDIDATE=str(CANDIDATE),PYTHONDONTWRITEBYTECODE='1'),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=100)
 row={'argv':argv,'script':script,'started_at_unix':wall,'finished_at_unix':time.time(),'started_monotonic':mono,'finished_monotonic':time.monotonic(),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 save(ROOT/'raw'/(script+'.stage-command.json'),row);rows.append(row)
 print(script+': '+str(p.returncode)+'\n'+p.stdout+p.stderr,flush=True)
save(ROOT/'raw'/'original-58-stage-commands.json',rows)
