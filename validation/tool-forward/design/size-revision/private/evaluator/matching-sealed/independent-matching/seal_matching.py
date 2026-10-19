"""Score-free joint commitment after sequential independent comparisons are sealed."""
import collections,datetime,hashlib,json,pathlib,shutil
ROOT=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');EVAL=ROOT/'validation/tool-forward/design/size-revision/private/evaluator';HERE=pathlib.Path(__file__).parent
SUBS=['submission-b2e249','submission-4f4364']
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def item(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def write_new(p,x):
 if p.exists():raise RuntimeError('Refusing immutable artifact overwrite '+str(p))
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def verify_item(i):
 p=pathlib.Path(i['path']);assert p.is_file() and p.stat().st_size==i['bytes'] and sha(p)==i['sha256'];return p
assert sha(EVAL/'d0-grades-seal.json')=='f0971f33f53d90473db71590abf471c2e36af1ccfbb3a6645b2e373684f733b7'
assert sha(EVAL/'final-grades-seal.json')=='ddd7f906266498924813be74946375e23bccdad75d50c742ce1c34cdb418f284'
methods=ROOT/'validation/tool-forward/METHODS.md';assert sha(methods)=='095e8ac34fb6f9e2d3a77536a348426212639e7c6a6630ee218801343ceb3f15'
audits=[];staged=[]
for sub in SUBS:
 d=HERE/sub;seal=load(d/'comparison-seal.json')
 for k in ['review','ownD0Grade','matching','audit','preservedOriginalReview','matcher','definitions']:verify_item(seal[k])
 review=load(pathlib.Path(seal['review']['path']));grade=load(pathlib.Path(seal['ownD0Grade']['path']));m=load(pathlib.Path(seal['matching']['path']));rows={(r['platform'],r['key']):r for r in grade['results']}
 assert len(rows)==2209 and grade['phase']=='D0' and grade['candidateId']==sub
 assert m['originalFindingCount']==len(review['findings'])==len(m['findings']);assert [f['originalFinding'] for f in m['findings']]==review['findings']
 assert sha(pathlib.Path(m['preservedOriginalReview']['path']))==sha(pathlib.Path(m['originalReview']['path']))
 assert m['negativeAndCoverageClaims']==review.get('coverageSummary')
 source=load(pathlib.Path(seal['ownD0Grade']['path']).parent/'source-inventory.json');hashes={x['sha256'] for x in source['files']}
 fingerprints=review['sourceFingerprintsBefore'];assert fingerprints==review['sourceFingerprintsAfter'];assert all(h in hashes for h in fingerprints.values())
 findings={f['id']:f for f in review['findings']};matches=m['atomicMatches'];seen=set();tp=set();fp=set();dups=collections.defaultdict(list)
 for a in matches:
  ident=(a['platform'],a['key']);f=findings[a['findingId']];r=rows[ident]
  assert a['assessmentId']==r['assessmentId'] and a['contextId']==r['contextId'] and a['aspect']==r['aspect'] and a['target']==r['target'] and a['criterion']==r['criterion']
  assert a['d0Outcome']==r['outcome'] and a['requiredBinding']==r['requiredBinding']
  assert a['classification'] in ['TP','FP','UNCERTAIN'];assert (a['findingId'],*ident) not in seen;seen.add((a['findingId'],*ident))
  assert r['contextId'] in {x.replace('--','/',1) for x in f.get('stateIds',[])}
  allowed=['android','apple'] if f['platform']=='both' else [{'ios':'apple'}.get(f['platform'],f['platform'])];assert r['platform'] in allowed
  assert a['reviewExactSource']['sha256']==seal['review']['sha256'] and a['d0GradeExactSource']['sha256']==seal['ownD0Grade']['sha256']
  if a['classification'] in ['TP','FP']:
   assert f['certainty']=='confirmed' and f.get('productViolationClaimed',True)
   assert r['outcome']==('FAIL' if a['classification']=='TP' else 'PASS') and a['exactEvidencePaths']
  if a['classification']=='TP':tp.add(ident)
  if a['classification']=='FP':fp.add(ident)
  dups[ident].append(a)
 fail={k for k,r in rows.items() if r['outcome']=='FAIL'};fn={(f['platform'],f['key']) for f in m['confirmedD0FailureKeysNotDetectedAsTP']}
 assert not(tp&fp) and fn==fail-tp
 assert {(d['platform'],d['key']) for d in m['duplicates']}=={k for k,v in dups.items() if len(v)>1}
 for duplicate in m['duplicates']:
  assert duplicate['occurrences']==[{'findingId':a['findingId'],'classification':a['classification']} for a in dups[(duplicate['platform'],duplicate['key'])]]
 c=load(pathlib.Path(seal['ownD0Grade']['path']).parent/'coverage-and-method-audit.json')['defectClusters'];assert {x['clusterId'] for x in m['defectClusters']}==set(c)
 for cl in m['defectClusters']:
  assert {x['assessmentId'] for x in cl['members']}==set(c[cl['clusterId']]['memberAssessmentIds']);assert cl['independentClusterSampleSize'] is None
  for x in cl['members']:assert x['discovered']==((x['platform'],x['key']) in tp)
 assert m['classicalFalsePositiveRate']['value'] is None and m['classicalFalsePositiveRate']['reviewedNegativeDenominator'] is None
 audit={'candidateId':sub,'checkedAtUTC':now(),'originalFindingsPreservedExactly':True,'originalSourceFingerprintsMatchOwnD0SealedSource':True,'exactPlatformStateAspectKeyMatchVerified':True,'allConfirmedMatchesSupportedByOwnD0OutcomeAndExactEvidence':True,'unassessedAndSuspectedClaimsRetained':True,'duplicateOccurrencesRetainedUniqueArithmeticVerified':True,'allOwnD0FailuresPartitionIntoTPAndFN':True,'originalGradesUnchanged':True,'classicalNegativeDenominatorNotInvented':True,'preReviewDescriptiveClusterMembersPreserved':True,'arithmeticVerified':m['descriptiveAtomicArithmetic'],'originalFindingCount':m['originalFindingCount'],'matching':item(d/'matching.json'),'comparisonSeal':item(d/'comparison-seal.json'),'reviewSourceFingerprints':fingerprints,'forbiddenMaterialsRead':False}
 audits.append(audit);staged.append((sub,d,seal))
assert load(HERE/SUBS[0]/'comparison-seal.json')['sealedAtUTC'] < load(HERE/SUBS[1]/'comparison-seal.json')['sealedAtUTC']
dest=EVAL/'matching-sealed';assert not dest.exists();dest.mkdir()
commitments=[]
for sub,d,seal in staged:
 sd=dest/sub;sd.mkdir()
 for name in ['review-original.json','matching.json','audit.json','comparison-seal.json']:shutil.copyfile(d/name,sd/name)
 a=next(x for x in audits if x['candidateId']==sub);ap=sd/'joint-validation.json';write_new(ap,a)
 commitments.append(dict(candidateId=sub,individualComparisonSealedAtUTC=seal['sealedAtUTC'],matching=item(sd/'matching.json'),preservedOriginalReview=item(sd/'review-original.json'),individualComparisonSeal=item(sd/'comparison-seal.json'),individualAudit=item(sd/'audit.json'),jointValidation=item(ap),ownD0Grade=seal['ownD0Grade'],originalReview=seal['review']))
method=dest/'independent-matching';method.mkdir()
for name in ['match_reviews.py','match_reviews_b.py','decisions_b.py','seal_matching.py']:shutil.copyfile(HERE/name,method/name)
shutil.copyfile(methods,method/'METHODS.md');shutil.copyfile(ROOT/'validation/tool-forward/methods-commitment.json',method/'methods-commitment.json')
protocol={'scope':'Both sequential sealed own-review versus own D0 comparisons only; all FINAL grades were sealed first.','definitionsSHA256':sha(methods),'comparisonOrder':SUBS,'secondReviewReadOnlyAfterFirstIndividualSeal':True,'assignmentCapabilityRepairReportsAndPairedCorpusRead':False,'originalReviewMetadataAndCitations':'Original findings, certainty, scope, evidence paths, commands and coverage are preserved literally in byte-identical original review copies. Referenced capability/tool/scratch/cache files were not opened. A named source method does not authorize runtime inference.','exactMatching':'Only explicitly supported case/state/aspect atomic predicates can be TP/FP. Unnamed parameterized members are not expanded. Confirmed product TP requires sealed D0 FAIL; FP requires adequate same-condition contradictory PASS. Unknown/suspected/method-limited and non-product observations are retained separately.','duplicatePolicy':'Every original finding and repeated atomic claim occurrence is retained; unique platform/key controls descriptive arithmetic.','negativePolicy':'Positive/equal observations and unresolved claims are preserved; snapshot counts do not create a classical reviewed-negative denominator.','clusterPolicy':'Use own D0 descriptive clusters sealed before reviews; correlated members/clusters do not establish an independent sample size.','proceduralBlindness':'Shared filesystem procedural discipline only; no OS isolation claim.'};write_new(method/'matching-protocol.json',protocol)
fm=EVAL/'self-review-matching-files-manifest.json';sealed=now();write_new(fm,{'phase':'D0_SELF_REVIEW_MATCHING','sealedAtUTC':sealed,'files':[item(p) for p in sorted(dest.rglob('*')) if p.is_file()],'qualityResultsIntentionallyOmitted':True})
joint=EVAL/'self-review-matching-seal.json';write_new(joint,dict(schemaVersion=1,phase='D0_SELF_REVIEW_MATCHING',sealedAtUTC=sealed,definitions=item(methods),methodsCommitment=item(ROOT/'validation/tool-forward/methods-commitment.json'),ownD0JointGradeSeal=item(EVAL/'d0-grades-seal.json'),priorFinalJointGradeSeal=item(EVAL/'final-grades-seal.json'),comparisonCommitments=commitments,fileManifest=item(fm),qualityResultsIntentionallyOmitted=True,assignmentCapabilityRepairReportsOrPairedCorpusRead=False,scope='Both sequential own-review comparisons independently sealed before assignment or later paired grading. All original grades unchanged; exact platform/key matching, original/uncertain/duplicate/negative evidence retained. Procedural blindness on shared filesystem; no OS isolation claim.'))
for x in load(fm)['files']:verify_item(x)
print(json.dumps({'seal':item(joint),'sealedAtUTC':sealed,'fileManifest':item(fm),'qualityResultsIntentionallyOmitted':True},indent=2))
