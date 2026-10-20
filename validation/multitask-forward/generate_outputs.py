#!/usr/bin/env python3
"""Write derived publication outputs once, after both all-task reveal barriers."""
import subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
ex.gate.verify(R/'gates','reveal',R);ex.gate.verify(R/'shared-environment-v1/gates','graded',R)
path=R/'operators/output-generation.json';assert not path.exists();record={'startedAtUnix':time.time(),'steps':[]};ex.save(path,record)
commands=[['metrics.py','--write'],['quality_breakdown.py','--write'],['pair_metrics.py','--write'],['costs.py','--write'],['observation_costs.py','--write'],['failure_index.py','--write'],['supplement.py','metrics','--write'],['review_product_summary.py','--write'],['implementation_comparison.py','--write'],['build_tables.py','--write'],['build_supplement_tables.py','--write'],['build_gallery.py','--write']]
for args in commands:
 row={'argv':[sys.executable,'-B',str(R/args[0])]+args[1:],'startedAtUnix':time.time()};record['steps'].append(row);ex.save(path,record);log=R/'operators'/('output-'+args[0]+'.log');assert not log.exists()
 with log.open('w')as stream:row['exitCode']=subprocess.run(row['argv'],stdout=stream,stderr=subprocess.STDOUT).returncode
 row['finishedAtUnix']=time.time();ex.save(path,record);print(args[0],row['exitCode'],flush=True)
 if row['exitCode']!=0:raise RuntimeError('Preserve failed output attempt; do not overwrite or bypass')
record['finishedAtUnix']=time.time();ex.save(path,record)
