#!/usr/bin/env python3
"""Freeze both independent FINAL grades only after final capture inventory confirmation.

The external-facing seal deliberately contains no outcome counts/findings.
All grading, method limits, strict state/aspect/group rollups stay in private grade
artifacts. Source/input/evidence inventories are separately hashed commitments.
"""
import argparse,collections,datetime,hashlib,importlib.util,json,pathlib,shutil,sys
import raw_review as rr
HERE=rr.HERE;EVAL=HERE.parent;ROOT=rr.ROOT
spec=importlib.util.spec_from_file_location('sealed_preparation_evaluator',EVAL/'evaluator.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
def write_new(p,x):
 if p.exists():raise RuntimeError('Refusing overwrite of seal artifact '+str(p))
 p.parent.mkdir(parents=True,exist_ok=True);rr.write(p,x)
def rel(p):return str(p.relative_to(ROOT))
def item(p):return dict(path=rel(p),sha256=rr.sha(p),bytes=p.stat().st_size)
def count(rows):return ev.rollup(rows)
def supplement(grade):
 rows=grade['results'];groups={};states={};cases={};aspects={};missing=collections.defaultdict(list)
 for r in rows:
  pl=r['platform'];cid=r['contextId'];case=cid.split('/')[0] if cid else 'COMMON'
  states.setdefault(pl+'/'+(cid or 'COMMON'),[]).append(r);cases.setdefault(pl+'/'+case,[]).append(r);aspects.setdefault(pl+'/'+(cid or 'COMMON')+'/'+r['aspect'],[]).append(r)
  if r.get('parameterizedGroupKey'):groups.setdefault(pl+'/'+r['parameterizedGroupKey'],[]).append(r)
  if r['outcome']=='UNASSESSED':
   for method in r['missingEvidenceMethod']:missing[pl+'/'+method].append(dict(assessmentId=r['assessmentId'],contextId=cid,missingEvidenceDetail=r['missingEvidenceDetail'],requiredBinding=r['requiredBinding'],consideredSources=r['consideredSources']))
 clusters=collections.defaultdict(list)
 for r in rows:
  if r['outcome']!='FAIL':continue
  key=r['key']
  if 'representativeColors/' in key and ('disabled' in key.lower()):c='disabled-primary-raster-color-mismatch'
  elif 'horizontalOverflow' in key or 'visibleText/notes.title' in key:c='notes-title-raster-clipping'
  elif r['criterion']=='documentedIdentifierSetEquals':c='documented-native-identifier-set-mismatch'
  elif r['aspect']=='actualCallbacks':c='observed-callback-interval-mismatch'
  else:c='other-'+r['criterion']
  clusters[r['platform']+'/'+c].append(dict(assessmentId=r['assessmentId'],contextId=r['contextId'],criterion=r['criterion'],reason=r['reason'],exactSources=r['exactSources']))
 return dict(candidateId=grade['candidateId'],phase='FINAL',requiredAssessmentCount=2897,exactKeyCoverage=True,
  caseRollups={k:count(v) for k,v in cases.items()},stateRollups={k:count(v) for k,v in states.items()},stateAspectRollups={k:count(v) for k,v in aspects.items()},
  parameterizedGroups={k:dict(**count(v),mandatoryMemberAssessmentIds=[r['assessmentId'] for r in v]) for k,v in groups.items()},
  unassessedByRequiredMethod={k:dict(count=len(v),members=v) for k,v in missing.items()},
  actualActivationMethods={r['assessmentId']:r.get('nativeActivationObservation') for r in rows if r['criterion']=='executedNativeActivation'},
  defectClusters={k:dict(memberAssessmentIds=[r['assessmentId'] for r in v],members=v) for k,v in clusters.items()},
  callbackInterpretation='Actual count/payload mismatches remain separate from delivered-stimulus proof. When actual dispatch is unavailable, these interval facts do not establish a defective business handler.',
  scope='Strict outcomes cover the frozen enumerated atomic matrix only; unknown mandatory members prevent their case/state/aspect/group/public rule from passing.')
def inventories(sub,packet,ledger):
 sourceRoot=ROOT/'validation/tool-forward/implementations/final'/sub;seal=sourceRoot/'manifest.json';files=rr.load(seal)['files'];source=[]
 for path,h in files.items():
  p=sourceRoot/path
  if rr.sha(p)!=h:raise ValueError('Business source seal mismatch')
  source.append(item(p))
 source += [item(seal),item(ROOT/'validation/tool-forward/common-host/Package.swift'),item(ROOT/'validation/tool-forward/common-host/PROVENANCE.json'),item(ROOT/'validation/tool-forward/final-source-application.json')]
 application=rr.load(ROOT/'validation/tool-forward/final-source-application.json')
 hosts=[x for x in application['hosts'] if x['submission']==sub]
 if len(hosts)!=2 or any(x['files']!=files or x['source_manifest_sha256']!=rr.sha(seal) for x in hosts):raise ValueError('Neutral final host source linkage mismatch')
 frozenInputs=ROOT/'validation/tool-forward/private/inputs/final';inputManifest=rr.load(frozenInputs/'manifest.json')
 if inputManifest['oracle_sha256']!=rr.sha(EVAL.parent/'oracle.json'):raise ValueError('Prepared input oracle commitment mismatch')
 nativeBindings=[];inputs=[];used={};captureFacts=[]
 for pl in ['android','apple']:
  for case in ['C01','C02','C03','C04','C05','C06','H01','H02']:
   p,o,cap,fx,m=rr.data(sub,pl,case)
   portable=rr.load(p/'portable-sha256.json')
   snapshotPaths=[p/s['screenshot'] for s in o['snapshots']]
   rawFiles=[p/name for name in ['fixtures.json','capture.json','manifest.json','observation.json']]+snapshotPaths
   for raw in rawFiles:
    if p.resolve() not in raw.resolve().parents:raise ValueError('Raw reference leaves permitted case')
    key=str(raw.relative_to(p))
    if portable.get(key)!=rr.sha(raw):raise ValueError('Portable raw commitment mismatch '+str(raw))
    used[str(raw)]=raw
   captureFacts.append(dict(platform=pl,caseId=case,originalCaptureStatus=cap.get('status'),originalNativeExitCode=cap.get('exit_code'),actualSnapshotCount=len(o['snapshots']),actualScreenshotFiles=[item(q) for q in snapshotPaths],interpretation='Raw capture/exit facts are preserved as observed provenance; status names or native exit alone are not business quality outcomes.'))
   observed={pathlib.Path(k).name:v for k,v in m['source_hashes'].items() if pathlib.Path(k).name in ['ReturnResolutionCard.kt','ReturnResolutionModels.kt','ReturnResolutionCard.swift','ReturnResolutionModels.swift','Package.swift']}
   if pl=='apple' and observed.get('Package.swift')!=rr.sha(ROOT/'validation/tool-forward/common-host/Package.swift'):raise ValueError('Native manifest does not bind the provided neutral package source')
   nativeBindings.append(dict(platform=pl,caseId=case,nativeManifest=item(p/'manifest.json'),observedSourceHashes=observed))
   models=[x.get('model',x) for x in [fx['initial']]+fx.get('updates',[])]
   preparedPath=frozenInputs/(case+'.json');prepared=rr.load(preparedPath);preparedSHA=rr.sha(preparedPath)
   if next(x['sha256'] for x in inputManifest['cases'] if x['case']==case)!=preparedSHA or cap.get('source_fixture_sha256')!=preparedSHA:raise ValueError('Prepared/native input hash linkage mismatch')
   if models!=[prepared['model']]+prepared.get('updates',[]):raise ValueError('Prepared/native complete models mismatch')
   contexts=[]
   for cid,c in rr.CTX.items():
    if c['caseId']!=case:continue
    pr=next(x for x in cap['action_protocol'] if x['checkpoint']==c['stateId']);actual=models[pr['input_index']]
    if actual!=c['model']:raise ValueError('Input model mismatch '+sub+'/'+pl+'/'+cid)
    contexts.append(dict(contextId=cid,modelId=c['modelId'],inputIndex=pr['input_index'],actualCanonicalModelSHA256=ev.sha(ev.canonical(actual)),frozenModelSHA256=c['modelSha256'],environmentSHA256=c['environmentSha256'],protocol=pr))
   inputs.append(dict(platform=pl,caseId=case,frozenPreparedCase=item(preparedPath),actualCaptureSourceFixtureSHA256=cap.get('source_fixture_sha256'),fixtures=item(p/'fixtures.json'),capture=item(p/'capture.json'),models=len(models),checkpoints=contexts))
   for name in ['fixtures.json','capture.json','manifest.json','observation.json','portable-sha256.json']:used[str(p/name)]=p/name
 for rec in packet['records']:
  for ref in rec['rawRefs']:
   if rec['method']!='sourceAudit':used[ref['path']]=pathlib.Path(ref['path'])
 for e in ledger['assessments']:
  for ref in e.get('binding',{}).get('provenanceRefs',[]):used[ref['path']]=pathlib.Path(ref['path'])
 return dict(source=dict(candidateId=sub,scope='Sealed production source plus explicit common package provenance and neutral final source application; report contents and host workspaces not read.',files=source,neutralHostSourceRecords=hosts,nativeBusinessBindings=nativeBindings),inputs=dict(candidateId=sub,scope='All actual C01..C06/H01/H02 complete input models and exact protocol/checkpoint correlations, both platforms.',preparedManifest=item(frozenInputs/'manifest.json'),cases=inputs),evidence=dict(candidateId=sub,scope='Every actual raw artifact cited by the assessment or its binding, all sixteen native observation/capture/input/manifest JSON sets and every screenshot referenced by every actual snapshot, each verified against its published portable commitment. No tool/compiled-project/source helper code is read.',nativeCaptureFacts=captureFacts,files=[item(p) for p in sorted(used.values())]))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--all-inventory-confirmed',action='store_true');args=parser.parse_args()
 if not args.all_inventory_confirmed:raise RuntimeError('Wait for coordinator final capture inventory; do not freeze incremental missing cases as final unknowns.')
 sealPath=EVAL/'final-grades-seal.json'
 if sealPath.exists():raise RuntimeError('Both FINAL grades already sealed; no rewrite')
 if rr.sha(EVAL/'d0-grades-seal.json')!='f0971f33f53d90473db71590abf471c2e36af1ccfbb3a6645b2e373684f733b7':raise ValueError('Prior D0 seal changed')
 if rr.sha(EVAL/'preparation-manifest.json')!='89ddc9a1124218408076f6a06152723e6a04604ae4e0515355e1b28f095d305c':raise ValueError('Preparation seal changed')
 revision=EVAL.parent.parent;freeze=rr.load(revision/'freeze-manifest.json');prep=rr.load(EVAL/'preparation-manifest.json')
 for record in freeze['mainArtifacts']+freeze['supportingArtifacts']+prep['files']:
  p=pathlib.Path(record['path'])
  if revision.resolve() not in p.resolve().parents:raise ValueError('Frozen record is outside permitted selected design')
  if rr.sha(p)!=record['sha256']:raise ValueError('Frozen design/preparation artifact changed: '+str(p))
 plan,ctx=ev.expand(ev.frozen_oracle(),'FINAL');expected={r['assessmentId'] for r in plan['assessments']};dest=EVAL/'final-sealed';commitments=[];prepared=[]
 if dest.exists():raise RuntimeError('Refusing overwrite of an earlier FINAL seal directory')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 staging=HERE/('joint-seal-preflight-'+stamp);staging.mkdir(exist_ok=False)
 for sub in ['submission-b2e249','submission-4f4364']:
  src=HERE/sub;packet=rr.load(src/'raw-index.json');ledger=rr.load(src/'decision-ledger.json')
  if ledger.get('pendingNotGraded'):raise RuntimeError('Unfinished incremental candidate inventory')
  ids=[x['assessmentId'] for x in ledger['assessments']]
  if len(ids)!=2897 or len(set(ids))!=2897 or set(ids)!=expected:raise RuntimeError('Missing/duplicate/unexpected atomic decisions')
  sd=staging/sub;sd.mkdir(parents=True,exist_ok=False)
  pp=sd/'evidence-index.json';lp=sd/'decision-ledger.json';write_new(pp,packet);write_new(lp,ledger)
  vp=sd/'visual-review-ledger.json';write_new(vp,rr.load(src/'visual-review-ledger.json'))
  gp=sd/'grade.json';base=sd/'assembled-base.json';eroot=ROOT/'validation/tool-forward/evidence/final'/sub;sroot=ROOT/'validation/tool-forward/implementations/final'/sub
  ev.assemble('FINAL',sub,pp,lp,base,[eroot/'android',eroot/'ios'],[sroot/'reply',sroot/'alerttoast',ROOT/'validation/tool-forward/common-host/Package.swift'])
  grade=rr.load(base);decisions={e['assessmentId']:e for e in ledger['assessments']};records={r['id']:r for r in packet['records']}
  for r in grade['results']:
   e=decisions[r['assessmentId']];r['actualObservedValue']=e.get('observedValue')
   if r['criterion']=='executedNativeActivation':
    r['nativeActivationObservation']=[dict(evidenceRecordId=eid,observedActivationMechanism=records[eid].get('observedActivationMechanism'),facts=records[eid].get('observation')) for eid in e['evidenceRecordIds']]
  ev.validate_report(grade)
  if any(r['outcome']!=decisions[r['assessmentId']]['outcome'] for r in grade['results']):raise RuntimeError('Assembly found a decision/evidence-method inconsistency; inspect the preflight before sealing')
  write_new(gp,grade)
  ap=sd/'coverage-and-method-audit.json';write_new(ap,supplement(grade));inv=inventories(sub,packet,ledger);paths={}
  for key,x in inv.items():
   p=sd/(key+'-inventory.json');write_new(p,x);paths[key+'Inventory']=item(p)
  prepared.append(dict(sub=sub,staged=sd,inventory=inv))
 # Both full assemblies and raw commitments must succeed before the immutable
 # grade tree is created. Recheck all source/evidence bytes after assembly.
 for obj in prepared:
  for kind in ['source','evidence']:
   for record in obj['inventory'][kind]['files']:
    if rr.sha(ROOT/record['path'])!=record['sha256']:raise ValueError('Raw/source bytes changed during joint preflight')
 dest.mkdir(exist_ok=False)
 for obj in prepared:
  sub=obj['sub'];stage=obj['staged'];sd=dest/sub;sd.mkdir(exist_ok=False)
  for name in ['evidence-index.json','decision-ledger.json','visual-review-ledger.json','assembled-base.json','coverage-and-method-audit.json','source-inventory.json','inputs-inventory.json','evidence-inventory.json']:
   shutil.copyfile(stage/name,sd/name)
  grade=rr.load(stage/'grade.json')
  grade['packetExactSource']=dict(path=str(sd/'evidence-index.json'),sha256=rr.sha(sd/'evidence-index.json'))
  grade['ledgerExactSource']=dict(path=str(sd/'decision-ledger.json'),sha256=rr.sha(sd/'decision-ledger.json'))
  ev.validate_report(grade);gp=sd/'grade.json';write_new(gp,grade)
  paths={kind+'Inventory':item(sd/(kind+'-inventory.json')) for kind in ['source','inputs','evidence']}
  commitments.append(dict(candidateId=sub,grade=item(gp),coverageAndMethodAudit=item(sd/'coverage-and-method-audit.json'),evidenceIndex=item(sd/'evidence-index.json'),decisionLedger=item(sd/'decision-ledger.json'),visualReviewLedger=item(sd/'visual-review-ledger.json'),**paths,requiredAssessmentCount=2897))
 method=dest/'independent-grader';method.mkdir()
 for name in ['raw_review.py','grade_d0.py','pixel_measurements.py','focus_review.py','seal_final.py','record_reviews.py','manual-reviews.json','adapter-notes.md','initialization-commitment.json','source-application-audit.json','observation-entry-corrections.json','complete-coverage-provenance-preflight.json']:
  shutil.copyfile(HERE/name,method/name)
 methodManifest=dest/'grader-files.json';write_new(methodManifest,dict(preparationManifest=item(EVAL/'preparation-manifest.json'),files=[item(p) for p in sorted(method.iterdir())]))
 sealedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 fileManifest=EVAL/'final-files-manifest.json';write_new(fileManifest,dict(phase='FINAL',sealedAtUTC=sealedAt,files=[item(p) for p in sorted(dest.rglob('*')) if p.is_file()],qualityResultsIntentionallyOmitted=True))
 write_new(sealPath,dict(schemaVersion=1,phase='FINAL',sealedAtUTC=sealedAt,selectedOracleSHA256=rr.sha(EVAL.parent/'oracle.json'),preparationManifestSHA256=rr.sha(EVAL/'preparation-manifest.json'),priorD0Seal=item(EVAL/'d0-grades-seal.json'),scope='Both anonymous main-collector final grades complete and independently sealed before any self-review/assignment matching. Procedural blindness on a shared filesystem; no OS isolation claim.',gradeCommitments=commitments,graderFiles=item(methodManifest),fileManifest=item(fileManifest),qualityResultsIntentionallyOmitted=True,assignmentOrSelfReviewRead=False))
 print(json.dumps(dict(seal=rel(sealPath),sha256=rr.sha(sealPath),sealedAtUTC=sealedAt,requiredAssessmentsPerSubmission=2897),indent=2))
if __name__=='__main__':main()
