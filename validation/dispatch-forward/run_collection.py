#!/usr/bin/env python3
"""One native slot per platform; seal a finished corpus without operator polling gaps."""
import argparse,concurrent.futures,json,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def utc():return datetime.now(timezone.utc).isoformat()
def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--tool',choices=['common-v3','candidate-v4'],required=True);p.add_argument('--phase',choices=['d0','final'],required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--simulator',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--seal',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);record={'startedAtUTC':utc(),'startedAtUnix':time.time(),'slots':{'ios':1,'android':1},'runs':{}}
 def run(platform):
  cmd=[sys.executable,str(R/'trial_operator.py'),'capture','--workspace',str(a.workspace.resolve()),'--tool',a.tool,'--phase',a.phase,'--inputs',str(a.inputs.resolve()),'--platform',platform,'--simulator',a.simulator,'--output',str((a.output/platform).resolve())];row={'argv':cmd,'startedAtUTC':utc(),'startedAtUnix':time.time()}
  with(a.output/(platform+'-process.log')).open('w')as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
  row.update(exitCode=code,finishedAtUTC=utc(),finishedAtUnix=time.time());return platform,row
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  futures=[pool.submit(run,platform)for platform in ['ios','android']]
  for future in concurrent.futures.as_completed(futures):
   platform,row=future.result();record['runs'][platform]=row;print(json.dumps({'platform':platform,'processExitCode':row['exitCode']}),flush=True)
 record.update(acquisitionFinishedAtUTC=utc(),acquisitionFinishedAtUnix=time.time());(a.output/'orchestration.json').write_text(json.dumps(record,indent=2)+'\n')
 assert all((a.output/platform/'corpus.json').is_file()for platform in ['ios','android']),'Incomplete collection; original commands/logs retained for operator, no fake corpus seal'
 subprocess.run([sys.executable,str(R/'seal_corpus.py'),'--source',str(a.output),'--destination',str(a.archive),'--seal',str(a.seal)],check=True)
 shutil.copy2(a.output/'orchestration.json',a.archive/'orchestration.json')
 for platform in ['ios','android']:shutil.copy2(a.output/(platform+'-process.log'),a.archive/(platform+'-process.log'))
 print(json.dumps({'archive':str(a.archive),'seal':str(a.seal),'completedAtUTC':utc()}),flush=True)
if __name__=='__main__':main()
