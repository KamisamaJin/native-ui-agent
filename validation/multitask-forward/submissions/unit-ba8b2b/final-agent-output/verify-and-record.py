from pathlib import Path
import json,hashlib,difflib,time
root=Path(__file__).resolve().parents[2]
out=root/'agent-output/repair'
submission=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/submissions/unit-ba8b2b')
source='alerttoast/Sources/AlertToast/CollectionConditionReviewPanel.swift'
original=submission/'d0/source'/source
patch=''.join(difflib.unified_diff(original.read_text().splitlines(True),(root/source).read_text().splitlines(True),fromfile='original/'+source,tofile='repaired/'+source))
(out/'production.patch').write_text(patch)
source_seal=json.loads((submission/'d0/seal.json').read_text())
changes=[]
for path,digest in source_seal['files'].items():
 p=root/path
 if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changes.append(path)
plans=[]
for p in (submission/'initial-agent-output/plans').rglob('*.json'):
 local=root/'agent-output/plans'/p.relative_to(submission/'initial-agent-output/plans')
 plans.append({'path':str(local.relative_to(root)),'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'unchanged':local.read_bytes()==p.read_bytes()})
(out/'immutability.json').write_text(json.dumps({'changed_sealed_source_files':changes,'original_plans':plans},indent=2)+'\n')
review_path=submission/'original-review/review.json'
review=json.loads(review_path.read_text())
start=json.loads((out/'phase-start.json').read_text())
record={
 'version':1,'startedAtUnix':start['startedAtUnix'],'finishedAtUnix':time.time(),
 'changed_files':changes,
 'source_sha256':{path:hashlib.sha256((root/path).read_bytes()).hexdigest() for path in changes},
 'original_findings_addressed':[
  {'cluster':'ios-replacement-seed','original_assertions':[{'case':x['case'],'platform':x['platform'],'id':x['id']} for x in review['machine_failure_ids']],
   'source_change':'Observe an Equatable replacement value containing the full incoming request; compare ids but seed decisions and focus from the new value passed by SwiftUI, avoiding the prior closure-captured request.',
   'status':'source_repaired_compile_verified_runtime_unassessed'},
  {'cluster':'ios-disabled-visible-palette','original_scope':'Original iOS light disabled primary and dark read-only classification controls, plus state duplicates retained in original review.',
   'source_change':'Replace PlainButtonStyle with a ButtonStyle returning the explicitly colored label, so disabled visual roles are not faded a second time. Native Button disabled state and selected traits remain applied.',
   'status':'source_repaired_compile_verified_visible_result_unassessed'}
 ],
 'unresolved_and_why':[
  'No new rendered or runtime feedback is authorized; final replacement, callback, selected-state, geometry and visible-palette behavior are unassessed for the repaired source.',
  'All original computed SwiftUI typography/color/ellipsis U cells remain U; this source repair does not expose those native properties.',
  'P2 blocked disabled classification dispatch remains unassessed as handler behavior on both platforms.',
  'Only original public P1/P2 routes supplied runtime evidence; other legal caller combinations remain without rendered runtime coverage.',
  'Android had no confirmed original production finding and was left byte-identical.'
 ],
 'commands':[
  {'purpose':'Read authorized repair instructions and original sealed review/source','command':'cat repair prompt; read assigned production SwiftUI source; read original-review/review.json root_cause_clusters'},
  {'purpose':'Apply targeted SwiftUI repair','command':'Python source replacement adding ConditionReplacement and ConditionButtonStyle, replacing the two PlainButtonStyle uses, and passing replacement.request into reset.'},
  {'purpose':'iOS compile-only','record':'agent-output/repair/repair-compile-ios-01-command.json','build_record':'agent-output/repair/repair-compile-ios-01-record.json','log':'agent-output/repair/repair-compile-ios-01-build.log','exitCode':0},
  {'purpose':'Failed original-source patch lookup','record':'agent-output/repair/inspection-failure-01.json','exitCode':1,'recovery':'Located the source/ directory within own D0 submission and generated the patch from its actual path.'},
  {'purpose':'Save final patch, hash check and repair record','script':'agent-output/repair/verify-and-record.py','exitCode':0}
 ],
 'logs':['agent-output/repair/repair-compile-ios-01.log','agent-output/repair/repair-compile-ios-01-build.log','agent-output/repair/production.patch','agent-output/repair/inspection-failure-01.log'],
 'original_review':{'path':str(review_path),'sha256':hashlib.sha256(review_path.read_bytes()).hexdigest()},
 'original_plans_unchanged':all(p['unchanged'] for p in plans),
 'scope_limits':['No renders, screenshots, observers, previews, SDK app launches, new feedback, expected-value changes, bridge/host edits or further repair cycle.','Compilation used the authorized no-render helper only.','No commits or pushes.','FINAL acceptance is not available and is not claimed.']
}
record['elapsedSeconds']=record['finishedAtUnix']-record['startedAtUnix']
(out/'repair.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'changed_files':changes,'plans_unchanged':record['original_plans_unchanged'],'elapsedSeconds':record['elapsedSeconds'],'source_sha256':record['source_sha256']},indent=2))
print(patch)
