from pathlib import Path
import json,hashlib,datetime,collections,importlib.util,sys
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/state-forward');I=R/'evaluation-inputs/selfreview';O=R/'evaluation/selfreview';D=R/'design/private'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
s=importlib.util.spec_from_file_location('frozen_compare_claim_panels',D/'compare.py');compare=importlib.util.module_from_spec(s);s.loader.exec_module(compare)
batch=json.loads((I/'batch.json').read_text());summary=json.loads((O/'SUMMARY.json').read_text())
for arm in batch['corpora']:
 aid=arm['anonymousID'];p=Path(arm['originalReviewDirectory']);review=json.loads((p/'review.json').read_text());cr=json.loads((O/aid/'claims.json').read_text());g0=json.loads(Path(arm['independentD0Grade']).read_text());gf=json.loads(Path(arm['independentFinalGrade']).read_text());interpretations={}
 if aid=='source-a':
  for x in json.loads((p/'review-original/all-failures.json').read_text()):interpretations[(x['platform'],x['original_row']['id'])]=x
 else:
  for x in review['typed_failures']:interpretations[(x['platform'],x['original_result']['id'])]=x
 for c in cr['claims']:
  if c['origin']=='typed':
   x=interpretations.get((c['platform'],c['original']['assertion']['id']));c['producerInterpretation']=x;c['producerInterpretationNote']='Original interpretation retained separately from the actual typed failed flag. Raw-checker panels assess failed flags; a producer limitation/rebuttal is not an extra positive product claim.'
 save(O/aid/'claims.json',cr)
 # Recompute with the exact same frozen comparison function after adding original provenance; adjudications remain unchanged.
 result=compare.compare(g0,gf,cr);save(O/aid/'comparison.json',result)
 original=[c for c in cr['claims'] if c['reportSeries']!='review-semantic-diagnostics'];save(O/aid/'comparison-original-reports-only.json',compare.compare(g0,gf,dict(claims=original)))
 def panel(cs):
  x=compare.compare(g0,gf,dict(claims=cs))['reviewMatching'];return dict(positiveClaims=len(cs),claimCounts=x['claimCounts'],conditionalFalseDiscoveryShare=x['conditionalFalseDiscoveryShare'],allUncertainConservativeInterval=x['allUncertainConservativeInterval'],classicalFPR=None,manualDetectedRows=len(x['manualDetectedRows']),actualTypedDetectedRows=len(x['actualTypedDetectedRows']),combinedDetectedRows=len(x['combinedDetectedRows']))
 groups={'manual_only':[c for c in cr['claims'] if c['origin']=='manual'],'actual_original_typed_reports':[c for c in cr['claims'] if c['origin']=='typed' and c['reportSeries']=='review-original'],'actual_diagnostic_typed_reruns':[c for c in cr['claims'] if c['origin']=='typed' and c['reportSeries']=='review-semantic-diagnostics'],'manual_plus_original_typed':original,'manual_plus_all_actual_typed':cr['claims']}
 byorigin={k:panel(v) for k,v in groups.items()};byclass={}
 for cls in sorted({c['classification'] for c in cr['claims']}):byclass[cls]=panel([c for c in cr['claims'] if c['classification']==cls])
 bystate={}
 for state in sorted({c['stateID'] for c in cr['claims']}):bystate[state]=panel([c for c in cr['claims'] if c['stateID']==state])
 save(O/aid/'claim-panels.json',dict(byOrigin=byorigin,byClass=byclass,byState=bystate,interpretation='False-discovery panels refer to actual raw failed-check flags and explicit manual positive claims under frozen requirements. Original reviewers also explicitly classify many flags as transport/float/viewport limitations; those qualifiers remain on each claim and in the ledger, and are not separate positive faults. Original U/pass/limitations do not enter positive-claim counts. Repeated diagnostic checks are shown separately; unique detected-cell sets never count repeats.',deduplication='Every actual failed typed row remains preserved and eligible. Original-only versus all-actual panels expose denominator effects of diagnostic reruns.'))
 summary['corpora'][aid]['claimPanelsByOrigin']=byorigin
 # Verify complete positive failed-row extraction independently of any machine_findings field or producer aggregate schema.
 audit=json.loads((O/aid/'matching-audit.json').read_text());reports=audit['actualReportProvenance'];expected=sum(x['counts']['failed'] for x in reports);actual=sum(c['origin']=='typed' for c in cr['claims']);assert expected==actual
 assert len(cr['claims'])==len({c['claimID'] for c in cr['claims']})
 for c in cr['claims']:
  for m in c['matches']:
   if m['adjudication']=='exact':assert next(x for x in g0['rows'] if x['cellID']==m['cellID'])['status']=='F'
 rows=json.loads((O/aid/'fixed-failure-detection-ledger.json').read_text())['rows'];assert len(rows)==sum(x['status']=='F' and x['classification'].startswith('runtime.') for x in g0['rows'])
 audit['completenessChecks']=dict(allActualFailedTypedRows=expected,preservedEligibleTypedClaims=actual,allPositiveManualClaims=sum(c['origin']=='manual' for c in cr['claims']),noMachineFindingsDependency=True,allNaturalFailedRowsRetained=len(rows),everyExactMatchWasOriginalD0F=True)
 save(O/aid/'matching-audit.json',audit)
