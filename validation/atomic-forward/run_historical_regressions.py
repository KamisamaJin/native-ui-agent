#!/usr/bin/env python3
"""Run the existing SDK-free publication regressions; retain every exit and log."""
import argparse,os,re,shlex,subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='historical-regressions');p.add_argument('--reuse-passed',type=Path);a=p.parse_args()
 workflow=(REPO/'.github/workflows/test.yml').read_text().split('      - name: Atomic review metric controls')[0]
 commands=[]
 for line in workflow.splitlines():
  match=re.match(r'^\s+(?:- )?run:\s+(python(?:3)?\s+.+)$',line)or re.match(r'^\s+(python(?:3)?\s+.+)$',line)
  if not match:continue
  command=match.group(1)
  if '-m pip install'in command or '-m unittest discover -s native-ui-agent/tests'in command:continue
  argv=shlex.split(command);argv[0]=sys.executable;commands.append(argv)
 out=R/'operators'/a.output;assert not out.exists();out.mkdir()
 reuse={tuple(v['argv']):v for v in ex.read(a.reuse_passed)['commands']if v['exitCode']==0}if a.reuse_passed else{}
 rows=[];started=time.time()
 for i,argv in enumerate(commands):
  if tuple(argv)in reuse:
   row=dict(reuse[tuple(argv)],reusedSuccessfulRecord=str(a.reuse_passed.resolve().relative_to(R)));rows.append(row);print(i,'reused PASS',' '.join(argv[1:]),flush=True);continue
  row={'argv':argv,'startedAtUnix':time.time()};log=out/(str(i).zfill(2)+'.log')
  with log.open('w')as stream:code=subprocess.run(argv,cwd=REPO,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')).returncode
  row.update(exitCode=code,finishedAtUnix=time.time(),log=str(log.relative_to(R)));rows.append(row);ex.save(out/'progress.json',{'startedAtUnix':started,'commands':rows,'planned':len(commands)})
  print(i,code,' '.join(argv[1:]),flush=True)
 ex.save(out/'result.json',{'startedAtUnix':started,'finishedAtUnix':time.time(),'commands':rows,'allPassed':all(v['exitCode']==0 for v in rows),'scope':'Shared SDK-free historical regression; no new task feedback or SDK acquisition. Runs overlap initial native collection, so resource sums are not independent elapsed cost.'})
 assert all(v['exitCode']==0 for v in rows),'Historical failure preserved; investigate before publication'
if __name__=='__main__':main()
