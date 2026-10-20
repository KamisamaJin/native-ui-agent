#!/usr/bin/env python3
"""Verify prospective source/input witnesses, phase barriers and native archives."""
import hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ts(s):
 if s.endswith(' UTC'):return datetime.strptime(s,'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc).timestamp()
 return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def listed(items):return items.items()if isinstance(items,dict)else[(r['path'],r['sha256'])for r in items]
def checkfiles(base,items):
 for rel,h in listed(items):assert sha(base/rel)==h,rel
def main():
 design=read(R/'design/private/DESIGN-SEAL.json');grader=read(R/'design/private/GRADER-SEAL.json')
 checkfiles(R/'design',design['files']);checkfiles(R/'design',grader['gradingFiles'])
 assert ts(read(R/'candidate-v5-freeze.json')['frozenAtUTC'])<ts(design['sealedAtUTC'])
 sources={};reviews=[];initial=[];final=[]
 for unit in ['unit-93485d','unit-fb632e']:
  base=R/'submissions'/unit
  for stage in ['d0','final']:
   cap=base/stage;seal=read(cap/'seal.json');checkfiles(cap/'source',seal['files']);checkfiles(cap,seal['upstreamLicenses'])
   sources[unit,stage]=seal
   assert set(seal['files'])=={str(p.relative_to(cap/'source'))for p in(cap/'source').rglob('*')if p.is_file()}
  initial_report=read(base/'initial-agent-output/implementation.json');review=read(base/'original-review/review.json');repair=read(base/'final-agent-output/repair.json')
  assert ts(design['sealedAtUTC'])<ts(initial_report['start_utc']);initial.append(ts(initial_report['start_utc']))
  for name,archive in [('plans','initial-agent-output'),('review','original-review')]:
   seal=read(base/archive/(name+'-seal.json'))
   for field in ['files','supporting_scripts']:
    for rel,h in listed(seal.get(field,{})):
     relative=Path(rel).relative_to('agent-output');assert sha(base/archive/relative)==h,(unit,rel)
     assert sha(base/'final-agent-output'/relative)==h,(unit,'changed after seal',rel)
  checkfiles(base/'own-inputs',read(base/'own-inputs/original-plan-binding.json')['files'])
  assert sources[unit,'d0']['sealedAtUnix']<=ts(review['start_utc'])
  assert ts(review['end_utc'])<=ts(repair['start_utc'])<=ts(repair['end_utc'])<=sources[unit,'final']['sealedAtUnix']
  for name,record,limit in [('implementation',initial_report,25),('review',review,12),('repair',repair,15)]:
   assert 0<=ts(record['end_utc'])-ts(record['start_utc'])<=limit*60,(unit,name)
  reviews.append(ts(review['start_utc']));final.append(sources[unit,'final']['sealedAtUnix'])
 assert max(sources[u,'d0']['sealedAtUnix']for u in ['unit-93485d','unit-fb632e'])<=min(reviews)
 assert max(read(R/'own-corpora'/u/'d0/corpus-seal.json')['sealedAtUnix']for u in ['unit-93485d','unit-fb632e'])<=min(reviews)
 assert max(final)<ts(read(R/'private/common-inputs-final/seal.json')['createdAtUTC'])
 for stage in ['d0','final']:
  checkfiles(R/'private'/('common-inputs-'+stage),read(R/'private'/('common-inputs-'+stage)/'seal.json')['files'])
 registry=[]
 for unit,tool in [('unit-93485d','candidate-v5'),('unit-fb632e','baseline-v4')]:
  for stage in ['d0','final']:registry.append((R/'own-corpora'/unit/stage,unit,stage,tool,4))
 assignment=read(R/'private/grade-assignment.json')['mapping']
 for alias,unit in assignment.items():
  for stage,n in [('d0',4),('final',6)]:registry.append((R/'common-corpora'/alias/stage,unit,stage,'candidate-v5',n))
  registry.append((R/'paired-corpora'/alias/'v4',unit,'d0','baseline-v4',4))
 counts=Counter();snapshots=0
 for path,unit,stage,tool,n in registry:
  seal=read(path/'corpus-seal.json');checkfiles(path,read(path/'portable-sha256.json'))
  assert sha(path/'portable-sha256.json')==seal['portableManifestSHA256']
  corpus=read(path/'corpus.json');started=read(path/'started.json')
  assert corpus['source']==started['source']==seal['source']==sources[unit,stage]['files']
  assert corpus['tool']==tool and sources[unit,stage]['sealedAtUnix']<=started['startedAtUnix']
  if 'operatorSHA256'in started:assert sha(path/'operator-source.py')==started['operatorSHA256']
  for platform,runs in corpus['platformRuns'].items():
   assert len(runs)==n
   for row in runs:
    capture=path/platform/row['case'];native=read(capture/'manifest.json');observation=read(capture/'observation.json')
    inputs=(R/'submissions'/unit/'own-inputs' if path.is_relative_to(R/'own-corpora') else R/'private'/('common-inputs-'+stage))/row['case']
    actions=inputs/('actions.'+platform+'.json')
    if not actions.exists():actions=inputs/'actions.json'
    assert native['input_hashes']=={'fixtures':sha(inputs/'fixtures.json'),'actions':sha(actions)}
    assert row['inputHashes']=={'fixtures.json':sha(inputs/'fixtures.json'),actions.name:sha(actions)}
    assert native['native_test_count']==1,(capture,'not a real native test')
    checkfiles(capture,native['image_hashes']);snapshots+=len(observation['snapshots'])
    assert row['finishedAtUnix']>=row['startedAtUnix']
    assert abs(row['wallSeconds']-(row['finishedAtUnix']-row['startedAtUnix']))<1e-6
    counts['commands']+=1;counts['nonzeroExits']+=row['exitCode']!=0
    # Actual native production source hashes must agree with sealed capsules.
    for original,h in native['source_hashes'].items():
     token='/'+tool+'/'
     if token in original:assert sha(R/tool/original.split(token,1)[1])==h,(capture,original)
     if original.endswith('/design/public/Bridge.swift'):assert sha(R/'design/public/Bridge.swift')==h
     if original.endswith('/design/public/ObserverBridge.kt'):assert sha(R/'design/public/ObserverBridge.kt')==h
     for prefix in ['alerttoast/Sources/','reply/Reply/app/src/main/']:
      token='/'+prefix
      if token in original:
       rel=prefix+original.split(token,1)[1];assert sources[unit,stage]['files'][rel]==h,(capture,rel)
 assert counts['commands']==88,counts
 release=read(R/'private/ASSIGNMENT-RELEASE.json');previous=None
 for stage in ['D0','FINAL','selfreview','paired-D0']:
  grade=read(R/'evaluation'/stage/'SEAL.json');delivery=read(R/'evaluation-inputs'/stage/'DELIVERY-SEAL.json')
  assert sha(R/'evaluation'/stage/'SEAL.json')==release['stageSeals'][stage]['sealSHA256']
  sealed=ts(grade['sealedAtUTC']);assert delivery['sealedAtUnix']<=sealed<release['releasedAtUnix']
  if previous is not None:assert previous<=delivery['sealedAtUnix'],'Next batch supplied before both prior outputs sealed'
  previous=sealed
 assert release['gradeAliases']==assignment
 assert read(R/'private/paired-acquisition-scheduling.json')['recordedAtUnix']<min(read(R/'paired-corpora'/alias/'v4/started.json')['startedAtUnix']for alias in assignment)
 print(json.dumps({'status':'PASS','plannedNativeCommands':counts['commands'],'retainedNonzeroExits':counts['nonzeroExits'],'rawSnapshots':snapshots,'barriers':'tool/design/source/review/repair/holdout verified'}))
if __name__=='__main__':main()
