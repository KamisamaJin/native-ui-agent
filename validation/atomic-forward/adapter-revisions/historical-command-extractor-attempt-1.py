#!/usr/bin/env python3
"""Run the existing SDK-free publication regressions; retain every exit and log."""
import os,shlex,subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def main():
 workflow=(REPO/'.github/workflows/test.yml').read_text().split('      - name: Atomic review metric controls')[0]
 commands=[]
 for line in workflow.splitlines():
  stripped=line.strip()
  if stripped.startswith('- run: python'):command=stripped[len('- run: '):]
  elif line.startswith('          python'):command=stripped
  else:continue
  if '-m pip install'in command or '-m unittest discover -s native-ui-agent/tests'in command:continue
  argv=shlex.split(command);argv[0]=sys.executable;commands.append(argv)
 out=R/'operators/historical-regressions';assert not out.exists();out.mkdir()
 rows=[];started=time.time()
 for i,argv in enumerate(commands):
  row={'argv':argv,'startedAtUnix':time.time()};log=out/(str(i).zfill(2)+'.log')
  with log.open('w')as stream:code=subprocess.run(argv,cwd=REPO,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')).returncode
  row.update(exitCode=code,finishedAtUnix=time.time(),log=str(log.relative_to(R)));rows.append(row);ex.save(out/'progress.json',{'startedAtUnix':started,'commands':rows,'planned':len(commands)})
  print(i,code,' '.join(argv[1:]),flush=True)
 ex.save(out/'result.json',{'startedAtUnix':started,'finishedAtUnix':time.time(),'commands':rows,'allPassed':all(v['exitCode']==0 for v in rows),'scope':'Shared SDK-free historical regression; no new task feedback or SDK acquisition. Runs overlap initial native collection, so resource sums are not independent elapsed cost.'})
 assert all(v['exitCode']==0 for v in rows),'Historical failure preserved; investigate before publication'
if __name__=='__main__':main()
