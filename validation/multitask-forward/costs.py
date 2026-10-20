#!/usr/bin/env python3
"""Actual six-unit/cohort latency, native work and experiment overhead."""
import argparse,json,statistics
from datetime import datetime
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def stamp(v):return v if isinstance(v,(int,float))else datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()
def phase(record):
 pairs=[('startedAtUnix','finishedAtUnix'),('start_utc','end_utc'),('started_at','finished_at'),('startUTC','endUTC')]
 for a,b in pairs:
  if a in record and b in record:
   x,y=stamp(record[a]),stamp(record[b]);assert y>=x;return {'startedAtUnix':x,'finishedAtUnix':y,'wallSeconds':y-x}
 raise ValueError('Missing actual model phase timestamps')
def union(xs):
 merged=[]
 for a,b in sorted(xs):
  if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
  else:merged.append([a,b])
 return sum(b-a for a,b in merged)
def build():
 assignment=read(R/'private/assignment.json');units={}
 for unit,config in assignment['units'].items():
  base=R/'submissions'/unit
  stages={name:phase(read(base/folder/(name+'.json')))for name,folder in [('implementation','initial-agent-output'),('review','original-review'),('repair','final-agent-output')]}
  native=[]
  for key in ['d0','final']:
   c=read(R/'own-corpora'/unit/key/'corpus.json');stages['own-'+key]={'startedAtUnix':c['startedAtUnix'],'finishedAtUnix':c['finishedAtUnix'],'wallSeconds':c['finishedAtUnix']-c['startedAtUnix']}
   native += [dict(row,platform=p,phase=key)for p,rows in c['platformRuns'].items()for row in rows]
  start=stages['implementation']['startedAtUnix'];end=read(R/'own-corpora'/unit/'final/corpus-seal.json')['sealedAtUnix'];active=union([(r['startedAtUnix'],r['finishedAtUnix'])for r in stages.values()])
  units[unit]={'task':config['task'],'tool':config['tool'],'continuousImplementationToOwnFinalSealSeconds':end-start,'ownFinalSealedAtUnix':end,'phaseUnionSeconds':active,'waitingAndCoordinationSeconds':end-start-active,'modelPhaseWallSumSeconds':sum(stages[k]['wallSeconds']for k in ['implementation','review','repair']),'ownNativeCommandWallSumSeconds':sum(r['wallSeconds']for r in native),'ownNativeCommands':len(native),'ownNativeNonzeroExits':sum(r['exitCode']!=0 for r in native),'stages':stages,'setup':read(R/'operators'/(unit+'-bootstrap.json'))}
 extras=[]
 for category in ['common-corpora','paired-corpora','own-retries']:
  for p in sorted((R/category).rglob('corpus.json')):
   c=read(p)
   if 'platformRuns'not in c:continue
   runs=[row for rows in c['platformRuns'].values()for row in rows]
   extras.append({'corpus':str(p.relative_to(R)),'wallSeconds':c['finishedAtUnix']-c['startedAtUnix'],'nativeCommandWallSumSeconds':sum(r['wallSeconds']for r in runs),'commands':len(runs),'nonzeroExits':sum(r['exitCode']!=0 for r in runs)})
 starts=[u['stages']['implementation']['startedAtUnix']for u in units.values()];ends=[u['ownFinalSealedAtUnix']for u in units.values()]
 reveal=read(R/'private/ASSIGNMENT-RELEASE.json')['releasedAtUnix'];preregister=read(R/'prospective-seal.json')['recordedAtUnix'];public_closed=read(R/'gates/own-final.json')['sealedAtUnix']
 for unit,value in units.items():value['continuousImplementationToCompletePublicCohortSealSeconds']=public_closed-value['stages']['implementation']['startedAtUnix']
 grading={stage:{'cohortSealedAtUnix':read(R/'gates'/(stage+'.json'))['sealedAtUnix'],'taskPhases':{t:phase(read(R/'evaluation'/folder/t/'phase.json'))for t in ['T1','T2','T3']}}for stage,folder in [('grade-d0','D0'),('grade-final','FINAL'),('grade-selfreview','selfreview'),('grade-pair','paired-D0')]}
 supplement={'label':'Posthoc shared infrastructure correction; excluded from treatment gains','fixSealedAtUnix':read(R/'shared-environment-v1/gates/fix.json')['sealedAtUnix'],'allTasksSealedAtUnix':read(R/'shared-environment-v1/gates/graded.json')['sealedAtUnix'],'taskPhases':{t:phase(read(R/'supplement'/t/'phase.json'))for t in ['T1','T2','T3']},'additionalNativeCommands':0}
 queues=[]
 for p in sorted((R/'operators').glob('*-unit-*.json')):
  row=read(p)
  if 'resourceWaitSeconds'in row:queues.append({'operator':str(p.relative_to(R)),'phase':row['phase'],'unit':row['unit'],'slot':row['slot'],'resourceWaitSeconds':row['resourceWaitSeconds'],'queuedAtUnix':row['queuedAtUnix'],'resourceGrantedAtUnix':row['resourceGrantedAtUnix']})
 arms={}
 for tool in ['baseline-v6','candidate-v7']:
  vv=[u for u in units.values()if u['tool']==tool];latencies=[u['continuousImplementationToOwnFinalSealSeconds']for u in vv]
  arms[tool]={'units':len(vv),'continuousLatencySeconds':latencies,'meanContinuousLatencySeconds':statistics.mean(latencies),'medianContinuousLatencySeconds':statistics.median(latencies),'modelPhaseWallSumSeconds':sum(u['modelPhaseWallSumSeconds']for u in vv),'ownNativeCommandWallSumSeconds':sum(u['ownNativeCommandWallSumSeconds']for u in vv),'waitingAndCoordinationSumSeconds':sum(u['waitingAndCoordinationSeconds']for u in vv)}
 return {'units':units,'arms':arms,'cohortImplementationToPublicEndpointSeconds':max(ends)-min(starts),'cohortImplementationToCompletePublicCohortSealSeconds':public_closed-min(starts),'completePublicCohortSealedAtUnix':public_closed,'earliestImplementationAtUnix':min(starts),'latestPublicEndpointAtUnix':max(ends),'implementationToAssignmentRevealSeconds':reveal-min(starts),'preregistrationToRevealSeconds':reveal-preregister,'experimentOnlyAcquisitions':extras,'extraNativeCommandWallSumSeconds':sum(v['nativeCommandWallSumSeconds']for v in extras),'gradingStages':grading,'sharedEnvironmentSupplement':supplement,'nativeResourceQueues':queues,'recordedResourceWaitSumSeconds':sum(q['resourceWaitSeconds']for q in queues),'tokens':None,'money':None,'scope':'Actual wall timestamps and SDK-wrapper command sums, not estimates. Per-unit primary endpoint is its own FINAL raw corpus seal; complete public cohort closure additionally includes all six final corpora and original final typed checks. Both are reported. Model walls include compile waits. Shared Mac, two builder slots, two native-acquisition slots, caches, task order and whole-cohort barriers confound per-arm latency. Global barriers are experimental overhead, not ordinary product delivery latency. Independent design/tool engineering/neutral checks and grading are shared infrastructure costs, not treatment speed gains. The initial own-D0 batch predates shared cross-process lock instrumentation, so it has no measured resource-lock wait; ordinary queue/barrier delay remains in primary continuous latency. Summed simultaneous command/model/unit walls are resource work, not cohort elapsed time.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'costs.json'
 if a.write:
  assert not out.exists();out.write_text(json.dumps(v,indent=2)+'\n')
 else:assert read(out)==v
 print(json.dumps({'status':'PASS','cohortPublicEndpointSeconds':v['cohortImplementationToPublicEndpointSeconds'],'units':{k:r['continuousImplementationToOwnFinalSealSeconds']for k,r in v['units'].items()}}))
if __name__=='__main__':main()