summary['notes']+=['Raw failed-check false-discovery is reported separately from manual findings and producer qualifications; original explicit U/limitations are never positive claims by default.','All original failed typed reports, including actual supplemental pre-repair diagnostic reruns, are eligible and retained; original-only panels prevent repeat reports from obscuring metrics.']
save(O/'SUMMARY.json',summary)
# Preserve the already-sealed quality stages and frozen evaluator byte-exact.
for stage in ['D0','FINAL']:
 d=R/'evaluation'/stage;s=json.loads((d/'SEAL.json').read_text());assert all(sha(d/x['path'])==x['sha256'] for x in s['files'])
for sealname,key in [('GRADER-SEAL.json','gradingFiles'),('DESIGN-SEAL.json','files')]:
 s=json.loads((D/sealname).read_text());assert all(sha(R/'design'/x['path'])==x['sha256'] for x in s[key])
start=json.loads((O/'phase-costs.json').read_text())['startedAtUTC'];end=now();wall=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds();save(O/'phase-costs.json',dict(stage='selfreview',startedAtUTC=start,endedAtUTC=end,continuousEvaluationWallSeconds=wall,scope='Both original simultaneous reviews/reports, source-free matching, own-D0 claim screenshot inspection and hash checks. No new native run, source repair or tool amendment.',phases=['Delivery/seal verification and original format-neutral extraction','Actual typed-row/plan/raw receipt matching and manual image review','Frozen comparisons, class/origin/miss/repair panels and both-output seal'],costAttribution='Independent experiment evaluation only; not builder review/repair time and not treatment benefit.'))
files=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts:files.append(dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size))
aggregate=hashlib.sha256(''.join(x['path']+'\0'+x['sha256']+'\n' for x in files).encode()).hexdigest();save(O/'SEAL.json',dict(schemaVersion=1,stage='selfreview',sealedAtUTC=now(),aggregateSHA256=aggregate,files=files,anonymousIDs=['source-a','source-b'],frozenCompareSHA256=sha(D/'compare.py'),qualityStagesUnchanged=True,noPairedDataRead=True,noAssignmentRead=True,originalClaimImageReferencesReviewed=71,originalOnlyAndAllActualTypedPanels=True,formatNeutralFailedRowEligibility=True))
print(json.dumps(dict(aggregateSHA256=aggregate,fileCount=len(files),wallSeconds=wall,counts={a:{k:v for k,v in x.items() if k in ['naturalD0FRows','manualDetected','actualTypedDetected','combinedDetected','fixedRowTransitions']} for a,x in summary['corpora'].items()}),indent=2))
