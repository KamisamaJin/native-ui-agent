#!/usr/bin/env python3
import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
out=R/'operators/final-audit';out.mkdir()
commands=[['verify_tools.py'],['verify_generic.py'],['design-v2/T1/private/test_grader.py'],['design-v2/T2/private/test_grader.py'],['design-v2/T3/private/test_grader.py'],['verify_trial.py'],['verify_evaluation.py'],['verify_claims.py'],['test_metrics.py'],['metrics.py'],['quality_breakdown.py'],['pair_metrics.py'],['costs.py'],['observation_costs.py'],['failure_index.py'],['build_tables.py'],['build_gallery.py'],['test_shared_environment.py'],['supplement.py','verify'],['supplement.py','metrics'],['build_supplement_tables.py'],['implementation_comparison.py'],['review_product_summary.py'],['audit_grader_disagreements.py']]
record={'startedAtUnix':time.time(),'commands':[]}
for i,args in enumerate(commands,1):
 argv=[sys.executable,'-B',str(R/args[0])]+args[1:];row={'argv':argv,'startedAtUnix':time.time(),'log':str((out/(str(i).zfill(2)+'.log')).relative_to(R))};record['commands'].append(row)
 with (R/row['log']).open('w')as f:row['exitCode']=subprocess.run(argv,cwd=REPO,stdout=f,stderr=subprocess.STDOUT).returncode
 row['finishedAtUnix']=time.time();(out/'commands.json').write_text(json.dumps(record,indent=2)+'\n');print(i,args,row['exitCode'],flush=True)
record['finishedAtUnix']=time.time();(out/'commands.json').write_text(json.dumps(record,indent=2)+'\n')
assert all(x['exitCode']==0 for x in record['commands'])
