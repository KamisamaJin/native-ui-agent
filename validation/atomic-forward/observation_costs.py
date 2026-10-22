#!/usr/bin/env python3
"""Original frame telemetry, distinct from whole native-command elapsed cost."""
import argparse
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def compute():
 ex.gate.authorize(R/'gates','reveal',R);rows=[]
 for pattern in ['own-corpora/*/*/corpus.json','common-corpora/*/*/*/corpus.json']:
  for cp in sorted(R.glob(pattern)):
   corpus=ex.read(cp)
   for pl,commands in corpus['platformRuns'].items():
    for cmd in commands:
     op=cp.parent/pl/cmd['case']/'observation.json';obs=ex.read(op)if op.is_file()else{};frames=obs.get('snapshots',[]);times=[];ax=[]
     for f in frames:
      value=f.get('performance',{}).get('capture_seconds')if pl=='ios'else f.get('capture_seconds')
      if isinstance(value,(int,float))and value>=0:times.append(value)
      value=f.get('performance',{}).get('ax_snapshot_seconds')
      if isinstance(value,(int,float))and value>=0:ax.append(value)
     rows.append({'observation':str(op.relative_to(R)),'platform':pl,'case':cmd['case'],'tool':corpus['tool'],'commandWallSeconds':cmd['finishedAtUnix']-cmd['startedAtUnix'],'exitCode':cmd['exitCode'],'observationExists':op.is_file(),'frameCount':len(frames),'timedCaptureFrameCount':len(times),'captureTelemetrySumSeconds':sum(times),'axSnapshotTimedFrameCount':len(ax),'axSnapshotTelemetrySumSeconds':sum(ax),'stateCaptureSets':len(obs.get('state_captures',[]))})
 assert len(rows)==108,len(rows)
 return {'commands':rows,'platforms':{pl:{'commands':len([v for v in rows if v['platform']==pl]),'frames':sum(v['frameCount']for v in rows if v['platform']==pl),'commandWallSumSeconds':sum(v['commandWallSeconds']for v in rows if v['platform']==pl),'captureTelemetrySumSeconds':sum(v['captureTelemetrySumSeconds']for v in rows if v['platform']==pl),'axSnapshotTelemetrySumSeconds':sum(v['axSnapshotTelemetrySumSeconds']for v in rows if v['platform']==pl)}for pl in ['ios','android']},'scope':'Actual observer frame telemetry only. Whole command wall includes compilation, native action/reveal/scroll/quiescence, collection/export and process overhead. The residual is not directly attributed CPU time, and auxiliary/duplicate-looking frames are not automatically unnecessary. No sampler/route was changed after the tested release froze.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=compute();path=R/'observation-costs.json'
 if a.check:assert ex.read(path)==value
 else:assert not path.exists();ex.save(path,value)
 print('PASS original frame telemetry')
if __name__=='__main__':main()
