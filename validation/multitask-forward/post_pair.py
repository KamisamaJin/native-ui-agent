#!/usr/bin/env python3
"""Deliver actual same-source pair only after all six native corpora complete."""
import subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
path=R/'operators/post-pair.json';assert not path.exists();record={'startedAtUnix':time.time(),'steps':[]};ex.save(path,record)
while not(R/'operators/paired-D0-batch.json').is_file():
 if time.time()-record['startedAtUnix']>7200:raise RuntimeError('Complete actual native pair did not finish')
 time.sleep(1)
for args in [['prepare_pair_delivery.py'],['prepare_evaluator_prompts.py','paired-D0']]:
 row={'argv':[sys.executable,'-B',str(R/args[0])]+args[1:],'startedAtUnix':time.time()};record['steps'].append(row);ex.save(path,record);log=R/'operators'/('post-pair-'+args[0]+'.log');assert not log.exists()
 with log.open('w')as stream:row['exitCode']=subprocess.run(row['argv'],stdout=stream,stderr=subprocess.STDOUT).returncode
 row['finishedAtUnix']=time.time();ex.save(path,record);assert row['exitCode']==0
record['finishedAtUnix']=time.time();ex.save(path,record);print('All-six actual native pair and original claim review sealed; paired-D0 prompts ready.',flush=True)
