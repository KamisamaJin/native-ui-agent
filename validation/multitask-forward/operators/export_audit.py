#!/usr/bin/env python3
import importlib.util,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
spec=importlib.util.spec_from_file_location('export_inventory',R/'artifacts.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
paths=set(subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().strip('\0').split('\0'))|set(a.enumerate_files())
export=Path(tempfile.mkdtemp(prefix='native-ui-v7-export-'))
record={'startedAtUnix':time.time(),'exportDirectory':str(export),'files':len(paths),'commands':[],'scope':'SDK-free clean source export; caches excluded. No native rerun or evaluation changes.'}
for rel in sorted(paths):
 source=REPO/rel
 if source.is_file():target=export/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
commands=[['verify_tools.py'],['verify_trial.py'],['verify_evaluation.py'],['verify_claims.py'],['supplement.py','verify'],['supplement.py','metrics'],['review_product_summary.py'],['audit_grader_disagreements.py']]
commands += [['../publication_history.py',p,'artifacts.py']for p in ['state-v5','contract-v6']]
commands += [['../publication_history.py','dispatch-v4','verify_artifacts.py']]
out=R/'operators/export-audit';out.mkdir()
for i,args in enumerate(commands,1):
 argv=[sys.executable,'-B',str(export/'validation/multitask-forward'/args[0])]+args[1:];row={'argv':argv,'startedAtUnix':time.time(),'log':str((out/(str(i).zfill(2)+'.log')).relative_to(R))};record['commands'].append(row)
 with (R/row['log']).open('w')as f:row['exitCode']=subprocess.run(argv,cwd=export,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')).returncode
 row['finishedAtUnix']=time.time();(out/'commands.json').write_text(json.dumps(record,indent=2)+'\n');print(i,args,row['exitCode'],flush=True)
record['finishedAtUnix']=time.time();(out/'commands.json').write_text(json.dumps(record,indent=2)+'\n');print('EXPORT',export,flush=True)
assert all(x['exitCode']==0 for x in record['commands'])
