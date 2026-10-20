#!/usr/bin/env python3
"""Recompute measured development walls, parallel command sums and exposed gaps."""
import argparse,datetime,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def epoch(value):
 if isinstance(value,(int,float)):return value
 return datetime.datetime.fromisoformat(value.replace(' UTC','+00:00').replace('Z','+00:00')).timestamp()
def iso(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
def report_time(p):
 d=read(p);start=next(k for k in ['started_at','start_utc','startedAtUTC','started_at_utc'] if k in d);end=next(k for k in ['finished_at','end_utc','finishedAtUTC','finished_at_utc','ended_at'] if k in d);a=epoch(d[start]);b=epoch(d[end]);assert b>=a
 return {'startUnix':a,'endUnix':b,'wallSeconds':b-a,'startUTC':iso(a),'endUTC':iso(b),'artifact':str(p.relative_to(R)),'artifactSHA256':sha(p),'fields':[start,end]}
def native_records(corpus):
 rows=[]
 for platform in ['ios','android']:
  for p in sorted((corpus/platform).glob('*-command.json')):
   c=read(p);case=p.parent/c['case'];m=read(case/'manifest.json') if(case/'manifest.json').exists()else {};native=None;summary=m.get('native_summary',{})
   if summary.get('finishTime') is not None and summary.get('startTime') is not None:native=summary['finishTime']-summary['startTime']
   if platform=='android' and(case/'junit.xml').exists():native=float(ET.parse(case/'junit.xml').getroot().attrib['time'])
   rows.append({'platform':platform,'case':c['case'],'startUnix':c['startedAtUnix'],'endUnix':c['finishedAtUnix'],'wallSeconds':c['wallSeconds'],'exitCode':c['exitCode'],'nativeTests':m.get('native_test_count'),'nativeIntervalSeconds':native,'producerTimings':m.get('timings'),'collectorBuildCacheHit':m.get('build_cache',{}).get('hit'),'commandArtifact':str(p.relative_to(R)),'commandArtifactSHA256':sha(p),'nativeManifestSHA256':sha(case/'manifest.json') if m else None})
 return rows
def collection(corpora,seal):
 rows=[row for c in corpora for row in native_records(c)];assert rows;start=min(r['startUnix'] for r in rows);end=max(r['endUnix'] for r in rows);s=read(seal);end=max(d['producerFinishedAtUnix'] for d in s['datasets'].values())
 return {'startUnix':start,'producerEndUnix':end,'sealUnix':s['sealedAtUnix'],'acquisitionWallSeconds':end-start,'archiveWallSeconds':s['archiveWallSeconds'],'producerEndToSealSeconds':s['sealedAtUnix']-end,'commandSumSeconds':sum(r['wallSeconds'] for r in rows),'commands':rows,'sealArtifact':str(seal.relative_to(R)),'sealArtifactSHA256':sha(seal)}
def compute():
 mapping=read(R/'private/assignment.json')['arms'];arms={}
 for arm in mapping:
  id=arm['submission'];p=R/'private/submissions'/id
  implementation=report_time(p/'implementation.json');review=report_time(p/'review.json');repair=report_time(p/'repair.json')
  roots=[R/'evidence/own-d0'/id]
  extra=R/'evidence/administrative-first-d0'/id
  if extra.exists():roots.insert(0,extra)
  initial=collection(roots,p/'d0-corpus-seal.json');final=collection([R/'evidence/own-final'/id],p/'final-corpus-seal.json')
  assert implementation['endUnix']<=initial['startUnix']<=initial['producerEndUnix']<=review['startUnix']<=review['endUnix']<=repair['startUnix']<=repair['endUnix']<=final['startUnix']<=final['producerEndUnix']<=final['sealUnix']
  raw=final['sealUnix']-implementation['startUnix'];segments=implementation['wallSeconds']+initial['acquisitionWallSeconds']+initial['archiveWallSeconds']+review['wallSeconds']+repair['wallSeconds']+final['acquisitionWallSeconds']+final['archiveWallSeconds']
  assert raw+0.01>=segments
  arms[id]={'tool':arm['capability'],'implementation':implementation,'initialCollection':initial,'review':review,'repair':repair,'finalCollection':final,'continuousStartUTC':implementation['startUTC'],'continuousEndUTC':iso(final['sealUnix']),'continuousWallSeconds':raw,'sequentialSegmentSumSeconds':segments,'barrierQueueAndUnallocatedGapSeconds':raw-segments,'namedGapsSeconds':{'implementationEndToFirstCapture':initial['startUnix']-implementation['endUnix'],'initialProducerEndToReview':review['startUnix']-initial['producerEndUnix'],'reviewEndToRepair':repair['startUnix']-review['endUnix'],'repairEndToFinalFirstCapture':final['startUnix']-repair['endUnix'],'finalProducerEndToCorpusSeal':final['sealUnix']-final['producerEndUnix']},'publicIntegration':'Included in implementation wall; do not add its native command sum to that wall again.'}
 audits={}
 for name in ['audit-v4-d0','audit-v4-final','audit-v3-d0']:
  root=R/'evidence'/name
  if root.exists():
   for sub in sorted(root.iterdir()):
    if sub.is_dir():audits[name+'/'+sub.name]=native_records(sub)
 lastPrimary=max(a['finalCollection']['sealUnix'] for a in arms.values())
 for rows in audits.values():assert all(r['startUnix']>=lastPrimary for r in rows),'Experiment-only acquisition contended with primary loop'
 pairs={}
 for sid in arms:
  old=native_records(R/'evidence'/('own-d0'if sid=='submission-e572b1'else'audit-v3-d0')/sid)
  new=native_records(R/'evidence'/('audit-v4-d0'if sid=='submission-e572b1'else'own-d0')/sid)
  pairs[sid]={}
  for platform in ['ios','android']:
   before=[r for r in old if r['platform']==platform];after=[r for r in new if r['platform']==platform]
   assert [r['case']for r in before]==[r['case']for r in after]
   b=sum(r['wallSeconds']for r in before);n=sum(r['wallSeconds']for r in after)
   pairs[sid][platform]={'commonV3CommandSeconds':b,'candidateV4CommandSeconds':n,'reductionSeconds':b-n,'reductionFraction':(b-n)/b,'commonV3Commands':before,'candidateV4Commands':after,'scope':'Identical D0 source and inputs, distinct acquisitions. Shared hardware/SDK/compiler caches, different run order; descriptive bundle comparison, not individual-knob ablation.'}
 setup=report_time(R/'setup.json');generic=read(R/'generic-summary.json');grade_ids=read(R/'private/grade-assignment.json')['mapping'];grading={}
 for phase in ['d0','final','selfreview','paired-d0']:
  start=epoch(read(R/'private/grade-deliveries'/(phase+'.json'))['preparedAtUTC']);end=max(epoch(read(R/'design/private/evaluation'/phase/anon/'SEAL.json')['payload']['sealed_at_utc'])for anon in grade_ids)
  grading[phase]={'startUTC':iso(start),'endUTC':iso(end),'wallSeconds':end-start,'scope':'Batch delivery until BOTH independent stage seals; includes service/queue intervals, not measured active reasoning.'}
 ledger=read(R/'private/phase-ledger.json');lower=epoch(ledger['engineeringStartLowerBoundUTC']);release=epoch(read(R/'private/assignment-release.json')['releasedAtUTC']);audit_rows=[r for rows in audits.values()for r in rows]
 experiment={'recordedEngineeringStartLowerBoundUTC':iso(lower),'formalAssignmentReleaseUTC':iso(release),'recordedLowerBoundWallSeconds':release-lower,'startScope':ledger['engineeringStartEvidence'],'scope':'Recorded engineering lower bound through formal release, including both parallel development loops, audit acquisitions, grading and gaps. Earlier unrecorded preparation and later documentation/publication/CI are not falsely claimed measured. Overlapping phase walls must not be added as a total.','auditAcquisitionWallSeconds':max(r['endUnix']for r in audit_rows)-min(r['startUnix']for r in audit_rows),'independentGrading':grading}
 return {'version':1,'scope':'Measured continuous development loops plus separately charged experiment acquisition. Segment sums are not active reasoning or uninterrupted throughput. Parallel command sums are not walls. All first translation attempts remain charged.','arms':arms,'experimentOnlyAcquisition':audits,'primaryBothLoopsEndUTC':iso(lastPrimary),'sameSourceD0Acquisition':pairs,'commonSetup':setup,'publicIntegrationCommands':{sid:native_records(R/'evidence/public-integration'/sid/'attempt-1')for sid in arms},'genericEngineeringAcquisition':{'nativeTests':generic['native_tests'],'snapshots':generic['snapshots'],'commandSumSeconds':sum(r['command_seconds']for r in generic['runs']),'scope':'Separate generic validation before fresh business design; not charged to either builder or counted as business samples.'},'fullRecordedExperiment':experiment,'modelUsage':{'tokens':None,'financialCost':None,'reason':'Host did not expose per-arm token/billing receipts. No estimate is substituted for measurement.'}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'cost-summary.json';d=compute()
 if a.write:assert not out.exists();out.write_text(json.dumps(d,indent=2)+'\n')
 else:assert read(out)==d,'Published cost summary does not reproduce'
 print(json.dumps({'status':'PASS','arms':{k:{'continuousWallSeconds':v['continuousWallSeconds'],'sequentialSegmentSumSeconds':v['sequentialSegmentSumSeconds'],'gapSeconds':v['barrierQueueAndUnallocatedGapSeconds']} for k,v in d['arms'].items()}}))
if __name__=='__main__':main()
