"""Independent exact D0/self-review matching. Candidate decisions are explicit below.
No FINAL quality results, assignment, capabilities, repair reports or paired corpus read.
"""
import collections,datetime,hashlib,json,pathlib,sys
ROOT=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
EVAL=ROOT/'validation/tool-forward/design/size-revision/private/evaluator'
HERE=pathlib.Path(__file__).parent
METHODS=ROOT/'validation/tool-forward/METHODS.md'
METHOD_SHA='095e8ac34fb6f9e2d3a77536a348426212639e7c6a6630ee218801343ceb3f15'
D0_SHA='f0971f33f53d90473db71590abf471c2e36af1ccfbb3a6645b2e373684f733b7'
FINAL_SHA='ddd7f906266498924813be74946375e23bccdad75d50c742ce1c34cdb418f284'
REVIEWS={'submission-b2e249':'bdb7ce231218967be63e7a05f2add41be81871f360a484bb4ace12211bcc73db','submission-4f4364':'a32636cec275824637dee90287cd9ba216901a1766d6021536e136e60a308070'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def item(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def write_new(p,v):
 if p.exists():raise RuntimeError('Refusing to overwrite sealed comparison '+str(p))
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def scoped(f,r):return r['platform']=={'ios':'apple'}.get(f.get('platform'),f.get('platform')) and r['contextId'] in {x.replace('--','/',1) for x in f.get('stateIds',[])}
def scoped(f,r):
 platforms=['android','apple'] if f.get('platform')=='both' else [{'ios':'apple'}.get(f.get('platform'),f.get('platform'))]
 return r['platform'] in platforms and r['contextId'] in {x.replace('--','/',1) for x in f.get('stateIds',[])}
def manual_decisions(sub,review,rows):
 assert sub=='submission-4f4364';out={}
 for f in review['findings']:
  fid=f['id'];matched=[];u=[];related=[];override=None
  if fid=='RR-SR-IOS-001':
   matched=[(r,'TP','The finding explicitly confirms required identifier propagation/loss in this exact named model state. Named missing descendant IDs supply a counterexample to this atomic documented-namespace set assertion. This does not claim every ID member separately, or any incorrect business callback.') for r in rows if scoped(f,r) and r['criterion']=='documentedIdentifierSetEquals']
   u.append({'claim':'Required control targets cannot be found by the collector. This does not prove that a physically tapped name-selected button emits the wrong action.','certainty':'confirmed discovery observation; explicit handler limitation','atomicKeysClaimed':[],'rationale':'Do not convert identifier/discovery evidence into callbacks.count or callbacks.payload detections, or silently add unlisted pending-action checkpoints. Native nonzero exits alone are not product assertions.'})
  elif fid=='RR-SR-IOS-002':
   matched=[(r,'TP','The finding explicitly confirms disabled primary fill/text pixel mismatches for this named initial state, the same exact representative-color conditions independently FAIL in D0. No different-target text or color member is inferred.') for r in rows if scoped(f,r) and r['criterion']=='sampledFlatColorMatches' and r['target']=='rr.primary']
   u.append({'claim':'Disabled reason colors in C02/C04 and primary colors in C02 caller-size-selected.','certainty':'confirmed','atomicKeysClaimed':[],'classification':'UNCERTAIN','rationale':'No same-target/state disabled-color atomic probes exist for these additional subclaims. Other header/normal text color, string readability and native-enabled members are different conditions and cannot become TP or FP.'})
  elif fid=='RR-SR-ANDROID-003':
   u.append({'claim':f['claim'],'certainty':'confirmed','atomicKeysClaimed':[],'classification':'UNCERTAIN','scopeOutsideFrozenAtomicMatrix':True,'rationale':'This is specifically summary totalValue base typography. The frozen runtime font probes target rr.header.title in C01/C03/C04, not totalValue; source/API assertions do not test total typography. A related typography key cannot receive detection credit or be called a contradictory PASS.'})
  elif fid=='RR-SR-IOS-004':
   u.append({'claim':f['claim'],'certainty':'confirmed source declaration only','atomicKeysClaimed':[],'classification':'UNCERTAIN','scopeOutsideFrozenAtomicMatrix':True,'rationale':'The review explicitly limits the claim to source-declared totalValue style and disclaims actual resolved runtime font size. There is no source-font-token atomic item, and a source concern cannot establish the runtime header font predicates.'})
  elif fid=='RR-SR-IOS-005':
   matched=[(r,'UNCERTAIN','The same named state and decorative-suppression property are suspected, with explicit lack of independent VoiceOver element/traversal proof. Native image presence/hittability cannot turn the D0 unassessed independent-accessibility condition into a confirmed failure.') for r in rows if scoped(f,r) and r['criterion']=='independentAccessibleDecorativeIconCount']
  elif fid in ['RR-SR-ANDROID-006','RR-SR-IOS-007','RR-SR-BOTH-008']:
   override='NO_CONFIRMED_CLAIM';u.append({'claim':f['claim'],'certainty':f['certainty'],'kind':'positive_observation','atomicKeysClaimed':[],'rationale':'A positive/equal observation is retained verbatim and does not allege a product failure. It is not forced into TP, FP or a zero-valued reviewed-negative denominator.'})
  elif fid=='RR-SR-BOTH-009':
   for r in rows:
    if not scoped(f,r):continue
    if r['platform']=='apple' and r['criterion']=='documentedIdentifierSetEquals':matched.append((r,'TP','The qualified positive observation also explicitly repeats that iOS region identifiers are overridden in these exact status states. That same-condition confirmed defect matches the D0 identifier-set FAIL; duplicate overlap with the identifier finding is retained and deduplicated only for arithmetic.'))
    if r['platform']=='android' and (r['criterion']=='heading' or (r['criterion']=='accessibilityValueEquals' and r['target']=='rr.progress')):matched.append((r,'UNCERTAIN','The review explicitly states Android stateDescription/heading traits are not exported for this named status condition; this is an evidence limit, not a confirmed failure.'))
   u.append({'claim':'The examined submitting/complete states show requested progress/result and total content, and iOS progress value In progress.','certainty':'confirmed positive observation','kind':'positive_observation','atomicKeysClaimed':[],'rationale':'Preserve the equal/positive scope separately; no whole P04/P06 status contract pass is inferred from these partial observations.'})
  elif fid=='RR-SR-COLLECTOR-010':
   override='NO_CONFIRMED_CLAIM';u.append({'claim':f['claim'],'certainty':'confirmed evidence-limit observation','kind':'evidence_limit','atomicKeysClaimed':[],'rationale':'The review explicitly identifies a measurement/collector concern and excludes a component layout failure. Collector source references are not opened. It is not a product FP or a component-margin/hit-bounds detection.'})
  elif fid=='RR-SR-BOTH-011':
   for r in rows:
    if not scoped(f,r):continue
    if r['criterion']=='resolvedFontFamilyIsNativeSystem' or (r['platform']=='apple' and r['criterion'] in ['unscaledPointOrSpRange','heading','independentAccessibleDecorativeIconCount']):matched.append((r,'UNCERTAIN','Explicit unresolved native font/Apple hidden-heading trait claim for this named state/property. No source font, AX boundary or sampled sheet substitutes for the requested native method; no confirmed failure is claimed.'))
   u.extend([{'claim':'Physical touch dispatch/iOS physical touch rectangles remain unassessed.','certainty':'unassessed','atomicKeysClaimed':[],'rationale':'No individual touch-target members or exact action checkpoint states are claimed. Preserve the method-level limitation without a blanket parameterized-member expansion.'},{'claim':'Complete clipping/color acceptance and full updated long-content overlapping coverage are withheld.','certainty':'unassessed','atomicKeysClaimed':[],'rationale':'No particular missing/clipped field, color role or failing product reachability item is asserted. A sampled-review/collector limitation is not a product failure and does not automatically claim all visual group members.'},{'claim':'Minimum-deployment runtime/package compatibility was not rerun.','certainty':'unassessed','atomicKeysClaimed':[],'rationale':'Runtime rerun absence is distinct from the frozen source-only availability audit. No source API or availability failure is inferred.'}])
  elif fid=='RR-SR-IOS-012':
   matched=[(r,'UNCERTAIN','The finding specifically names Medium/Large in C06 initial, but explicitly suspects stronger word-flow readability and concedes all-character visibility may be satisfied. The D0 complete-glyph text condition is PASS; uncertainty is not a confirmed clipping FP or TP.') for r in rows if scoped(f,r) and r['criterion']=='fullyReadableTextEquals' and r['target'] in ['size.medium.label','size.large.label']]
   u.append({'claim':'Prefer fewer columns for enlarged ordinary words; no missing glyph or overlap established.','certainty':'suspected/recommendation','atomicKeysClaimed':[],'rationale':'No normative minimum column width or word-fragmentation predicate exists. Do not match unrelated layout/hit-target or overlap assertions.'})
  else:raise ValueError('Unreviewed original finding '+fid)
  out[fid]={'matches':matched,'unverifiable':u,'related':related,'findingClassificationOverride':override}
 return out

def build(sub):
 assert sha(METHODS)==METHOD_SHA and sha(EVAL/'d0-grades-seal.json')==D0_SHA and sha(EVAL/'final-grades-seal.json')==FINAL_SHA
 dest=HERE/sub
 if (dest/'comparison-seal.json').exists():raise RuntimeError('Comparison already sealed')
 if sub=='submission-4f4364' and not (HERE/'submission-b2e249/comparison-seal.json').is_file():raise RuntimeError('First own-review comparison must be sealed before second review read')
 reviewpath=ROOT/'validation/tool-forward/phase-reports'/sub/'readonly-review/reports/self-review.json';assert sha(reviewpath)==REVIEWS[sub];review=load(reviewpath)
 commit=next(x for x in load(EVAL/'d0-grades-seal.json')['gradeCommitments'] if x['candidateId']==sub);gradepath=ROOT/commit['grade']['path'];assert sha(gradepath)==commit['grade']['sha256'];grade=load(gradepath);rows=grade['results'];rowids={(r['platform'],r['key']):i for i,r in enumerate(rows)};assert len(rows)==len(rowids)==2209
 original_findings=review['findings'];decisions=manual_decisions(sub,review,rows);assert set(decisions)=={f['id'] for f in original_findings}
 evpath=gradepath.parent/'evidence-inventory.json';srcpath=gradepath.parent/'source-inventory.json';evi=load(evpath);src=load(srcpath)
 bysha=collections.defaultdict(list)
 for record in evi['files']+src['files']:
  q=dict(record);q['path']=str(ROOT/q['path']) if not pathlib.Path(q['path']).is_absolute() else q['path'];bysha[q['sha256']].append(q)
 def evidence_audit(f):
  out=[]
  for e in f.get('evidence',[]):
   h=e.get('sha256') or review.get('sourceFingerprintsBefore',{}).get(e['path']);found=bysha.get(h,[]) if h else []
   out.append({'originalEvidence':e,'resolvedBy':'exact SHA256 from sealed D0 evidence/source inventory' if found else None,'independentlyResolvedSources':found,'status':'BOUND_TO_SEALED_D0' if found else 'REVIEW_REFERENCE_WITHOUT_VERIFIED_RAW_HASH_OR_DERIVATIVE_NOT_OPENED','limitation':None if found else 'Original cache aliases/snapshot indices and any absent hashes remain literal and are not rebound to a different capture by basename. Original alias bytes, scratch artifacts and collector source were not opened. Same-condition matching uses the independently sealed D0 exact sources, named case/state/property and matching anonymous production source fingerprints.'})
  return out
 findings=[];matches=[];unverifiable=[];suspected=[];related=[]
 for fi,f in enumerate(original_findings):
  d=decisions[f['id']];audit=evidence_audit(f);local=[]
  for r,cl,why in d['matches']:
   if cl=='TP':assert f['certainty']=='confirmed' and f.get('productViolationClaimed',True) and r['outcome']=='FAIL'
   if cl=='FP':assert f['certainty']=='confirmed' and f.get('productViolationClaimed',True) and r['outcome']=='PASS' and r['exactSources']
   assert scoped(f,r), (f['id'],r['key'])
   i=rowids[(r['platform'],r['key'])]
   a={'findingId':f['id'],'platform':r['platform'],'key':r['key'],'assessmentId':r['assessmentId'],'contextId':r['contextId'],'aspect':r['aspect'],'target':r['target'],'criterion':r['criterion'],'classification':cl,'d0Outcome':r['outcome'],'claimRationale':why,'reviewExactSource':{**item(reviewpath),'locator':{'kind':'jsonPointer','pointer':'/findings/'+str(fi)}},'d0GradeExactSource':{**item(gradepath),'locator':{'kind':'jsonPointer','pointer':'/results/'+str(i)}},'requiredBinding':r['requiredBinding'],'exactEvidencePaths':r['exactSources'] or r['consideredSources'],'d0MissingEvidenceMethod':r['missingEvidenceMethod'],'d0MissingEvidenceDetail':r['missingEvidenceDetail'],'reviewEvidenceAudit':audit}
   matches.append(a);local.append(a)
  resolved={a['classification'] for a in local if a['classification'] in ['TP','FP']}
  label='MIXED' if resolved=={'TP','FP'} else 'TP_ONLY' if resolved=={'TP'} else 'FP_ONLY' if resolved=={'FP'} else 'NO_CONFIRMED_CLAIM' if f.get('productViolationClaimed') is False else 'UNCERTAIN' if local or d['unverifiable'] or f['certainty']!='confirmed' else 'NO_CONFIRMED_CLAIM'
  label=d.get('findingClassificationOverride') or label
  findings.append({'id':f['id'],'certainty':f['certainty'],'classification':label,'originalFinding':f,'originalScope':{k:f.get(k) for k in ['platform','caseIds','stateIds','aspect','productViolationClaimed']},'normalizationRationale':'ios is normalized to exact grade platform apple; case--state becomes case/state only. Resolved finding classifications describe adjudicable atomic claims only; unresolved/non-product subclaims remain separate and prevent any claim that the whole original finding was validated. No source cause creates runtime matches.','completeClaimAdjudicated':not d['unverifiable'],'atomicMatchRefs':[{'platform':x['platform'],'key':x['key'],'classification':x['classification']} for x in local],'exactSupportingSources':audit,'unverifiableSubclaims':d['unverifiable']})
  for u in d['unverifiable']:unverifiable.append({'findingId':f['id'],**u,'originalReviewSource':{**item(reviewpath),'locator':{'kind':'jsonPointer','pointer':'/findings/'+str(fi)}}})
  if f['certainty']!='confirmed' or any(u.get('certainty')=='suspected' for u in d['unverifiable']):suspected.append({'findingId':f['id'],'originalCertainty':f['certainty'],'originalFinding':f,'exactAtomicRefs':[{'platform':x['platform'],'key':x['key'],'classification':x['classification']} for x in local],'unverifiableSubclaims':d['unverifiable']})
  related += [{'findingId':f['id'],'platform':r['platform'],'key':r['key'],'d0Outcome':r['outcome'],'classification':None,'rationale':'Related but not the same product-failure condition; deliberately not an atomic detection or false positive.','exactEvidencePaths':r['exactSources'] or r['consideredSources']} for r in d['related']]
 tp={(m['platform'],m['key']) for m in matches if m['classification']=='TP'};fp={(m['platform'],m['key']) for m in matches if m['classification']=='FP'};fail={(r['platform'],r['key']) for r in rows if r['outcome']=='FAIL'}
 fn=[{'platform':r['platform'],'key':r['key'],'assessmentId':r['assessmentId'],'contextId':r['contextId'],'aspect':r['aspect'],'target':r['target'],'criterion':r['criterion'],'exactEvidencePaths':r['exactSources'],'reason':'No supported confirmed same-condition review claim matched this exact D0 failure as TP.'} for r in rows if (r['platform'],r['key']) in fail-tp]
 groups=collections.defaultdict(list)
 for m in matches:groups[(m['platform'],m['key'])].append(m)
 duplicates=[{'platform':pl,'key':key,'occurrences':[{'findingId':m['findingId'],'classification':m['classification']} for m in mm],'countingPolicy':'Preserve every claim occurrence; unique exact platform/key is counted once in atomic arithmetic.'} for (pl,key),mm in groups.items() if len(mm)>1]
 clusterpath=gradepath.parent/'coverage-and-method-audit.json';cl=load(clusterpath)['defectClusters'];clusters=[]
 for name,c in cl.items():
  members=[]
  for mid in c['memberAssessmentIds']:
   r=next(x for x in rows if x['assessmentId']==mid);ident=(r['platform'],r['key']);members.append({'platform':r['platform'],'key':r['key'],'assessmentId':mid,'discovered':ident in tp,'findingIds':[m['findingId'] for m in matches if (m['platform'],m['key'])==ident and m['classification']=='TP']})
  clusters.append({'clusterId':name,'source':item(clusterpath),'members':members,'discoveredMemberKeys':[{'platform':m['platform'],'key':m['key']} for m in members if m['discovered']],'notDiscoveredMemberKeys':[{'platform':m['platform'],'key':m['key']} for m in members if not m['discovered']],'coverage':'ALL_MEMBERS_DISCOVERED' if all(m['discovered'] for m in members) else 'PARTIAL' if any(m['discovered'] for m in members) else 'NOT_DISCOVERED','independentClusterSampleSize':None,'rationale':'Use the pre-self-review sealed descriptive D0 clusters; correlated members/clusters are not independent experimental samples.'})
 dest.mkdir(parents=True,exist_ok=True);original=dest/'review-original.json'
 if original.exists():raise RuntimeError('Original review copy already exists')
 original.write_bytes(reviewpath.read_bytes());assert sha(original)==REVIEWS[sub]
 result={'schemaVersion':1,'candidateId':sub,'phase':'D0_SELF_REVIEW_MATCHING','generatedAtUTC':now(),'definitions':item(METHODS),'d0JointSeal':item(EVAL/'d0-grades-seal.json'),'finalJointSeal':item(EVAL/'final-grades-seal.json'),'ownD0Grade':item(gradepath),'originalReview':item(reviewpath),'preservedOriginalReview':item(original),'originalFindingCount':len(original_findings),'findings':findings,'atomicMatches':matches,'confirmedD0FailureKeysNotDetectedAsTP':fn,'suspectedOrUnassessedClaims':suspected,'unverifiableClaims':unverifiable,'duplicates':duplicates,'relatedButNotMatched':related,'defectClusters':clusters,'negativeAndCoverageClaims':review.get('coverageSummary'),'reviewReportedRootCauseGrouping':review.get('rootCauseGrouping'),'retainedPositiveObservations':[f for f in original_findings if f.get('kind')=='positive_observation'],'classicalFalsePositiveRate':{'value':None,'reviewedNegativeDenominator':None,'reason':'Snapshot/check counts and broad coverage summaries do not enumerate a validated independent reviewed-negative atomic denominator. No zero denominator is reported as zero percent.'},'descriptiveAtomicArithmetic':{'uniqueTPKeys':len(tp),'uniqueFPKeys':len(fp),'confirmedD0FailureKeys':len(fail),'uniqueFNKeys':len(fail-tp),'uncertainClaimOccurrences':sum(m['classification']=='UNCERTAIN' for m in matches),'confirmedFalseDiscoveryFractionNumerator':len(fp),'confirmedFalseDiscoveryFractionDenominator':len(tp|fp),'missFractionNumerator':len(fail-tp),'missFractionDenominator':len(fail)},'scopePolicy':{'platformNames':'Exact own D0 names android and apple. Original ios strings remain verbatim in preserved findings.','broadFindings':'No automatic expansion into unnamed parameterized controls, text or token members.','uncertainty':'An unknown/unassessed/suspected or non-product observation never becomes a confirmed TP/FP. Same-condition adequately supported contradiction is required for FP.','findingClassification':'TP_ONLY/FP_ONLY/MIXED describe resolved exact atomic claims, with all unresolved subclaims retained separately; MIXED requires both TP and FP. UNCERTAIN has no resolved confirmed product claim; NO_CONFIRMED_CLAIM includes explicit productViolationClaimed=false.','independence':'Sequential own-review comparisons, procedural blindness on shared filesystem; no OS isolation claim.','forbiddenMaterialsRead':False}}
 mp=dest/'matching.json';write_new(mp,result)
 audit={'candidateId':sub,'checkedAtUTC':now(),'reviewSHA256Verified':sha(reviewpath)==REVIEWS[sub],'gradeSHA256Verified':sha(gradepath)==commit['grade']['sha256'],'originalFindingIdsPreserved':[f['id'] for f in original_findings],'exactPlatformKeyMembership':all((m['platform'],m['key']) in rowids for m in matches),'noDuplicateSameFindingAtomicPair':len(matches)==len({(m['findingId'],m['platform'],m['key']) for m in matches}),'allD0FailureKeysPartitionedIntoTPOrFN':tp <= fail and tp|{(x['platform'],x['key']) for x in fn}==fail,'noOriginalGradeEdits':True,'secondReviewReadDuringThisComparison':False,'matchingArtifact':item(mp)};assert all(audit[k] for k in ['reviewSHA256Verified','gradeSHA256Verified','exactPlatformKeyMembership','noDuplicateSameFindingAtomicPair','allD0FailureKeysPartitionedIntoTPOrFN']);ap=dest/'audit.json';write_new(ap,audit)
 seal={'schemaVersion':1,'candidateId':sub,'sealedAtUTC':now(),'review':item(reviewpath),'ownD0Grade':item(gradepath),'matching':item(mp),'audit':item(ap),'preservedOriginalReview':item(original),'matcher':item(pathlib.Path(__file__)),'definitions':item(METHODS),'qualityResultsIntentionallyOmitted':True};sp=dest/'comparison-seal.json';write_new(sp,seal);print(json.dumps({'comparisonSeal':item(sp),'sealedAtUTC':seal['sealedAtUTC'],'qualityResultsIntentionallyOmitted':True}))
if __name__=='__main__':build(sys.argv[1])
