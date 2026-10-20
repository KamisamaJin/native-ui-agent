from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
base=Path(__file__).resolve().parent.parent;out=base/'agent-output'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
start=json.loads((out/'repair-start.json').read_text())
review=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward/submissions/unit-092e15/original-review/review.json')
swift=base/'alerttoast/Sources/AlertToast/WorkshopEnrollmentCard.swift'
kotlin=base/'reply/Reply/app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt'
checks=[]
for platform in ['ios','android']:
 folder=out/f'compile-{platform}-repair-01';r=json.loads((folder/'record.json').read_text())
 checks.append({'platform':platform,'kind':'common_compile_only_no_render','record':str(folder/'record.json'),'record_sha256':sha(folder/'record.json'),'log':str(folder/'build.log'),'log_sha256':sha(folder/'build.log'),'argv':r['argv'],'cwd':r['cwd'],'exit_code':r['exitCode'],'start_utc':datetime.fromtimestamp(r['startedAtUnix'],timezone.utc).isoformat(),'end_utc':datetime.fromtimestamp(r['finishedAtUnix'],timezone.utc).isoformat(),'wall_seconds':r['finishedAtUnix']-r['startedAtUnix']})
original_plan_seal=json.loads((out/'plans-seal.json').read_text())
assert all(sha(out/n)==h for n,h in original_plan_seal['files'].items())
original_review_seal=json.loads((out/'review-seal.json').read_text())
assert all(sha(n)==h for n,h in original_review_seal['artifacts'].items())
end=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
record={
 'phase':'single_bounded_product_repair','start_utc':start['start_utc'],'end_utc':end,'wall_seconds':(datetime.fromisoformat(end.replace('Z','+00:00'))-datetime.fromisoformat(start['start_utc'].replace('Z','+00:00'))).total_seconds(),'budget_minutes':15,
 'changes':[
  {'file':str(kotlin),'scope':'Reserve action control minimum height','before':'heightIn(min = 48.dp)','after':'heightIn(min = 49.dp)','reason':'The original typed checker reported 47.99994000000004dp against the required >=48dp lower bound in three independently named P2 states. The production minimum now has 1dp of margin above the lower bound so coordinate serialization near exactly 48 does not determine conformance. The public requirement is a lower bound, not an exact 48dp size.','supported_by':['P2/android/browse/reserve-height','P2/android/editing/reserve-height','P2/android/replaced/reserve-height'],'confirmation':'Compile-only passed. Final native geometry has not been captured.'},
  {'file':str(swift),'scope':'Shared option/action ButtonStyle','before':'PlainButtonStyle plus explicit disabled opacity','after':'WorkshopEnrollmentButtonStyle renders the explicit label palette, keeps the existing single explicit 0.62 disabled opacity, and adds only press opacity feedback. Button and .disabled remain the actual native control and native disabled gate.','reason':'The original manual review recorded very pale disabled option labels in P1 reserved. PlainButtonStyle adding a native disabled treatment to the explicit opacity is a plausible cause. An explicit custom ButtonStyle is intended to keep the caller-defined ink readable while retaining visibly disabled controls and selected traits.','supported_by':['P1/ios/reserved/disabled-readability-concern'],'confirmation':'This was a qualitative concern, not a confirmed exact color or contrast failure. Compile-only passed; visual improvement and runtime traits remain to be verified after the final source seal.'}
 ],
 'supported_by_original_findings':{'review':str(review),'review_sha256':sha(review),'finding_ids':['P2/android/browse/reserve-height','P2/android/editing/reserve-height','P2/android/replaced/reserve-height','P1/ios/reserved/disabled-readability-concern']},
 'plan_changes':[],'original_plans_and_support_unchanged':True,'original_review_artifacts_unchanged':True,'compile_checks':checks,
 'initial_source_sha256':start['initial_source_sha256'],'final_source_sha256':{str(p):sha(p) for p in [swift,kotlin]},
 'limits':[
  'No native observation, screenshot, preview, test execution, app launch, final capture, independent grade or heldout feedback was used during repair.',
  'Only compilation is validated. Neither original typed failures nor the qualitative concern is claimed resolved without a new source-bound capture.',
  'The Android measurement discrepancy may involve exported coordinate precision; its cause remains uncertain. No expected value, tolerance, comparator, fixture or action route was changed.',
  'The SwiftUI change is based on a qualitative readability concern and a style-layer hypothesis. It is not evidence of computed color or contrast compliance.',
  'All original plans/actions retain their independent design lock integrity and exact hashes. Original review P/F/U rows remain preserved.',
  'Unsupported iOS computed measurements, blocked callback behavior and prior inconsistent geometry remain unassessed in the original evidence.',
  'Public production API, catalog reconciliation, reservation payloads and callback dispatch logic are unchanged.',
  'Frozen tools, bridges, host files, common infrastructure, framework/deployment versions and public design were not edited.'
 ]
}
(out/'repair.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
sources={str(p):sha(p) for p in [swift,kotlin]}
plans={str(p):sha(p) for p in sorted((out/'plans').rglob('*')) if p.is_file()}
canonical=json.dumps(sources,sort_keys=True,separators=(',',':')).encode()
final={'phase':'final_source_and_plan_seal_before_final_capture','sealed_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'approved_design_lock_sha256':'c2548a601384046a016e98258728877982f30a4ed25be22455d9ec9ea4399bc1','production_source_sha256':sources,'production_source_fingerprint_sha256':hashlib.sha256(canonical).hexdigest(),'final_plan_hashes':plans,'original_plans_seal_sha256':sha(out/'plans-seal.json'),'plans_unchanged':True,'original_review_seal_sha256':sha(out/'review-seal.json'),'repair_record':str(out/'repair.json'),'repair_record_sha256':sha(out/'repair.json'),'repair_support':{str(p):sha(p) for p in [out/'repair-start.json',Path(__file__)]}}
(out/'final-seal.json').write_text(json.dumps(final,indent=2)+'\n')
print(json.dumps({'end_utc':end,'wall_seconds':record['wall_seconds'],'compile_exit_codes':[c['exit_code'] for c in checks],'final_source_fingerprint':final['production_source_fingerprint_sha256'],'plan_files_sealed':len(plans)},indent=2))
