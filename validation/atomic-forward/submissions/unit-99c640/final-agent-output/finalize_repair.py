from pathlib import Path
import json,time,datetime,hashlib,shutil
O=Path(__file__).resolve().parent;W=O.parents[1]
S=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/submissions/unit-99c640')
D=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
initial=json.loads((W/'agent-output/implementation.json').read_text())
reviewpath=S/'original-review/review.json';review=json.loads(reviewpath.read_text())
failed=[f for f in review['findings'] if f['status']=='failed']
planseal=json.loads((W/'agent-output/plans-seal.json').read_text())
planchecks={k:{'original_sha256':v,'actual_sha256':sha(W/k),'unchanged':sha(W/k)==v} for k,v in planseal['files'].items()}
source_records=[];changed=[]
for rel,original in initial['source_sha256'].items():
 p=W/rel;actual=sha(p)
 dest=O/'final-sources'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 source_records.append({'path':str(p),'original_sha256':original,'final_sha256':actual,'changed':actual!=original,'immutable_copy':str(dest),'immutable_copy_sha256':sha(dest)})
 if actual!=original:changed.append(rel)
start=json.loads((O/'phase-start.json').read_text());finish=time.time()
cmd=json.loads((O/'compile-ios-01-command.json').read_text());build=json.loads((O/'compile-ios-01-record.json').read_text())
record={
 'version':1,'phase':'one_authorized_repair','status':'source_repaired_compile_only_passed_pending_final_acquisition',
 'startedAtUnix':start['startedAtUnix'],'startedAtUTC':start['startedAtUTC'],'finishedAtUnix':finish,'finishedAtUTC':datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),'elapsedSeconds':finish-start['startedAtUnix'],'wallBudgetSeconds':900,
 'changed_files':changed,
 'original_findings_addressed':[{
  'case':'P1','platform':'ios','requirement_id':'responsive-grid','aspect':'grid_column_count','expected':2,'unit':'columns','affected_states':['baseline','selected','expanded','blocked','replaced','reselected','submitted'],
  'original_review':{'path':str(reviewpath),'sha256':sha(reviewpath)},
  'original_observation':'Wide ordinary-text P1 rendered full-inner-width cards vertically in all seven reviewed states; expected two columns.',
  'source_change':'Replace the background GeometryReader preference propagation with direct onAppear and onChange updates from proxy.size.width; remove the unused preference key.',
  'cause_hypothesis':'Original geometry-backed width state failed to select the wide branch. The original captures establish the one-column result, not the internal preference/state cause. Direct geometry lifecycle updates remove that propagation dependency while retaining the 320pt and sizeCategory<=large conditions.',
  'repair_scope':'Only width measurement delivery changed; eager grid, thresholds, theme, typography, semantics, model state and callbacks retain their original implementation.',
  'verification':'The allowed compile-only helper rebuilt the production SwiftUI package and public bridge successfully. No final runtime result is claimed.'
 }],
 'unresolved_and_why':[
  {'requirement_id':'responsive-grid','status':'pending_final_acquisition','reason':'One permitted repair is implemented and compiles; no post-repair capture or second feedback cycle is authorized in this phase.'},
  {'requirement_id':'title-native-weight','platform':'ios','status':'unassessed','reason':'Public accessibility does not expose computed SwiftUI native weight. Original fourteen U cells remain original; this is not a supported product repair.'},
  {'requirement_id':'disabled-activation-callback','status':'unassessed','reason':'Original disabled actions were blocked with no successful dispatch. No callback absence pass can be inferred; native disabled semantics were separately observed.'}
 ],
 'commands':[cmd],
 'logs':[{'path':str(O/n),'sha256':sha(O/n)} for n in ['compile-ios-01-wrapper.log','compile-ios-01-build.log','compile-ios-01-record.json','compile-ios-01-command.json','edit-record.json','production-change.diff']],
 'compile_only':build,
 'source_records':source_records,
 'protected_original_plan_action_script_checks':planchecks,
 'original_compiler_unchanged':sha(Path(initial['compiler']['path']))==initial['compiler']['sha256'],
 'public_bridge_sha256':sha(D/'Bridge.swift'),
 'public_bridge_matches_initial_build':sha(D/'Bridge.swift')==json.loads((W/'agent-output/logs/ios-01-record.json').read_text())['bridgeSHA256'],
 'command_notes':[
  'First action read the assigned repair specification; phase start recorded immediately afterward using Python UTC/Unix time.',
  'Read current production SwiftUI source and own immutable original review only. Original design requirements and assigned frozen Skill were already read in this task.',
  'Applied one scripted exact replacement in the production Swift file; edit-record.json retains before/after hashes and production-change.diff retains the complete patch.',
  'Ran only the specified compile-only helper with a fresh own cache output; no failed compile attempts occurred.',
  'Read-only comparison against own sealed D0 source and original plans confirmed the intended source delta and unchanged original plans/scripts.'
 ],
 'limits':[
  'No SDK rendering, observer execution, preview, app launch, screenshot, new feedback or second repair cycle was performed.',
  'Android production source is byte-identical to initial D0; no Android repair or repeat compile was needed.',
  'No original plan/action/expected value, tolerance, design, bridge, tool, host, build setting or framework version was edited.',
  'No private/hidden/evaluation/common corpus, other candidate or other Skill version was inspected; no agents, commits or pushes.',
  'Stop after this immutable repair record; root will seal all six final sources before final acquisition. No further repair is authorized.'
 ],
 'errors':[]
}
(O/'repair.json').write_text(json.dumps(record,indent=2)+'\n')
artifacts=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='repair-seal.json')
(O/'repair-seal.json').write_text(json.dumps({'version':1,'sealedAtUnix':time.time(),'files':{str(p.relative_to(W)):sha(p) for p in artifacts}},indent=2)+'\n')
print(json.dumps({'elapsedSeconds':record['elapsedSeconds'],'changed_files':changed,'all_original_plans_unchanged':all(x['unchanged'] for x in planchecks.values()),'bridge_unchanged':record['public_bridge_matches_initial_build'],'status':record['status'],'repair':str(O/'repair.json')},indent=2))
