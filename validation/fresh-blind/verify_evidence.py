#!/usr/bin/env python3
"""Portable integrity/coverage audit; does not rerun native SDKs or judge images."""
import hashlib,json,xml.etree.ElementTree as ET
from datetime import datetime
from collections import Counter
from pathlib import Path
from PIL import Image
import verify_frozen
R=Path(__file__).resolve().parent
ROOT=R.parents[1]

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def epoch(value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def portable(path):
 p=Path(path)
 if not p.is_absolute():return (R/p).resolve()
 for anchor in ['validation/','native-ui-agent/']:
  if anchor in str(p):
   assert str(p).count(anchor)==1
   return ROOT/(anchor+str(p).split(anchor,1)[1])
 raise AssertionError('Unknown archived absolute path: '+str(p))

def evidence_refs(value):
 if isinstance(value,dict):
  if isinstance(value.get('path'),str) and value.get('sha256'):
   p=portable(value['path']);assert p.is_relative_to(ROOT) and p.is_file(),str(p);assert sha(p)==value['sha256'],str(p)
  for child in value.values():evidence_refs(child)
 elif isinstance(value,list):
  for child in value:evidence_refs(child)

def check_grades(phase,sub,cases):
 counts={}
 for platform in ['android','ios']:
  p=R/'design/grader'/f'{sub}-{phase}-{platform}.json';d=read(p)
  assert d['phase'].lower()==phase and d['submission']==sub and d.get('sealedAtUTC')
  assert d['blinding']['armMappingUnknown'] is True
  rows=d['platforms'][platform]['cases'];assert {c['caseId']for c in rows}==set(cases)
  tally=Counter()
  for c in rows:
   ratings=c['ratings'];assert len(ratings)==len(cases[c['caseId']])
   assert {x['ruleId']for x in ratings}==set(cases[c['caseId']])
   assert len({x['ruleId']for x in ratings})==len(ratings)
   for rating in ratings:
    assert rating['status'] in {'passed','failed','unassessed'};tally[rating['status']]+=1
    if rating['status'] in {'passed','failed'}:assert rating['evidence']
  summary=d['platforms'][platform]['summary']
  for state in ['passed','failed','unassessed']:assert tally[state]==summary[state],(p,state,tally,summary)
  assert sum(tally.values())==summary['applicableCaseRulePairs']
  evidence_refs(d);counts[platform]=dict(tally)
 return counts

def check_capture(phase,sub,platform,case):
 dest=R/'evidence'/phase/sub/platform/case['caseId'];index=read(dest/'archived-files.json')
 for path,h in index['files'].items():
  p=(dest/path).resolve();assert p.is_relative_to(dest.resolve()) and sha(p)==h
 capture=read(dest/'capture.json');assert capture['platform']==platform and capture['status']=='captured_not_graded'
 spec=dict(case['fixture']);spec['actions']=[{k:v for k,v in a.items()if k in {'type','identifier','checkpoint','model','direction'}}for a in case['protocol']]
 assert hashlib.sha256((json.dumps(spec,indent=2)+'\n').encode()).hexdigest()==capture['fixture_sha256']
 prod=read(R/'implementations'/phase/sub/'manifest.json')['files']
 prefix='reply/Reply/'if platform=='android'else'alerttoast/'
 expected={k[len(prefix):]:v for k,v in prod.items()if k.startswith(prefix)}
 assert expected and capture['sources']==expected,(phase,sub,platform,case['caseId'])
 obs=read(dest/'observation.json');assert obs['snapshots']
 for snapshot in obs['snapshots']:
  p=(dest/snapshot['screenshot']).resolve();assert p.is_relative_to(dest.resolve()) and p.is_file()
  with Image.open(p)as im:assert im.width>0 and im.height>0
 if platform=='android':
  native=ET.parse(dest/'junit.xml').getroot().attrib
  assert native['tests']=='1' and native['failures']=='0' and native['errors']=='0'
  assert obs['phase']=='complete'
 else:
  manifest=read(dest/'manifest.json');native=read(dest/'native-summary.json')
  assert manifest['native_test_count']==native['totalTestCount']==1
  assert native['passedTests']+native['failedTests']==1 and native['skippedTests']==0
  # Native transport/action failure stays in evidence; it is not a product pass.
  for path,h in manifest['image_hashes'].items():assert sha(dest/path)==h
  for path,h in expected.items():
   matches=[v for k,v in manifest['source_hashes'].items()if k.endswith('/alerttoast/'+path)]
   assert matches==[h]
 return len(obs['snapshots'])

def main():
 verify_frozen.main()
 patch=read(R/'shipped-adapter-patch.json');frozen=read(R/'freeze.json')['skill_v2']
 for item in patch['files']:
  p=R/'shipped-adapter'/item['file'].removeprefix('native-ui-agent/');assert p.is_file() and sha(p)==item['afterSha256']
  assert frozen[item['file'].removeprefix('native-ui-agent/')]==item['beforeSha256']
  if item.get('sameCommonAdapter'):assert sha(ROOT/item['sameCommonAdapter'])==item['afterSha256']
 for path in patch['genericNativeEvidence']:assert (R/path).is_file()
 # Retained failures and superseded samples remain independently hash-verifiable.
 for index_path in (R/'evidence').rglob('archived-files.json'):
  dest=index_path.parent
  for path,h in read(index_path)['files'].items():
   p=(dest/path).resolve();assert p.is_relative_to(dest.resolve()) and sha(p)==h
 oracle=read(R/'design/private/oracle.json');subs=sorted(p.name for p in(R/'implementations/d0').glob('submission-*'));assert len(subs)==3
 capture_count=snapshot_count=0;grade_counts={}
 for phase in ['d0','final']:
  selected=[c for c in oracle['cases']if phase=='final'or c['phase']=='initial'];cases={c['caseId']:c['applicableRuleIds']for c in selected}
  for sub in subs:
   assert(R/'implementations'/phase/sub/'manifest.json').is_file()
   for platform in ['android','ios']:
    for case in selected:snapshot_count+=check_capture(phase,sub,platform,case);capture_count+=1
   grade_counts[f'{phase}/{sub}']=check_grades(phase,sub,cases)
 assert capture_count==84
 replay=read(R/'replay/replay.json');assert set(replay['platforms'])=={'android','ios'}
 for platform in ['android','ios']:
  dest=R/'replay'/platform
  assert replay['platforms'][platform]['nativeTestCount']==1
  assert sha(dest/'capture.json')==replay['platforms'][platform]['captureSha256']
  for path,h in read(dest/'archived-files.json')['files'].items():assert sha(dest/path)==h
 for seal_name in ['review-seals.json','final-source-seals.json']:
  for key,h in read(R/seal_name)['files'].items():assert sha(R/key)==h
 for key,h in read(R/'d0-grade-seals.json')['files'].items():assert sha(R/key)==h
 release=read(R/'unblinding.json')
 receipt=read(R/'matching-inputs/release-receipt.json')
 assert receipt['allFinalGradesSealed'] and receipt['sourceFinalGradeSealsSha256']==sha(R/'final-grade-seals.json')
 for sub,item in receipt['submissions'].items():
  original=read(R/item['sourceReport']);copy=read(R/item['findingCopy'])
  assert sha(R/item['sourceReport'])==item['sourceReportSha256'] and sha(R/item['findingCopy'])==item['findingCopySha256']
  assert copy['findings']==original['findings'] and copy['sourceReportSha256']==item['sourceReportSha256']
 for key,h in read(R/'final-grade-seals.json')['files'].items():
  assert sha(R/key)==h and epoch(read(R/key)['sealedAtUTC'])<=epoch(receipt['releasedAtUTC'])
 matching=read(R/'design/grader/review-match.json');assert matching['blinding']['armMappingUnknown']
 assert epoch(matching['sealedAtUTC'])<=epoch(release['releasedAtUTC'])
 evidence_refs(matching)
 assert sha(R/'released-assignment.json')==read(R/'freeze.json')['assignment_sha256']
 assert sha(R/'released-submissions.json')==read(R/'freeze.json')['submissions_sha256']
 assignment=read(R/'released-assignment.json');anonymous=read(R/'released-submissions.json')
 assert release['submissions']=={sub:assignment[unit]for unit,sub in anonymous.items()}
 for key,h in release['graderSeals'].items():assert sha(R/key)==h
 for sub in subs:
  compat_path=R/'build-evidence/final'/sub/'compatibility.json';compat=read(compat_path)
  assert compat['productionArchiveManifestSha256']==sha(R/'implementations/final'/sub/'manifest.json')
  production=read(R/'implementations/final'/sub/'manifest.json')['files']
  assert compat['sourceFiles'] and all(production[k]==v for k,v in compat['sourceFiles'].items())
  assert {c['target']for c in compat['commands']}=={'arm64-apple-ios14.0-simulator','arm64-apple-macosx11.0'}
  for command in compat['commands']:assert command['exitCode']==0 and sha(compat_path.parent/command['log'])==command['logSha256']
  for phase in ['readonly-review','repair']:
   dest=R/'phase-reports'/sub/phase
   for key,h in read(dest/'manifest.json')['files'].items():assert sha(dest/key)==h
  review=read(R/'phase-reports'/sub/'readonly-review/reports/self-review.json')
  repair=read(R/'phase-reports'/sub/'repair/reports/repair.json')
  # Normalized phase timing retains source report paths/hashes in timing.json.
  t=read(R/'timing.json')['submissions'][sub]
  for platform in ['android','ios']:
   assert epoch(read(R/'design/grader'/f'{sub}-d0-{platform}.json')['sealedAtUTC'])<=epoch(t['readonlyReview']['startedAtUTC'])
   assert epoch(read(R/'design/grader'/f'{sub}-final-{platform}.json')['sealedAtUTC'])<=epoch(release['releasedAtUTC'])
  assert epoch(t['readonlyReview']['endedAtUTC'])<=read(R/'phase-reports'/sub/'readonly-review/manifest.json')['sealed_at']<=epoch(t['repair']['startedAtUTC'])
  assert t['readonlyReview']['durationSeconds']<=720
  if t['repair']['durationSeconds']>900:
   exceptions=read(R/'protocol-deviations.json')['deviations']
   assert any(x['submission']==sub and x['phase']=='repair'and x['actualSeconds']==t['repair']['durationSeconds'] and sha(R/x['report'])==x['reportSha256'] for x in exceptions)
 scope=read(R/'design/grader/coverage-scope-addendum.json');evidence_refs(scope)
 assert scope['blinding']['armMappingUnknown'] and scope['preservationVerification']['allTwelveOriginalGradesUnchanged']
 assert scope['preservationVerification']['reviewMatchSha256']==sha(R/'design/grader/review-match.json')
 assert scope['conservativeFullRequirementCoverageRollup']['fullRequirementCoverageRollupAvailable'] is False
 report_seal=read(R/'reporting-audit-seal.json');assert report_seal['unblindingReceiptSha256']==sha(R/'unblinding.json')
 for path,h in report_seal['files'].items():assert sha(R/path)==h
 assert epoch(release['releasedAtUTC'])<=epoch(scope['sealedAtUTC'])<=epoch(report_seal['sealedAtUTC'])
 for item in scope['conservativeFullRequirementCoverageRollup']['knownScopeExclusionBounds']:
  sub,phase,platform=item['artifactId'].split('/');grade=read(R/'design/grader'/f'{sub}-{phase.lower()}-{platform}.json')
  for cohort in item['cohorts']:
   chosen=[c for c in grade['platforms'][platform]['cases']if cohort['cohort']=='all'or (c['caseId'].startswith('initial_')if cohort['cohort']=='initial'else c['caseId'].startswith('repair_holdout_'))]
   statuses={(c['caseId'],rating['ruleId']):rating['status']for c in chosen for rating in c['ratings']};tally=Counter(statuses.values())
   assert all(tally[state]==cohort['sealedCountsUnchanged'][state]for state in ['passed','failed','unassessed'])
   limited={(x['caseId'],x['ruleId'])for x in cohort['exactKnownLimitedPairs']};assert all(statuses[p]=='passed'for p in limited)
   assert len(limited)==cohort['knownPassedEntriesWithRequiredTouchRegionGap']
   assert tally['passed']-len(limited)==cohort['maximumPossibleFullySupportedPassEntriesAfterKnownExclusions']
 import metrics
 assert read(R/'result-summary.json')==metrics.calculate()
 print(json.dumps({'status':'passed_archived_new_trial_audit','native_captures':capture_count,'native_snapshots':snapshot_count,'case_rule_counts':grade_counts,'does_not_replay':'AI decisions, native SDKs, visual grading, precision fonts or physical Android taps'}))
if __name__=='__main__':main()
