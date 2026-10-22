#!/usr/bin/env python3
"""Report auxiliary judging/replay cost without changing frozen consumer metrics."""
import argparse,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def compute():
 ex.gate.authorize(R/'gates','reveal',R)
 panels=[]
 for pattern in ['judgments/*/*/*/phase.json','claim-judgments/*/*/phase.json']:
  for p in sorted(R.glob(pattern)):
   v=ex.read(p);start=v.get('startedAtUnix');end=v.get('finishedAtUnix')
   assert isinstance(start,(int,float))and isinstance(end,(int,float))and end>=start,str(p)
   panels.append({'record':str(p.relative_to(R)),'startedAtUnix':start,'finishedAtUnix':end,'wallSeconds':end-start})
 assert len(panels)==18,len(panels)
 acquisition=[]
 for phase,pattern in [('own','own-corpora/*/*/corpus.json'),('common','common-corpora/*/*/*/corpus.json')]:
  for p in sorted(R.glob(pattern)):
   v=ex.read(p)
   if 'platformRuns'not in v:continue
   for pl,rows in v['platformRuns'].items():
    acquisition += [{'record':str(p.relative_to(R)),'scope':phase,'platform':pl,'case':row['case'],'wallSeconds':row['finishedAtUnix']-row['startedAtUnix'],'exitCode':row['exitCode']}for row in rows]
 assert len(acquisition)==108,len(acquisition)
 replay=[]
 for p in sorted(R.glob('evaluation/pair/*/*/*/*/*-command.json')):
  v=ex.read(p);replay.append({'record':str(p.relative_to(R)),'wallSeconds':v['finishedAtUnix']-v['startedAtUnix'],'exitCode':v['exitCode'],'newSDKCommands':v['newSDKCommands']})
 assert len(replay)==48,len(replay)
 return {'judgmentTaskSpans':panels,'judgmentTaskWallSumSeconds':sum(v['wallSeconds']for v in panels),'judgmentStageEnvelopes':{key:{'wallSeconds':max(v['finishedAtUnix']for v in panels if v['record'].startswith(key))-min(v['startedAtUnix']for v in panels if v['record'].startswith(key))}for key in sorted({'/'.join(v['record'].split('/')[:-2])for v in panels})},'nativeCommands':acquisition,'nativeCommandWallSumSeconds':sum(v['wallSeconds']for v in acquisition),'nativeCommandWallSumByScope':{scope:sum(v['wallSeconds']for v in acquisition if v['scope']==scope)for scope in ['own','common']},'offlineReplay':replay,'offlineReplayWallSumSeconds':sum(v['wallSeconds']for v in replay),'offlineReplaySDKCommands':sum(v['newSDKCommands']for v in replay),'scope':'Auxiliary shared validation cost. Sums include overlapping spans and are not elapsed latency. Frozen costs.json remains the primary per-unit consumer endpoint. Tokens, dollars and unrecorded host-agent compute are not estimated. Publication/CI is visible in Git history and the exact-head Actions run.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=compute();path=R/'grading-costs.json'
 if a.check:assert ex.read(path)==value
 else:assert not path.exists();ex.save(path,value)
 print('PASS auxiliary shared costs')
if __name__=='__main__':main()
