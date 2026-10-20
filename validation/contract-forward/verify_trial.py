#!/usr/bin/env python3
"""SDK-free provenance, immutable evidence and prospective-barrier checks."""
import hashlib,json
from collections import Counter
from datetime import datetime
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ts(v):return datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()
def checkfiles(root,items):
 for rel,h in items.items():assert sha(root/rel)==h,(root,rel)
def main():
 design=read(R/'design/private/DESIGN-SEAL.json');grader=read(R/'design/private/GRADER-SEAL.json')
 checkfiles(R/'design',design['files']);checkfiles(R/'design',grader['files']);assert read(R/'candidate-v6-freeze.json')['frozenAtUnix']<ts(design['sealed_at_utc'])
 assignment=read(R/'private/assignment.json');units=assignment['units'];aliases=assignment['gradeAliases'];sources={};reviews=[];repairs=[]
 for unit,config in units.items():
  base=R/'submissions'/unit
  for phase in ['d0','final']:
   cap=base/phase;seal=read(cap/'seal.json');checkfiles(cap/'source',seal['files']);checkfiles(cap,seal['upstreamLicenses']);sources[unit,phase]=seal
   assert set(seal['files'])=={str(p.relative_to(cap/'source'))for p in(cap/'source').rglob('*')if p.is_file()}
  records=[(name,read(base/folder/(name+'.json')),limit)for name,folder,limit in [('implementation','initial-agent-output',25),('review','original-review',12),('repair','final-agent-output',15)]]
  for name,record,limit in records:assert 0<=ts(record['end_utc'])-ts(record['start_utc'])<=limit*60,(unit,name)
  initial,review,repair=[r for _,r,_ in records];assert ts(design['sealed_at_utc'])<ts(initial['start_utc'])
  assert sources[unit,'d0']['sealedAtUnix']<=ts(review['start_utc'])<=ts(review['end_utc'])<=ts(repair['start_utc'])<=ts(repair['end_utc'])<=sources[unit,'final']['sealedAtUnix']
  reviews.append(ts(review['start_utc']));repairs.append(ts(repair['start_utc']))
  for archive in ['initial-agent-output','original-review','final-agent-output']:checkfiles(base/archive,read(base/archive/'portable-sha256.json'))
  for plan in (base/'initial-agent-output/plans').rglob('*'):
   if plan.is_file():assert sha(plan)==sha(base/'original-review/plans'/plan.relative_to(base/'initial-agent-output/plans')),'Plan edited during original review'
  for folder in ['own-inputs','own-inputs-final']:
   for rel,h in read(base/folder/'original-plan-binding.json')['files'].items():assert sha(base/rel)==h
   for case in ['P1','P2']:
    assert sha(base/folder/case/'fixtures.json')==sha(R/'design/public/cases'/case/'fixtures.json')
    for platform in ['ios','android']:
     strip=lambda xs:[{k:v for k,v in x.items()if k not in {'after_target','after_targets','observation_max_scrolls','observe_after'}}for x in xs]
     assert strip(read(base/folder/case/('actions.'+platform+'.json')))==strip(read(R/'design/public/cases'/case/('actions.'+platform+'.json')))
  effective=read(base/'effective-own-d0.json');assert effective['sealedAtUnix']<=ts(review['start_utc'])
 assert max(sources[u,'final']['sealedAtUnix']for u in units)<min(read(R/'own-corpora'/u/'final/started.json')['startedAtUnix']for u in units)
 deviation=read(R/'PROTOCOL-DEVIATIONS.json')['deviations'][0];assert deviation['earlyStartSeconds']==max(sources[u,'d0']['sealedAtUnix']for u in units)-min(read(R/'own-corpora'/u/'d0/started.json')['startedAtUnix']for u in units)and deviation['earlyStartSeconds']>0
 assert max(sources[u,'d0']['sealedAtUnix']for u in units)<=min(reviews)
 assert max(read(R/'submissions'/u/'effective-own-d0.json')['sealedAtUnix']for u in units)<=min(reviews)
 final_inputs=read(R/'private/common-inputs-final/seal.json');assert max(read(R/'own-corpora'/u/'final/corpus-seal.json')['sealedAtUnix']for u in units)<final_inputs['createdAtUnix']
 registry=[]
 for unit,c in units.items():
  for phase in ['d0','final']:registry.append((R/'own-corpora'/unit/phase,unit,phase,c['tool'],'own-inputs'if phase=='d0'else'own-inputs-final',4))
  for phase in ['d0','final']:
   path=R/'own-retries'/unit/phase
   if path.is_dir():registry.append((path,unit,phase,c['tool'],'own-inputs'if phase=='d0'else'own-inputs-final',1))
 for alias,unit in aliases.items():
  for phase,n in [('d0',4),('final',6)]:registry.append((R/'common-corpora'/alias/phase,unit,phase,'candidate-v6',None,n))
  registry.append((R/'paired-corpora'/alias/'v5',unit,'d0','baseline-v5',None,4))
 counts=Counter();snapshots=0
 for path,unit,phase,tool,own,n in registry:
  checkfiles(path,read(path/'portable-sha256.json'));seal=read(path/'corpus-seal.json');assert sha(path/'portable-sha256.json')==seal['portableManifestSHA256']
  corpus=read(path/'corpus.json');started=read(path/'started.json');assert corpus['source']==started['source']==seal['source']==sources[unit,phase]['files'];assert corpus['tool']==tool
  assert sources[unit,phase]['sealedAtUnix']<=started['startedAtUnix']
  if 'operatorSHA256'in started:assert sha(path/'operator-source.py')==started['operatorSHA256']
  runs=[(p,r)for p,rows in corpus['platformRuns'].items()for r in rows];assert len(runs)==n,(path,len(runs),n)
  for platform,row in runs:
   counts['commands']+=1;counts['nonzeroExits']+=row['exitCode']!=0;capture=path/platform/row['case'];assert abs(row['wallSeconds']-(row['finishedAtUnix']-row['startedAtUnix']))<1e-6
   inputs=(R/'submissions'/unit/own if own else R/'private'/('common-inputs-'+phase))/row['case'];actions=inputs/('actions.'+platform+'.json');fixture=inputs/'fixtures.json'
   assert row['inputHashes']=={'fixtures.json':sha(fixture),actions.name:sha(actions)}
   if not(capture/'observation.json').is_file():
    assert row['exitCode']==2 and phase=='d0'and own and platform=='ios'and row['case']=='P2','Missing native observation is not an allowed success'
    counts['retainedPreNativeWidthFailures']+=1;continue
   obs=read(capture/'observation.json');native=read(capture/'manifest.json');assert native['input_hashes']=={'fixtures':sha(fixture),'actions':sha(actions)}
   assert native['native_test_count']==1;checkfiles(capture,native['image_hashes']);snapshots+=len(obs['snapshots'])
   for original,h in native['source_hashes'].items():
    for version in ['baseline-v5','candidate-v6','runtime-baseline-v5','runtime-candidate-v6']:
     token='/'+version+'/'
     if token in original:assert sha(R/version/original.split(token,1)[1])==h,(capture,original)
    for bridge in ['Bridge.swift','ObserverBridge.kt']:
     if original.endswith('/design/public/'+bridge):assert sha(R/'design/public'/bridge)==h
    for prefix in ['alerttoast/Sources/','reply/Reply/app/src/main/']:
     token='/'+prefix
     if token in original:assert sources[unit,phase]['files'][prefix+original.split(token,1)[1]]==h
 for phase in ['d0','final']:checkfiles(R/'private'/('common-inputs-'+phase),read(R/'private'/('common-inputs-'+phase)/'seal.json')['files'])
 release=read(R/'private/ASSIGNMENT-RELEASE.json');last=None
 for stage in ['D0','FINAL','selfreview','paired-D0']:
  folder=R/'evaluation'/stage;seal=read(folder/'SEAL.json');delivery=read(R/'evaluation-inputs'/stage/'DELIVERY-SEAL.json');checkfiles(folder,seal['files']);checkfiles(R/'evaluation-inputs'/stage,delivery['files'])
  assert sha(folder/'SEAL.json')==release['stageSeals'][stage]['sealSHA256'];end=ts(seal['sealedAtUTC']);assert delivery['sealedAtUnix']<=end<release['releasedAtUnix']
  if last is not None:assert last<=delivery['sealedAtUnix']
  last=end
 assert release['gradeAliases']==aliases
 addendum=R/'evaluation/factual-addenda';checkfiles(addendum,read(addendum/'SEAL.json')['files'])
 assert counts['commands']==46 and counts['retainedPreNativeWidthFailures']==2
 for unit in units:
  effective=read(R/'submissions'/unit/'effective-own-d0.json');assert len(effective['missingOriginalRetries'])==1
  assert effective['missingOriginalRetries'][0]['case']=='P2'
 checkfiles(R,read(R/'private/claim-protocol-seal.json')['files'])
 assert read(R/'private/claim-protocol-seal.json')['recordedAtUnix']<min(ts(read(R/'submissions'/u/'original-review/review.json')['end_utc'])for u in units)
 paired=read(R/'private/paired-acquisition-scheduling.json');assert max(paired['primaryEndpoints'].values())<paired['recordedAtUnix']<min(read(R/'paired-corpora'/a/'v5/started.json')['startedAtUnix']for a in aliases)
 print(json.dumps({'status':'PASS',**counts,'rawSnapshots':snapshots,'scope':'All native trial commands, including failed original width calls and explicit shared retries; native neutral probes accounted separately.'}))
if __name__=='__main__':main()
