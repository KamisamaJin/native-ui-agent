#!/usr/bin/env python3
"""Normalize source-reported phase times; keep queue/native costs separate."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def epoch(value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def phase(path,kind):
 d=read(path)
 start=d.get('startedAtUTC')or d.get('begin_utc')or d.get('started_utc')
 end=d.get('endedAtUTC')or d.get('end_utc')or d.get('ended_utc')
 duration=d.get('durationSeconds',d.get('active_wall_seconds'))
 assert start and end and duration is not None
 assert abs(epoch(end)-epoch(start)-duration)<1,(path,duration)
 limit={'implementation':1500,'readonlyReview':720,'repair':900}[kind]
 if duration>limit:
  exceptions=read(R/'protocol-deviations.json')['deviations']
  assert any(x['report']==str(path.relative_to(R))and abs(x['actualSeconds']-duration)<0.001 and x['limitSeconds']==limit for x in exceptions)
 return {'startedAtUTC':start,'endedAtUTC':end,'durationSeconds':duration,'limitSeconds':limit,'withinLimit':duration<=limit,'sourceReport':str(path.relative_to(R)),'sourceSha256':sha(path)}
def main():
 result={}
 for folder in sorted((R/'implementations/d0').glob('submission-*')):
  sub=folder.name;root=R/'phase-reports'/sub
  phases={'implementation':phase(root/'d0-summary.json','implementation'),'readonlyReview':phase(root/'readonly-review/reports/self-review.json','readonlyReview'),'repair':phase(root/'repair/reports/repair.json','repair')}
  phases['agentPhaseSeconds']=round(sum(phases[k]['durationSeconds']for k in ['implementation','readonlyReview','repair']),3)
  phases['interStageSeconds']={'implementationToReadonlyReview':round(epoch(phases['readonlyReview']['startedAtUTC'])-epoch(phases['implementation']['endedAtUTC']),3),'readonlyReviewToRepair':round(epoch(phases['repair']['startedAtUTC'])-epoch(phases['readonlyReview']['endedAtUTC']),3)}
  phases['supportedNativeCaptureCommandSeconds']={p:{platform:round(sum(read(f/'capture.json')['seconds']for f in(R/'evidence'/p/sub/platform).iterdir()if(f/'capture.json').exists()),3)for platform in ['android','ios']}for p in ['d0','final']}
  result[sub]=phases
 output={'schemaVersion':1,'submissions':result,'operatorWorkBeganApproximately':read(R/'setup.json')['work_began_approximately'],'recordedAtUTC':datetime.now(timezone.utc).isoformat(),'interpretation':['Agent phases include their own tool/build/native waits; raw phase report times preserved.','Inter-stage time includes operator collection, independent grading, queues and waiting for peers; it is not agent active work.','Native command durations are per-arm/platform sums and overlap across arms; do not add them into a claimed elapsed speedup.','Initial infrastructure setup/repairs and superseded captures are separate engineering costs, not measured v2 benefits.','No calibrated model/hardware/random-seed timing control; descriptive only.']}
 (R/'timing.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'status':'normalized_phase_timing','submissions':len(result)}))
if __name__=='__main__':main()
