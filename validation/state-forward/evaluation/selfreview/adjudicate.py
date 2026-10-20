from pathlib import Path
import json,hashlib,datetime,collections,importlib.util,sys,copy
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/state-forward');I=R/'evaluation-inputs/selfreview';O=R/'evaluation/selfreview';D=R/'design/private'
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mod(name,p):s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
compare=mod('frozen_compare_original_reviews',D/'compare.py');oracle=json.loads((D/'oracle.json').read_text())['cells'];batch=json.loads((I/'batch.json').read_text());public={x['caseID']:x for x in json.loads((R/'design/public/cases.json').read_text())['cases']};allsummary={};audit=[]
def canon(x):
 if isinstance(x,str):
  try:return json.loads(x)
  except (ValueError,TypeError):return x
 return x
for arm in batch['corpora']:
 aid=arm['anonymousID'];p=Path(arm['originalReviewDirectory']);own=Path(arm['ownD0NativeCaptures']);g0=json.loads(Path(arm['independentD0Grade']).read_text());gf=json.loads(Path(arm['independentFinalGrade']).read_text());before={x['cellID']:x for x in g0['rows']};review=json.loads((p/'review.json').read_text());manual=review.get('manual_findings',review.get('manual_and_native_findings',[]));claims=[];ledger=[];original_rows=[];reportlog=[];validation=[];plans={};obs={};reportcounts={};claimaliases=[]
 for plat in ['android','ios']:
  for cid in ['P1','P2','P3','P4']:
   plpath=p/'review-plan'/cid/f'plan.{plat}.json';pl=json.loads(plpath.read_text());plans[plat,cid]={x['id']:x for x in pl['assertions']};obpath=own/plat/cid/'observation.json';ob=json.loads(obpath.read_text());obs[plat,cid]=ob
   fixture=json.loads((own/plat/cid/'fixtures.json').read_text());fixed=public[cid];assert [fixture['initial']['model']]+[u['model'] for u in fixture['updates']]==fixed['models'];assert fixture['initial']['host']==fixed['host'];assert all(u['host']==fixed['host'] for u in fixture['updates'])
   validation.append(dict(platform=plat,caseID=cid,observation=str(obpath),observationSHA256=sha(obpath),plan=str(plpath),planSHA256=sha(plpath),actualFixture=str(own/plat/cid/'fixtures.json'),modelsAndHostMatchFixedPublic=True))
 def match(cell,adj,reason):
  return dict(cellID=cell['cellID'],adjudication=adj,reason=reason,fixedD0Status=before[cell['cellID']]['status'],fixedExpected=cell['expected'])
 def candidates(plat,sid,target=None):return [x for x in oracle if x['platform']==plat and x['stateID']==sid and (target is None or x.get('targetID')==target)]
 def rowmatches(plat,cid,row,spec):
  sid=row['state'];target=spec.get('target',{}).get('identifier');prop=spec.get('property');kind=spec['kind'];cs=candidates(plat,sid,target);proof={};cl='runtime.unknown'
  if kind=='event':
   cell=next(x for x in candidates(plat,sid) if x['aspect']=='behavior.callbackInterval');actual=row.get('actual',{});idx=spec['action_index'];step=obs[plat,cid]['steps'][idx];expected=spec['expected'];interval=actual.get('interval_facts');equal=interval is not None and [canon(x) for x in interval]==[canon(x) for x in expected]
   assert step['dispatch']['succeeded'] is True and actual['stimulus_established'] is True
   assert [canon(x) for x in cell['expected']]==[canon(x) for x in expected]
   proof=dict(actualStepIndex=idx,rawStep=step,canonicalImmediateInterval=[canon(x) for x in interval] if interval is not None else None,canonicalExpected=expected,canonicalEqual=equal,normalization='JSON envelope decode ignores object key order only. Original report/raw receipts retained byte-exact.')
   return [match(cell,'false' if equal and before[cell['cellID']]['status']=='P' else 'uncertain','Original checker failed string-versus-object transport. Exact immediate actual callback envelope equals the fixed public event after JSON decoding; immutable independent D0 callback is P. No product callback defect established.' if equal else 'Actual interval does not establish a decisive match to a natural fixed D0 failure.')],proof,'runtime.business.stimulus'
  if prop=='font_sp':
   cell=next(x for x in cs if x['aspect'].endswith('.fontSize'));status=before[cell['cellID']]['status'];values=row.get('actual',[]);assert status=='P';assert all(isinstance(v,(float,int)) and abs(v-cell['expected'])<=.75 for v in values)
   return [match(cell,'false','Original failed strict floating comparison differs only below frozen0.75sp font epsilon. Actual exported sizes meet this fixed native font obligation; D0 is P.')],dict(originalValues=values,fixedEpsilon=.75,originalExpected=spec['expected']),cell['classification']
  if prop in ['ax_height','touch_height','ax_width','touch_width']:
   dim='height' if prop.endswith('height') else 'width';cell=next(x for x in cs if x['aspect'].endswith('.semanticBounds.'+dim));status=before[cell['cellID']]['status']
   if status=='F' and plat=='ios' and target=='printbatch.priority':return [match(cell,'exact','Same actual state, exact priority control and actual AX height28 below fixed minimum48 even with2pt uncertainty. Source/API/hit-testing inference is unnecessary.')],dict(originalProperty=prop,measurementMeaning='actual unique native control AX rectangle',physicalHitClaim=False),cell['classification']
   return [match(cell,'uncertain','Original strict geometry or viewport touch-bound failure does not establish frozen semantic-layout minimum failure. Fixed D0 is U under2-unit edge uncertainty; Android native touch-action rectangle and semantic layout rectangle are distinct. No physical-hit conclusion.')],dict(originalProperty=prop,independentMeasurement=before[cell['cellID']].get('measurement'),independentStatus=status),cell['classification']
  if prop=='overflow':
   cell=next(x for x in candidates(plat,sid) if x['aspect']=='visual.noClip')
   return [match(cell,'uncertain','Actual exported native overflow flag is retained. There is no fixed native-overflow cell; the separate screenshot noClip obligation was visibly satisfied in independent D0. A native layout flag is not interchangeable with visible clipped/truncated required content, so neither an exact match nor a confirmed false product claim is manufactured.')],dict(originalOverflow=row.get('actual'),targetID=target,nativeFlagNotScreenshotVerdict=True),'runtime.style.native'
  return [],dict(reason='No unambiguous fixed original D0 state/aspect correspondence.'),cl
 for series in ['review-original','review-semantic-diagnostics']:
  if not (p/series).exists():continue
  counts=collections.Counter()
  for plat in ['android','ios']:
   for cid in ['P1','P2','P3','P4']:
    rp=p/series/f'{plat}-{cid}.json'
    if not rp.exists():continue
    report=json.loads(rp.read_text());obpath=own/plat/cid/'observation.json';plpath=p/'review-plan'/cid/f'plan.{plat}.json';assert report['input_hashes']['observation']==sha(obpath);assert report['input_hashes']['plan']==sha(plpath)
    counts.update(report['counts']);nfail=0
    for j,row in enumerate(report['assertions']):
     spec=plans[plat,cid][row['id']];ref=str(rp)+f'#/assertions/{j}';entry=dict(occurrenceID=f'{series}:{plat}:{cid}:{j}',origin='typed',reportSeries=series,platform=plat,caseID=cid,stateID=row.get('state'),originalID=row['id'],originalStatus=row['status'],actualTypedCheck=True,rawRefs=[ref,str(plpath),str(obpath)],originalPlan=spec,originalRowRef=ref,positiveFaultClaim=row['status']=='failed')
     ledger.append(entry)
     if row['status']!='failed':continue
     nfail+=1;m,proof,cls=rowmatches(plat,cid,row,spec);claimid='typed:'+series+':'+plat+':'+row['id'];entry['normalizedClaimID']=claimid
     claims.append(dict(claimID=claimid,origin='typed',scope='runtime',reportSeries=series,classification=cls,platform=plat,caseID=cid,stateID=row['state'],target=spec.get('target'),aspect=spec.get('property',spec['kind']),original=dict(assertion=row,plan=spec),rawRefs=[ref,str(plpath),str(obpath)],typedCheckEstablished=True,typedNativeReportRefs=[ref],matches=m,adjudicationEvidence=proof))
    assert nfail==report['counts']['failed'];reportlog.append(dict(path=str(rp),sha256=sha(rp),series=series,platform=plat,caseID=cid,counts=report['counts'],nativeObservationHashVerified=True,planHashVerified=True,machineFindingsFieldRequired=False))
  reportcounts[series]=dict(counts)
 # Every original manual assertion remains in the ledger; only explicit failed findings enter positive-claim statistics.
 for j,item in enumerate(manual):
  ref=str(p/'review.json')+('#/manual_findings/' if 'manual_findings' in review else '#/manual_and_native_findings/')+str(j);positive=item.get('status','').startswith('failed');entry=dict(occurrenceID='manual:'+str(j),origin='manual',original=item,rawRefs=[ref]+[e['path'] for e in item.get('evidence',[]) if isinstance(e,dict) and e.get('path')],positiveFaultClaim=positive);ledger.append(entry)
  if not positive:continue
  plat=item['platform'];sid=item['stateID'];cs=candidates(plat,sid);aspect=item['aspect'];matches=[];cls='runtime.style.visual';scope='runtime';explain=''
  if aspect=='visible status badge and header layout':
   matches=[match(next(x for x in cs if x['aspect']==a),'exact','Same-state original manual screenshot explicitly reports absent/unreadable clipped status words. Matches independent frozen D0 visual noClip/readability failure; source cause is not used for detection.') for a in ['visual.noClip','visual.readability']]
  elif aspect=='native semantic minimum bounds':
   cell=next(x for x in cs if x.get('targetID')=='printbatch.priority' and x['aspect'].endswith('.semanticBounds.height'));matches=[match(cell,'exact','Original manual/native finding explicitly identifies this state priority AX height28 below48. Exact frozen D0 native-geometry failure, independent of implementation or later repair.')];cls='runtime.layout.native'
  elif aspect in ['RTL text reading order','RTL English and numeric readability']:
   cell=next(x for x in cs if x['aspect']=='visual.readability');matches=[match(cell,'uncertain','Original claim requires exact rendered English/number token order such as28 cr. Frozen visual row says words/numeric values remain readable, with mirrored row positions checked separately; independent D0 passed this narrow readability wording. Original screenshot shows cr28 but intact legible tokens. Preserve an uncertain/partial semantic correspondence, do not retrofit a broader F or manufacture a confirmed false alarm.')]
  elif aspect=='outer host canvas palette':
   scope='integration.host';cls='integration.host';explain='Original explicitly scopes pixels to common host outside production component and leaves responsibility unmapped. Frozen acceptance judges component root; retain as unmapped integration issue, not product palette F/false.'
  else:explain='Original manual finding lacks a narrow decisive correspondence to fixed D0 failure.'
  claimid='manual:'+item['claimID'];entry['normalizedClaimID']=claimid;claims.append(dict(claimID=claimid,originalClaimID=item['claimID'],origin='manual',scope=scope,reportSeries='manual',classification=cls,platform=plat,caseID=item['caseID'],stateID=sid,aspect=aspect,original=item,rawRefs=entry['rawRefs'],matches=matches,unmappedReason=explain or None))
 # Limitations, status-only summaries, aggregate aliases and source hypotheses are preserved without promoting them to positive detector claims.
 for key in ['uncertain_unmapped_issues','uncertain_or_unmapped_issues','review_limits','source_witnesses','summary','typed_failures','machine_failures','transport_diagnostic_counts','original_plan_integrity']:
  if key in review:ledger.append(dict(occurrenceID='review-section:'+key,origin='review_section',rawRefs=[str(p/'review.json')+'#/'+key],original=review[key],positiveFaultClaim=False,note='Preserved original section. Aggregated typed aliases do not create extra independent detector claims; limitations/U/source hypotheses are not promoted to findings.'))
 for path in sorted((p/'review-original').glob('all-*.json')):
  claimaliases.append(dict(path=str(path),sha256=sha(path),role='Verbatim aggregate of canonical assertion rows; retained original reference, not counted twice.'))
 transport=p/'review-original/transport-diagnostics.json'
 if transport.exists():claimaliases.append(dict(path=str(transport),sha256=sha(transport),role='Diagnostic decoding of original callback intervals; retained without rewriting original failed statuses.'))
 # Duplicate content across actual diagnostic rechecks is retained and identified even for uncertain/false claims.
 signature={};duplicates=[]
 for c in claims:
  if c['origin']!='typed':continue
  original=c['original'];sig=json.dumps(dict(platform=c['platform'],caseID=c['caseID'],stateID=c['stateID'],target=c.get('target'),aspect=c['aspect'],expected=original['plan'].get('expected'),actual=original['assertion'].get('actual')),sort_keys=True,ensure_ascii=False)
  if sig in signature:duplicates.append(dict(claimID=c['claimID'],duplicateOf=signature[sig],reason='Same native state/target/property/expectation/actual values in a separate actual diagnostic report. Retained, not an extra unique detected row.'))
  else:signature[sig]=c['claimID']
 actualReview=dict(schemaVersion=1,anonymousID=aid,claims=claims,positiveClaimScope='All original failed actual typed assertions plus original explicit failed manual findings. Supplemental actual diagnostic reruns remain distinct and duplicate-aware; no machine_findings eligibility requirement.',nonpositiveLedger=str(O/aid/'original-claim-ledger.json'),originalReports=reportlog)
 save(O/aid/'claims.json',actualReview);save(O/aid/'original-claim-ledger.json',dict(schemaVersion=1,anonymousID=aid,originalReview=str(p/'review.json'),originalReviewSHA256=sha(p/'review.json'),occurrences=ledger,aggregateAliases=claimaliases,duplicateNativeClaims=duplicates,note='Every manual assertion and every actual typed assertion, including P/U, is referenced here; positive fault claims alone enter conditional false-discovery and detection comparisons.'))
 result=compare.compare(g0,gf,actualReview);save(O/aid/'comparison.json',result)
 originalclaims=[x for x in claims if x['reportSeries']!='review-semantic-diagnostics'];originalresult=compare.compare(g0,gf,dict(claims=originalclaims));save(O/aid/'comparison-original-reports-only.json',originalresult)
 # Atomic row detection/miss and repairs are based only on original independent D0 F; FINAL never creates a detector match.
 detected=set(result['reviewMatching']['combinedDetectedRows']);manualset=set(result['reviewMatching']['manualDetectedRows']);typedset=set(result['reviewMatching']['actualTypedDetectedRows']);rowledger=[]
 for row in g0['rows']:
  if row['status']!='F' or not row['classification'].startswith('runtime.'):continue
  exactclaims=[c['claimID'] for c in claims if any(m['cellID']==row['cellID'] and m['adjudication']=='exact' for m in c['matches'])];partial=[c['claimID'] for c in claims if any(m['cellID']==row['cellID'] and m['adjudication'] in ['partial','uncertain'] for m in c['matches'])];planchecks=[]
  for k,specs in plans.items():
   if k!=(row['platform'],row['caseID']):continue
   for spec in specs.values():
    if spec.get('state')!=row['stateID'] or spec.get('target',{}).get('identifier')!=row['targetID']:continue
    prop=spec.get('property');wanted='font_sp' if row['aspect'].endswith('.fontSize') else 'font_weight' if row['aspect'].endswith('.fontWeight') else None
    if wanted and prop==wanted:planchecks.append(spec)
  reason='Exact original finding matched.' if row['cellID'] in detected else 'No original positive failed typed/manual finding matched this exact state and aspect; limitations/source causes/later repairs do not create detection.'
  if row['aspect']=='summary.fontSize' and not exactclaims:reason='Original Android plan expected14 (or16.8) rather than frozen12 (or14.4), so its passing summary-size checks miss this native font failure.'
  if row['aspect']=='balance.fontWeight' and not exactclaims:reason='Original Android plan expected400 (regular) rather than frozen600 (semibold), so its passing balance-weight checks miss this native font failure.'
  if row['classification']=='runtime.coverage' and not exactclaims:reason='Original limitations/partial coverage observations are retained but no positive exact failed requirement check matches this native-all-targets F. Shared clipped-status source cause cannot backfill coverage detection.'
  end=next(x for x in gf['rows'] if x['cellID']==row['cellID']);rowledger.append(dict(cellID=row['cellID'],platform=row['platform'],caseID=row['caseID'],stateID=row['stateID'],classification=row['classification'],aspect=row['aspect'],D0='F',FINAL=end['status'],manualDetected=row['cellID'] in manualset,typedDetected=row['cellID'] in typedset,combinedDetected=row['cellID'] in detected,exactClaimIDs=exactclaims,partialOrUncertainClaimIDs=partial,relatedOriginalPlans=planchecks,reason=reason,repairCaveat='F->U is unresolved under frozen measurement/capability policy, not a verified repair.' if end['status']=='U' else 'Literal fixed-row result only; no source-inferred runtime proof.'))
 save(O/aid/'fixed-failure-detection-ledger.json',dict(rows=rowledger))
 classes=['runtime.business.current','runtime.business.stimulus','runtime.style.native','runtime.style.visual','runtime.layout.native','runtime.coverage','runtime.capability.physicalHit']
 panels={}
 for cls in classes:
  rr=[x for x in rowledger if x['classification']==cls];n=len(rr);panels[cls]=dict(naturalFRows=n,manualDetected=sum(x['manualDetected'] for x in rr),typedDetected=sum(x['typedDetected'] for x in rr),combinedDetected=sum(x['combinedDetected'] for x in rr),missed=sum(not x['combinedDetected'] for x in rr),manualDetectionShare=sum(x['manualDetected'] for x in rr)/n if n else None,combinedDetectionShare=sum(x['combinedDetected'] for x in rr)/n if n else None,fixedRowTransitions=dict(collections.Counter(x['FINAL'] for x in rr)),repairShare=sum(x['FINAL']=='P' for x in rr)/n if n else None,reasonIfNA='Zero natural D0 failures; detection/repair denominator N/A.' if not n else None)
 save(O/aid/'detection-panels.json',dict(byClass=panels,sourceInput='Source and input checks are separate from natural runtime failure detection; neither has a natural F in sealed D0.'))
 inv=json.loads((O/aid/'manual-image-inventory.json').read_text());save(O/aid/'manual-image-review-log.json',dict(reviewedAtUTC=now(),imageCount=len(inv['images']),sheets=[dict(path=str((R.parent.parent/Path(x)).resolve()) if False else str((Path.cwd()/x).resolve()),sha256=sha(Path(x)),review='Explicitly displayed full original-resolution ordered sheet; claim-scoped screenshot evidence only.') for x in inv['sheets']],reviewedImages=inv['images'],scope='All71 distinct positive-manual-finding image refs across both anonymous sources reviewed. Pixel/AX geometry grades are not derived from montage size.'))
 save(O/aid/'matching-audit.json',dict(reportCounts=reportcounts,actualReportProvenance=reportlog,ownNativeInputValidation=validation,manualStatusCounts=dict(collections.Counter(x.get('status') for x in manual)),actualFailedRowsEqualEligibility=True,machineFindingsFieldNotUsed=True,diagnosticDuplicates=duplicates,adjudicationRuleNotes=['Native flags are not screenshot review; source hypotheses and later repairs are not original detections.','Original decoded callback intervals match promised JSON envelopes; raw report failure preserved and classified false under frozen object-order-insensitive policy.','Floating native font discrepancies within0.75sp epsilon are false claims; minimum geometry within2-unit uncertainty remains uncertain.','All RTL visual token-order claims remain uncertain under narrow frozen readability wording; no changed quality rows.','Outside-card common-host palette issues remain integration.host unmapped.','Every P/U original typed assertion and passed scoped visual assertion is preserved in ledger without automatic positive fault eligibility.'],fixedGradesUnchanged=True))
 rm=result['reviewMatching'];om=originalresult['reviewMatching'];allsummary[aid]=dict(naturalD0FRows=result['naturalFRows'],manualDetected=len(rm['manualDetectedRows']),actualTypedDetected=len(rm['actualTypedDetectedRows']),combinedDetected=len(rm['combinedDetectedRows']),manualExclusive=len(rm['manualExclusiveRows']),typedExclusive=len(rm['typedExclusiveRows']),both=len(rm['bothRows']),manualDetectionShare=rm['manualDetectionShare'],combinedDetectionShare=rm['combinedDetectionShare'],allActualPositiveClaimCounts=rm['claimCounts'],allActualConditionalFDR=rm['conditionalFalseDiscoveryShare'],allActualUncertainBounds=rm['allUncertainConservativeInterval'],originalOnlyPositiveClaimCounts=om['claimCounts'],originalOnlyConditionalFDR=om['conditionalFalseDiscoveryShare'],originalOnlyUncertainBounds=om['allUncertainConservativeInterval'],classicalFPR=None,fixedRowTransitions=result['fixedRowTransitions'],repairShare=result['repairShare'],byClass=panels,typedReportCounts=reportcounts,mainQualityGradesModified=False)
print(json.dumps(allsummary,indent=2))
save(O/'SUMMARY.json',dict(stage='selfreview',corpora=allsummary,blindingLimit='Original producer paths and report schemas may make versions recognizable at this stage. No private assignment was opened or inferred for grading. D0/FINAL scores already sealed and unchanged.',noPairedDataRead=True,notes=['Matching uses exact original D0 failed requirement states/aspects. Every actual failed row is eligible without machine_findings.','ConditionalFDR among adjudicable positive claims is accompanied by all uncertain/unmapped bounds, original-only/all-actual panels, and preserved duplicates. No complete TN universe: classicalFPR N/A.','Source/API/source risks and host integration claims remain separate; no source-as-runtime or repair-state backfill.','Zero-natural-F per-class denominators N/A, never100%.']))
