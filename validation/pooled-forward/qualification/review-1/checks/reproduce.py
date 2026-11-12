"""Rerun these checks only in a fresh owned child of this review's work directory."""
from support import *
import argparse,subprocess,shutil
p=argparse.ArgumentParser();p.add_argument('--suite',choices=['initial','extended','host','source','layer','coverage'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
target=a.output.absolute()
if not target.is_relative_to(ROOT/'work') or target==ROOT/'work':raise ValueError('Fresh positively owned output beneath review-1/work is required')
target.mkdir(parents=True,exist_ok=False)
save(target/'OWNERSHIP.json',{'owner':'review-1-independent-reproduction','token':uuid.uuid4().hex,'parent_review':str(ROOT),'candidate':str(CANDIDATE),'native_commands_authorized':False})
for name in ['work','raw','first-failures']:(target/name).mkdir()
shutil.copytree(ROOT/'checks',target/'checks')
script={'initial':'run_checks.py','extended':'extended_checks.py','host':'host_checks.py','source':'source_checks.py','layer':'layer_checks.py','coverage':'coverage_checks.py'}[a.suite]
env=dict(os.environ,REVIEW_CANDIDATE=str(CANDIDATE),PYTHONDONTWRITEBYTECODE='1')
argv=[sys.executable,'-B',str(target/'checks'/script)];started=time.time()
r=subprocess.run(argv,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120)
save(target/'raw'/'reproduction-command.json',{'argv':argv,'at_unix':started,'finished_at_unix':time.time(),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'evidence_class':'HOST/SIMULATED only'})
print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr);print(str(target))
raise SystemExit(r.returncode)
