#!/usr/bin/env python3
"""Actual recorded wall costs; overlapping spans and command sums are not additive."""
import argparse,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def compute():
 assignment=ex.read(R/'private/assignment.json');closure=ex.read(R/'gates/own-final.json')['sealedAtUnix'];units=[]
 for unit,config in assignment['units'].items():
  base=R/'submissions'/unit;spans={}
  for phase,path in [('implementation',base/'initial-agent-output/implementation.json'),('review',base/'original-review/review.json'),('repair',base/'final-agent-output/repair.json')]:
   row=ex.read(path);a=row['startedAtUnix'];b=row['finishedAtUnix'];assert b>=a;spans[phase]={'startedAtUnix':a,'finishedAtUnix':b,'wallSeconds':b-a}
  initial=spans['implementation']['startedAtUnix'];endpoint=ex.read(base/'own-checks-final.json')['completedAtUnix'];raw=ex.read(R/'own-corpora'/unit/'final/corpus-seal.json')['sealedAtUnix'];native=[]
  for phase in ['d0','final']:
   corpus=ex.read(R/'own-corpora'/unit/phase/'corpus.json')
   for pl,rows in corpus['platformRuns'].items():
    for row in rows:native.append({'phase':phase,'platform':pl,'case':row['case'],'seconds':row['finishedAtUnix']-row['startedAtUnix'],'exitCode':row['exitCode']})
  queues=[]
  for phase in ['own-D0','own-FINAL']:
   row=ex.read(R/'operators'/(phase+'-'+unit+'.json'));queues.append({'phase':phase,'seconds':row['resourceWaitSeconds']})
  units.append({'unit':unit,**config,'phases':spans,'modelPhaseWallSumSeconds':sum(v['wallSeconds']for v in spans.values()),'ownNativeCommandCount':len(native),'ownNativeCommandSumSeconds':sum(v['seconds']for v in native),'nativeCommands':native,'nativeQueueSeconds':sum(v['seconds']for v in queues),'queues':queues,'ownFinalRawSealAtUnix':raw,'ownFinalRawSeconds':raw-initial,'ownFinalRawAndCheckEndpointAtUnix':endpoint,'ownFinalRawAndCheckSeconds':endpoint-initial,'allSixClosureSeconds':closure-initial,'ownFinalCheckWallTailSeconds':endpoint-raw})
 native_all=[]
 for phase in ['own-D0','own-FINAL','common-D0','common-FINAL']:
  batch=ex.read(R/'operators'/(phase+'-batch.json'))
  native_all.append({'phase':phase,'wallSeconds':max(r['finishedAtUnix']for r in batch['runs'])-min(r['startedAtUnix']for r in batch['runs']),'queueSeconds':sum(r['resourceWaitSeconds']for r in batch['runs'])})
 def mean(values):return sum(values)/len(values)if values else None
 groups={}
 for tool in ['baseline-v7','candidate-v8']:
  rows=[r for r in units if r['tool']==tool];groups[tool]={'units':len(rows),'meanOwnFinalRawAndCheckSeconds':mean([r['ownFinalRawAndCheckSeconds']for r in rows]),'meanOwnFinalRawSeconds':mean([r['ownFinalRawSeconds']for r in rows]),'meanAllSixClosureSeconds':mean([r['allSixClosureSeconds']for r in rows]),'modelPhaseWallSumSeconds':sum(r['modelPhaseWallSumSeconds']for r in rows),'ownNativeCommandSumSeconds':sum(r['ownNativeCommandSumSeconds']for r in rows),'nativeQueueSeconds':sum(r['nativeQueueSeconds']for r in rows),'phaseWallSumSeconds':{p:sum(r['phases'][p]['wallSeconds']for r in rows)for p in ['implementation','review','repair']}}
 prereg=ex.read(R/'PREREGISTRATION.json');reveal=ex.read(R/'gates/reveal.json')['sealedAtUnix'];toolseal=ex.read(R/'gates/tools.json')['sealedAtUnix'];designseal=ex.read(R/'gates/design.json')['sealedAtUnix']
 return {'units':units,'groups':groups,'acquisitionBatches':native_all,'chronology':{'preregistration':prereg,'toolsSealedAtUnix':toolseal,'designSealedAtUnix':designseal,'ownFinalClosureAtUnix':closure,'revealAtUnix':reveal},'tokenCost':None,'monetaryCost':None,'scope':'Recorded consumer endpoint includes real cohort barriers and checks; no minute substitutes from raw-file creation alone. Native commands overlap and sums are not elapsed cost. Compilation waits are included in model phases. Shared caches/order/hardware and three pairs prevent a causal speed claim. Publication/CI is recorded separately.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=compute();path=R/'costs.json'
 if a.check:assert ex.read(path)==value
 else:assert not path.exists();ex.save(path,value)
 print('PASS actual costs')
if __name__=='__main__':main()
