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
def manual_decisions(sub,review,rows):
 out={}
 if sub=='submission-b2e249':
  for f in review['findings']:
   fid=f['id'];matched=[];unverifiable=[];related=[]
   if fid=='SR-ANDROID-NOTES-CLIPPING':
    matched=[(r,'TP','The finding explicitly names this state and notes.title glyph clipping. This exact readability/overflow condition is independently FAIL in the sealed D0 pixels; no other text, token, chevron, or accessibility member is claimed.') for r in rows if scoped(f,r) and (r['criterion']=='horizontalOverflowRegionIdsEqual' or (r['criterion']=='fullyReadableTextEquals' and r['target']=='notes.title'))]
    unverifiable.append({'claim':'A rounded TextButton clip is the suspected cause; check other multiline TextButton labels.','certainty':'suspected/recommendation','atomicKeysClaimed':[],'rationale':'The cause and other controls were not confirmed and do not claim the radius/spacing predicates or additional state/member failures.'})
   elif fid=='SR-IOS-DISABLED-TOKENS':
    matched=[(r,'TP','The confirmed native-pixel claim explicitly identifies this case/initial state, disabled primary fill or glyph color, and the same numeric mismatch independently recorded as FAIL. Only the named disabled-primary representative probes are matched.') for r in rows if scoped(f,r) and r['criterion']=='sampledFlatColorMatches' and r['target']=='rr.primary']
    unverifiable.append({'claim':'Disabled primary colors in C03 initial/open and C04 initial/new-purchase; unavailable option/size text and reasons in C02/C04.','certainty':'confirmed','atomicKeysClaimed':[],'classification':'UNCERTAIN','rationale':'These explicitly described subclaims do not have same-target/same-state disabled color probes in the frozen D0 atomic matrix. C04 header/card color probes and legible-string/native-enabled assertions concern different conditions. No nearby PASS is treated as FP and no related FAIL is credited.'})
    unverifiable.append({'claim':'Default disabled appearance is the likely source mechanism.','certainty':'suspected','atomicKeysClaimed':[],'rationale':'Source mechanism speculation does not establish any additional runtime style member.'})
   elif fid=='SR-IOS-EXCHANGE-HEIGHT-DRIFT':
    related=[r for r in rows if r['platform']=='apple' and r['contextId']=='C06/initial' and r['criterion']=='entireCardReachableByParentVerticalScroll']
    unverifiable.append({'claim':f['claim'],'certainty':f['certainty'],'atomicKeysClaimed':[],'productViolationClaimed':False,'rationale':'The review explicitly disclaims a product violation. Changing lazy content-height metadata is not the frozen criterion of actual component reachability/overlapping coverage. Its evidence-quality caution is retained, without converting the related independently PASS reachability item into a product FP.'})
   elif fid=='SR-ANDROID-HOST-CANVAS':
    unverifiable.append({'claim':f['claim'],'certainty':f['certainty'],'atomicKeysClaimed':[],'productViolationClaimed':False,'rationale':'Explicit host/capture observation outside rr.card. The frozen matrix does not assert the demonstration outer-canvas token. No component margin, card palette, or native environment member is claimed as failing.'})
   elif fid=='SR-ANDROID-UNEXPORTED-SEMANTICS-FONTS':
    criteria={'expanded','heading','independentAccessibleDecorativeIconCount','resolvedFontFamilyIsNativeSystem','effectiveNativeScalingMatchesHost'}
    matched=[(r,'UNCERTAIN','Explicit unassessed-method claim for this named state and property; it is not a confirmed product failure. An independently assessed bounded native property is retained as a difference in evidence judgement, not a product FP.') for r in rows if scoped(f,r) and (r['criterion'] in criteria or (r['criterion']=='accessibilityValueEquals' and r['target']=='rr.progress'))]
    unverifiable.append({'claim':'Android physical OS touch and screen-reader activation not demonstrated; native OnClick was used.','certainty':'unassessed','atomicKeysClaimed':[],'rationale':'No specific activation-checkpoint state is listed in this finding. The full-state list is not silently expanded to every action member; actual OnClick facts remain in the sealed grade.'})
   elif fid=='SR-IOS-UNEXPORTED-FONTS-HIT-TRAITS':
    criteria={'heading','independentAccessibleDecorativeIconCount','resolvedFontFamilyIsNativeSystem','unscaledPointOrSpRange','effectiveNativeScalingMatchesHost'}
    matched=[(r,'UNCERTAIN','Explicit unassessed-method claim for this named state and resolved-font/trait property; native AX dimensions/source styles cannot supply the missing method. This is not a confirmed product failure.') for r in rows if scoped(f,r) and r['criterion'] in criteria]
    unverifiable.extend([{'claim':'Physical hit regions remain unassessed.','certainty':'unassessed','atomicKeysClaimed':[],'rationale':'The finding names the method/category but does not name individual controls of the parameterized touch-target group. Preserve the group-level limitation without automatically claiming every mandatory member.'},{'claim':'Accessibility performAction activation remains unassessed; adapter executes XCUI tap.','certainty':'unassessed','atomicKeysClaimed':[],'rationale':'The finding lists full-state checkpoints, not exact activation checkpoint states. No action-member expansion or product failure is invented.'}])
   else:raise ValueError('Unreviewed original finding '+fid)
   out[fid]={'matches':matched,'unverifiable':unverifiable,'related':related}
 else:raise ValueError('Second comparison has not yet been authorized by completion of first comparison')
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
   out.append({'originalEvidence':e,'resolvedBy':'exact SHA256 from sealed D0 evidence/source inventory' if found else None,'independentlyResolvedSources':found,'status':'BOUND_TO_SEALED_D0' if found else 'REVIEW_DERIVATIVE_OR_REFERENCE_NOT_OPENED','limitation':None if found else 'Retained as originally reported; scratch/other review artifacts are not permitted source material for this comparison and were not opened.'})
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
 result={'schemaVersion':1,'candidateId':sub,'phase':'D0_SELF_REVIEW_MATCHING','generatedAtUTC':now(),'definitions':item(METHODS),'d0JointSeal':item(EVAL/'d0-grades-seal.json'),'finalJointSeal':item(EVAL/'final-grades-seal.json'),'ownD0Grade':item(gradepath),'originalReview':item(reviewpath),'preservedOriginalReview':item(original),'originalFindingCount':len(original_findings),'findings':findings,'atomicMatches':matches,'confirmedD0FailureKeysNotDetectedAsTP':fn,'suspectedOrUnassessedClaims':suspected,'unverifiableClaims':unverifiable,'duplicates':duplicates,'relatedButNotMatched':related,'defectClusters':clusters,'negativeAndCoverageClaims':review.get('coverageSummary'),'classicalFalsePositiveRate':{'value':None,'reviewedNegativeDenominator':None,'reason':'Snapshot/check counts and broad coverage summaries do not enumerate a validated independent reviewed-negative atomic denominator. No zero denominator is reported as zero percent.'},'descriptiveAtomicArithmetic':{'uniqueTPKeys':len(tp),'uniqueFPKeys':len(fp),'confirmedD0FailureKeys':len(fail),'uniqueFNKeys':len(fail-tp),'uncertainClaimOccurrences':sum(m['classification']=='UNCERTAIN' for m in matches),'confirmedFalseDiscoveryFractionNumerator':len(fp),'confirmedFalseDiscoveryFractionDenominator':len(tp|fp),'missFractionNumerator':len(fail-tp),'missFractionDenominator':len(fail)},'scopePolicy':{'platformNames':'Exact own D0 names android and apple. Original ios strings remain verbatim in preserved findings.','broadFindings':'No automatic expansion into unnamed parameterized controls, text or token members.','uncertainty':'An unknown/unassessed/suspected or non-product observation never becomes a confirmed TP/FP. Same-condition adequately supported contradiction is required for FP.','findingClassification':'TP_ONLY/FP_ONLY/MIXED describe resolved exact atomic claims, with all unresolved subclaims retained separately; MIXED requires both TP and FP. UNCERTAIN has no resolved confirmed product claim; NO_CONFIRMED_CLAIM includes explicit productViolationClaimed=false.','independence':'Sequential own-review comparisons, procedural blindness on shared filesystem; no OS isolation claim.','forbiddenMaterialsRead':False}}
 mp=dest/'matching.json';write_new(mp,result)
 audit={'candidateId':sub,'checkedAtUTC':now(),'reviewSHA256Verified':sha(reviewpath)==REVIEWS[sub],'gradeSHA256Verified':sha(gradepath)==commit['grade']['sha256'],'originalFindingIdsPreserved':[f['id'] for f in original_findings],'exactPlatformKeyMembership':all((m['platform'],m['key']) in rowids for m in matches),'noDuplicateSameFindingAtomicPair':len(matches)==len({(m['findingId'],m['platform'],m['key']) for m in matches}),'allD0FailureKeysPartitionedIntoTPOrFN':tp <= fail and tp|{(x['platform'],x['key']) for x in fn}==fail,'noOriginalGradeEdits':True,'secondReviewReadDuringThisComparison':False,'matchingArtifact':item(mp)};assert all(audit[k] for k in ['reviewSHA256Verified','gradeSHA256Verified','exactPlatformKeyMembership','noDuplicateSameFindingAtomicPair','allD0FailureKeysPartitionedIntoTPOrFN']);ap=dest/'audit.json';write_new(ap,audit)
 seal={'schemaVersion':1,'candidateId':sub,'sealedAtUTC':now(),'review':item(reviewpath),'ownD0Grade':item(gradepath),'matching':item(mp),'audit':item(ap),'preservedOriginalReview':item(original),'matcher':item(pathlib.Path(__file__)),'definitions':item(METHODS),'qualityResultsIntentionallyOmitted':True};sp=dest/'comparison-seal.json';write_new(sp,seal);print(json.dumps({'comparisonSeal':item(sp),'sealedAtUTC':seal['sealedAtUTC'],'qualityResultsIntentionallyOmitted':True}))
if __name__=='__main__':build(sys.argv[1])
