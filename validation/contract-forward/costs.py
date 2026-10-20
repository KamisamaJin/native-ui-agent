#!/usr/bin/env python3
"""Recompute actual wall/resource costs without estimating tokens or money."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def timestamp(value):
 if isinstance(value,(int,float)):return value
 if value.endswith(' UTC'):return datetime.strptime(value,'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc).timestamp()
 return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def union(intervals):
 merged=[]
 for a,b in sorted(intervals):
  assert b>=a
  if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
  else:merged.append([a,b])
 return sum(b-a for a,b in merged)
def build():
 assignment=read(R/'private/assignment.json');units={}
 for unit,config in assignment['units'].items():
  stages={};intervals=[];base=R/'submissions'/unit
  for name,folder in [('implementation','initial-agent-output'),('review','original-review'),('repair','final-agent-output')]:
   record=read(base/folder/(name+'.json'));a=timestamp(record['start_utc']);b=timestamp(record['end_utc']);intervals.append((a,b));stages[name]={'startedAtUnix':a,'finishedAtUnix':b,'wallSeconds':b-a}
  native={};resource=0
  for phase in ['d0','final']:
   data=read(R/'own-corpora'/unit/phase/'corpus.json');a=data['startedAtUnix'];b=data['finishedAtUnix'];intervals.append((a,b));stages['own-'+phase]={'startedAtUnix':a,'finishedAtUnix':b,'wallSeconds':b-a}
   for platform,runs in data['platformRuns'].items():
    n={'commandWallSumSeconds':sum(r['wallSeconds']for r in runs),'commands':len(runs),'nonzeroExits':sum(r['exitCode']!=0 for r in runs)};native[phase+'-'+platform]=n;resource+=n['commandWallSumSeconds']
   retry=R/'own-retries'/unit/phase/'corpus.json'
   if retry.exists():
    data=read(retry);x=data['startedAtUnix'];y=data['finishedAtUnix'];intervals.append((x,y));stages['own-'+phase+'-common-retry']={'startedAtUnix':x,'finishedAtUnix':y,'wallSeconds':y-x}
    for platform,runs in data['platformRuns'].items():
     n={'commandWallSumSeconds':sum(r['wallSeconds']for r in runs),'commands':len(runs),'nonzeroExits':sum(r['exitCode']!=0 for r in runs)};native[phase+'-common-retry-'+platform]=n;resource+=n['commandWallSumSeconds']
  a=stages['implementation']['startedAtUnix'];b=read(R/'own-corpora'/unit/'final/corpus-seal.json')['sealedAtUnix'];setup=read(R/'operators'/(unit+'-bootstrap.json'))
  units[unit]={'tool':config['tool'],'continuousImplementationToOwnFinalSealSeconds':b-a,'phaseUnionSeconds':union(intervals),'waitingAndCoordinationSeconds':b-a-union(intervals),'modelPhaseWallSumSeconds':sum(stages[k]['wallSeconds']for k in ['implementation','review','repair']),'ownNativeCommandWallSumSeconds':resource,'setupWallSeconds':setup['finishedAtUnix']-setup['startedAtUnix'],'stages':stages,'native':native}
 extras=[]
 for category in ['common-corpora','paired-corpora']:
  for p in sorted((R/category).rglob('corpus.json')):
   data=read(p)
   if 'platformRuns'not in data:continue
   runs=[r for rs in data['platformRuns'].values()for r in rs];extras.append({'corpus':str(p.relative_to(R)),'wallSeconds':data['finishedAtUnix']-data['startedAtUnix'],'nativeCommandWallSumSeconds':sum(r['wallSeconds']for r in runs),'commands':len(runs),'nonzeroExits':sum(r['exitCode']!=0 for r in runs)})
 common_recovery={}
 if(R/'COMMON-WIDTH-AMENDMENT.json').exists():
  common_recovery={'amendment':'COMMON-WIDTH-AMENDMENT.json','neutralProbe':'generic-width/RESULT.json','windowStartUnix':min(row['finishedAtUnix']for u in assignment['units']for rows in read(R/'own-corpora'/u/'d0/corpus.json')['platformRuns'].values()for row in rows if row['exitCode']==2),'windowEndUnix':max(read(R/'submissions'/u/'effective-own-d0.json')['sealedAtUnix']for u in assignment['units']),'attribution':'Shared frontend input policy recovery. Both original failures and retries included in primary continuous/resource costs; this window is not a v6 treatment benefit.'}
  common_recovery['windowWallSeconds']=common_recovery['windowEndUnix']-common_recovery['windowStartUnix']
 grading={}
 for stage in ['D0','FINAL','selfreview','paired-D0']:
  delivery=read(R/'evaluation-inputs'/stage/'DELIVERY-SEAL.json');seal=read(R/'evaluation'/stage/'SEAL.json');grading[stage]={'deliveryAtUnix':delivery['sealedAtUnix'],'dualSealAtUnix':seal['sealedAtUnix'],'deliveryToDualSealWallSeconds':seal['sealedAtUnix']-delivery['sealedAtUnix'],'scope':'Shared experiment grading interval, includes dispatch/coordination; not per-arm active model time and may overlap acquisition/primary development.'}
 experiment_start=min(v['stages']['implementation']['startedAtUnix']for v in units.values());experiment_end=read(R/'private/ASSIGNMENT-RELEASE.json')['releasedAtUnix']
 return {'sharedGradingStages':grading,'sharedExperimentImplementationToRevealWallSeconds':experiment_end-experiment_start,'units':units,'experimentOnlyAcquisitions':extras,'commonInfrastructureRecovery':common_recovery,'commonDesignAndEngineering':'Independent design and tool engineering are common experiment costs, not attributed as treatment feature-delivery speed. Primary starts at each implementation phase and includes all real barriers until fresh own FINAL evidence is sealed. Setup reported separately; caches and shared hardware limit causal cost claims.','tokens':None,'money':None,'scope':'Phase walls overlap native and other agents; command sums are resource work, not elapsed wall. One task per arm, shared Mac, no statistical speed guarantee.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();data=build();out=R/'costs.json'
 if a.write:out.write_text(json.dumps(data,indent=2)+'\n')
 else:assert read(out)==data
 print(json.dumps({'status':'PASS','primaryWallSeconds':{u:v['continuousImplementationToOwnFinalSealSeconds']for u,v in data['units'].items()}}))
if __name__=='__main__':main()
