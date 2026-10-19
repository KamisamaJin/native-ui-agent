import pathlib,json,hashlib,datetime,sys,collections
import raw_review as rr
sys.path.insert(0,str(rr.EVAL));import evaluator as ev
R=rr.ROOT/'validation/tool-forward';sys.path.insert(0,str(R));import verify_evidence
W=rr.HERE;SUB='submission-4f4364';GP=rr.EVAL/'paired-sealed'/SUB/'grade-v002.json';g=rr.load(GP);plan={r['assessmentId']:r for r in rr.PLAN};reviews={(r['platform'],r['contextId']):r for r in rr.load(W/'manual-pixel-reviews.json')['states']}
def rec(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=rr.sha(p))
assert verify_evidence.validate_grade(GP,'d0',SUB,True)==2209;assert ev.validate_report(g)
assert len(g['results'])==len({x['assessmentId'] for x in g['results']})==2209
sources=rr.load(W/'source-rows.json');assert [x for x in g['results'] if x['sourceOnly']]==sources
sourceOrigin=rr.EVAL/'d0-sealed'/SUB/'grade.json';assert rr.sha(sourceOrigin)=='72cb5aeada8ecb2dd200d2857143c3eebe68db6da11c822dc9aed982e77abb36'
# Extract only the authorized source-only rows for exact equality; runtime rows
# of the sealed original are neither compared nor used as paired evidence.
original_source=[x for x in rr.load(sourceOrigin)['results'] if x['sourceOnly']];assert original_source==sources
runtime=[x for x in g['results'] if not x['sourceOnly']];assert len(runtime)==1830 and len(sources)==379
methods=collections.defaultdict(collections.Counter);states=collections.defaultdict(collections.Counter);refs=[]
refCache={}
def validate_binding_ref(s,row):
 p=pathlib.Path(s['path'])
 if p not in refCache:
  ev.validate_ref(dict(path=str(p),sha256=s['sha256'],locator={'kind':'whole-file'}),row,[R/'paired-evidence/d0'],[])
  refCache[p]=dict(sha256=s['sha256'],document=None)
 cached=refCache[p];assert cached['sha256']==s['sha256']
 loc=s['locator']
 if loc['kind']=='json-pointer':
  if cached['document'] is None:cached['document']=rr.load(p)
  value=cached['document'];pointer=loc['pointer'];assert pointer=='' or pointer.startswith('/')
  for token in pointer.split('/')[1:] if pointer else []:
   token=token.replace('~1','/').replace('~0','~');value=value[int(token)] if isinstance(value,list) else value[token]
 elif loc['kind']!='whole-file':raise AssertionError('Unexpected binding locator')

for row in g['results']:
 assert all(row[k]==plan[row['assessmentId']][k] for k in ['key','platform','phase','contextId','aspect','target','criterion','expected','requirementRefs','sourceOnly'])
 if row['outcome']=='UNASSESSED':assert row['missingEvidenceMethod']
 if row['sourceOnly']:continue
 case=row['contextId'].split('/')[0];expected=R/'paired-evidence/d0'/('ios' if row['platform']=='apple' else 'android')/case
 for s in row['exactSources']+row['consideredSources']:
  p=pathlib.Path(s['path']);assert expected==p.parent or expected in p.parents;assert p.suffix not in ev.SOURCE_EXTENSIONS
 # Audit exact binding references as well as the decisive/considered evidence.
 for s in row['binding']['provenanceRefs']:
  p=pathlib.Path(s['path']);assert expected==p.parent or expected in p.parents
  validate_binding_ref(s,plan[row['assessmentId']])
 if row['criterion']=='fullyReadableTextEquals' and row['outcome']=='PASS':assert row['target'] in reviews[(row['platform'],row['contextId'])]['fields']
 if row['collectionScope'] if 'collectionScope' in row else False:raise AssertionError('Unexpected changed grade schema')
 methods[row['platform']+'/'+row['aspect']+'/'+row['criterion']][row['outcome']]+=1;states[row['platform']+'/'+row['contextId']][row['outcome']]+=1
