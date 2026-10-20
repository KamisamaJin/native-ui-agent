#!/usr/bin/env python3
"""Guarded post-common-FINAL delivery and actual paired SDK continuation."""
import subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
record={'startedAtUnix':time.time(),'steps':[]};path=R/'operators/post-common.json';assert not path.exists();ex.save(path,record)
while not(R/'operators/common-FINAL-batch.json').is_file():
 if time.time()-record['startedAtUnix']>7200:raise RuntimeError('Common FINAL cohort did not finish')
 time.sleep(1)
for args in [['seal_delivery.py','FINAL'],['prepare_evaluator_prompts.py','FINAL']]:
 row={'argv':[sys.executable,'-B',str(R/args[0])]+args[1:],'startedAtUnix':time.time()};record['steps'].append(row);ex.save(path,record)
 log=R/'operators'/('post-common-'+args[0]+'.log');assert not log.exists()
 with log.open('w')as stream:row['exitCode']=subprocess.run(row['argv'],stdout=stream,stderr=subprocess.STDOUT).returncode
 row['finishedAtUnix']=time.time();ex.save(path,record);assert row['exitCode']==0
record['FINALPromptsReadyAtUnix']=time.time();ex.save(path,record);print('Complete common FINAL delivered; all FINAL prompts ready.',flush=True)
code=subprocess.run([sys.executable,'-B',str(R/'run_batch.py'),'paired-D0']).returncode
record.update(finishedAtUnix=time.time(),pairedBatchExitCode=code);ex.save(path,record);assert code==0
