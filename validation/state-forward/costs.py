#!/usr/bin/env python3
"""Recompute primary continuous endpoints and separate experiment acquisition costs."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def timestamp(s):
 if s.endswith(' UTC'):return datetime.strptime(s,'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc).timestamp()
 return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def interval_union(intervals):
 merged=[]
 for start,end in sorted(intervals):
  assert end>=start
  if merged and start<=merged[-1][1]:merged[-1][1]=max(end,merged[-1][1])
  else:merged.append([start,end])
 return sum(b-a for a,b in merged)
def build():
 units={}
 for u in ['unit-93485d','unit-fb632e']:
  base=R/'submissions'/u;stages={};intervals=[]
  for name,folder in [('implementation','initial-agent-output'),('review','original-review'),('repair','final-agent-output')]:
   data=read(base/folder/(name+'.json'));start=timestamp(data['start_utc']);end=timestamp(data['end_utc'])
   stages[name]={'startedAtUnix':start,'finishedAtUnix':end,'wallSeconds':end-start,'clockSource':'agent recorded actual phase timestamps'};intervals.append((start,end))
  commands={};totalcommands=0
  for stage in ['d0','final']:
   corpus=read(R/'own-corpora'/u/stage/'corpus.json');start=corpus['startedAtUnix'];end=corpus['finishedAtUnix']
   stages['own-'+stage]={'startedAtUnix':start,'finishedAtUnix':end,'wallSeconds':end-start,'clockSource':'native collection operator; archive sealing follows'};intervals.append((start,end))
   for platform,runs in corpus['platformRuns'].items():
    commands[stage+'-'+platform]={'commandWallSumSeconds':sum(r['wallSeconds']for r in runs),'commands':len(runs),'nonzeroExits':sum(r['exitCode']!=0 for r in runs)}
    totalcommands+=sum(r['wallSeconds']for r in runs)
  start=stages['implementation']['startedAtUnix'];end=read(R/'own-corpora'/u/'final/corpus-seal.json')['sealedAtUnix']
  units[u]={'continuousImplementationToOwnFinalSealSeconds':end-start,'phaseUnionSeconds':interval_union(intervals),'uncoveredWaitingAndCoordinationSeconds':end-start-interval_union(intervals),'modelPhaseWallSumSeconds':sum(stages[k]['wallSeconds']for k in ['implementation','review','repair']),'ownNativeCommandWallSumSeconds':totalcommands,'stages':stages,'native':commands,'limitsMinutes':{'implementation':25,'review':12,'repair':15}}
 extra=[]
 for root in ['common-corpora','paired-corpora']:
  for p in sorted((R/root).rglob('corpus.json')):
   d=read(p)
   if 'platformRuns'not in d:continue
   runs=[r for rows in d['platformRuns'].values()for r in rows]
   extra.append({'corpus':str(p.relative_to(R)),'phase':d['phase'],'wallSeconds':d['finishedAtUnix']-d['startedAtUnix'],'nativeCommandWallSumSeconds':sum(r['wallSeconds']for r in runs),'commands':len(runs),'nonzeroExits':sum(r['exitCode']!=0 for r in runs)})
 return {'units':units,'experimentOnlyAcquisitions':extra,'scope':'Continuous endpoints include actual barriers/coordination/cache contention, native commands run one slot per OS per acquisition. Command sums are resource work, not elapsed wall. Shared Mac and one task per arm do not establish causal speed. Generic engineering, common grading, paired captures, publication and CI are experiment work, not treatment development cost. Tokens and monetary cost were not measured.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();data=build();target=R/'costs.json'
 if a.write:target.write_text(json.dumps(data,indent=2)+'\n')
 else:assert read(target)==data,'Costs differ from original timestamps'
 print(json.dumps({'status':'PASS','primaryWallSeconds':{k:v['continuousImplementationToOwnFinalSealSeconds']for k,v in data['units'].items()},'experimentCommands':sum(x['commands']for x in data['experimentOnlyAcquisitions'])}))
if __name__=='__main__':main()