for row in runtime:
 if row['criterion']=='executedNativeActivation' and row['outcome'] in ['PASS','FAIL']:
  mechanisms={x['observedActivationMechanism'] for x in rr.load(W/SUB/'raw-index.json')['records'] if x['id'] in row['acceptedEvidenceRecordIds']}
  allowed=ev.PHYSICAL_ACTIVATION if row['expected']['method']=='tap' else ev.ACCESSIBLE_ACTIVATION
  assert mechanisms and mechanisms<=allowed
 if row['criterion']=='minimumTouchBounds' and row['platform']=='apple':assert row['outcome']=='UNASSESSED'
checks={
 rr.EVAL.parent/'oracle.json':'3728d2961548354f866dc0490cd4d05b5513a9bd81813b8e45234bc0620c875b',
 rr.EVAL.parent.parent/'freeze-manifest.json':'dc362b438287d4f204b253488f45513f0e78164073a231f0d37eb76c6de8a811',
 rr.EVAL/'evaluator.py':'d3b14be70d890036cc1dd0989191e14e12d4f50afe182886e087488899b2d41d',
 rr.EVAL/'preparation-manifest.json':'89ddc9a1124218408076f6a06152723e6a04604ae4e0515355e1b28f095d305c',
 rr.EVAL/'d0-grades-seal.json':'f0971f33f53d90473db71590abf471c2e36af1ccfbb3a6645b2e373684f733b7',
 rr.EVAL/'final-grades-seal.json':'ddd7f906266498924813be74946375e23bccdad75d50c742ce1c34cdb418f284',
 rr.EVAL/'self-review-matching-seal.json':'b988c49e5fdec553a5da30348b5ec2c3fc07af709eb84fbcfd204f263f433104',
 R/'METHODS.md':'095e8ac34fb6f9e2d3a77536a348426212639e7c6a6630ee218801343ceb3f15',
 sourceOrigin:'72cb5aeada8ecb2dd200d2857143c3eebe68db6da11c822dc9aed982e77abb36'}
for p,digest in checks.items():assert rr.sha(p)==digest,(str(p),'old commitment changed')
oldsealed=[]
for p in [rr.EVAL/'d0-grades-seal.json',rr.EVAL/'final-grades-seal.json',rr.EVAL/'self-review-matching-seal.json']:oldsealed.append(rec(p))
audit=dict(schemaVersion=1,candidateId=SUB,phase='D0',runtimeCorpus='paired-evidence/d0 only',auditedAtUTC=ev.now(),mechanicalValidator='verify_evidence.validate_grade(path, d0, submission-4f4364, True)',mechanicalValidation='PASS',localFrozenEvaluatorValidation='PASS',requiredAtomicKeyCount=len(g['results']),runtimeAtomicKeyCount=len(runtime),reusedSourceAtomicKeyCount=len(sources),exactSourceRowsUnchanged=True,allRequiredMetadataUnchanged=True,allRuntimeExactAndConsideredSourcesArePaired=True,allBindingReferencesValid=True,fieldPassCoverageRecorded=True,actionMethodLimitsPreserved=True,strictUnassessedMethodsRetained=True,earlierCommitmentsUnchanged=[rec(p) for p in checks],outcomesByMethod={k:dict(v) for k,v in methods.items()},outcomesByState={k:dict(v) for k,v in states.items()},selectedGrade=rec(GP),scopeNote=rec(W/'scope-note.json'),pairedProvenanceInventory=rec(W/'provenance-inventory.json'),qualityInterpretation='Atomic conditions and methods only; callback counts do not independently diagnose an unavailable-dispatch handler, and native observer coverage gaps do not establish product failure.')
rr.write(W/'final-audit.json',audit);print('Paired full contract, coverage, exact-source and commitment audits passed')
