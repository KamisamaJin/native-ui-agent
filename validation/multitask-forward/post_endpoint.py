#!/usr/bin/env python3
"""One-shot guarded continuation of this already authorized live experiment."""
import subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def main():
 start=time.time();record={'startedAtUnix':start,'steps':[]};path=R/'operators/post-endpoint.json';assert not path.exists();ex.save(path,record)
 while not(R/'operators/own-FINAL-batch.json').is_file():
  if time.time()-start>7200:raise RuntimeError('Public final batch did not finish; no downstream SDK authorized')
  time.sleep(1)
 commands=[['close_own.py','final'],['materialize_hidden.py'],['seal_delivery.py','D0'],['prepare_evaluator_prompts.py','D0']]
 for args in commands:
  row={'argv':[sys.executable,'-B',str(R/args[0])]+args[1:],'startedAtUnix':time.time()};record['steps'].append(row);ex.save(path,record)
  log=R/'operators'/('post-endpoint-'+args[0]+'.log');assert not log.exists()
  with log.open('w')as stream:row['exitCode']=subprocess.run(row['argv'],stdout=stream,stderr=subprocess.STDOUT).returncode
  row['finishedAtUnix']=time.time();ex.save(path,record);assert row['exitCode']==0,'Preserve failed phase; do not bypass its gate'
 record['D0PromptsReadyAtUnix']=time.time();ex.save(path,record);print('Complete own FINAL cohort closed; hidden inputs materialized; D0 anonymous delivery/prompts ready.',flush=True)
 # This command independently authorizes hidden-inputs again before any SDK.
 code=subprocess.run([sys.executable,'-B',str(R/'run_batch.py'),'common-FINAL']).returncode
 record.update(finishedAtUnix=time.time(),commonFinalBatchExitCode=code);ex.save(path,record);assert code==0
if __name__=='__main__':main()
