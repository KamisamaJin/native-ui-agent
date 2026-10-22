from pathlib import Path
import collections,datetime,hashlib,json,time
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
workspace=base/'cache/unit-a891c8'
output=workspace/'agent-output/review'
corpus=base/'own-corpora/unit-a891c8/d0'
submission=base/'submissions/unit-a891c8'
started=json.loads((output/'phase-start.json').read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def evidence(path):return {'path':str(path),'sha256':digest(path)}
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
findings=[];summary=[];coverage=[];commands=[];failure_ids=[];dispositions=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  original_plan=submission/'initial-agent-output/plans'/case/platform/'plan.json'
  original_report=submission/'own-checks/d0'/case/platform/'report.json'
  observation=corpus/platform/case/'observation.json'
  plan=json.loads(original_plan.read_text());report=json.loads(original_report.read_text());obs=json.loads(observation.read_text())
  planned={a['id']:a for a in plan['assertions']}
  state_map={s['state_id']:s for s in obs['state_captures']}
  summary.append({'case':case,'platform':platform,'status':report['status'],'counts':report['counts'],'failed_assertion_ids':report['failed_assertion_ids'],'report':evidence(original_report),'observation':evidence(observation),'original_plan':evidence(original_plan),'expectation_provenance':report['expectation_provenance']})
  failure_ids += [{'case':case,'platform':platform,'id':i} for i in report['failed_assertion_ids']]
  dispositions.append({'case':case,'platform':platform,'original_matrix_contract':report['matrix_contract']})
  for a in report['assertions']:
   expected=planned[a['id']];state=a['state'];rid=expected['requirement_id']
   state_capture=state_map[state]
   indices=a.get('snapshot_indices') or state_capture['snapshot_indices'][:1]
   status=a['status'];origin='original_typed_native_check';reason=a['reason']
   if rid in ['content-wrapping','content-overlap']:
    indices=state_capture['snapshot_indices']
    origin='original_screenshot_review'
    if rid=='content-overlap':
     status='passed';reason='Reviewed every original overlapping state viewport, top through footer. Required text blocks, severity, disclosure/dossier and primary action occupy separate areas; no unintended overlap or occlusion was visible.'
    elif case=='P2' and platform=='android':
     status='unassessed';reason='All required text is present and characters remain readable without visible ellipsis or clipping. Qualitative line-break concern: the ferry label renders pressure-gau / ge drift, rather than using the available hyphen break; expanded dossier also renders Maintenance-he / ld. The brief prefers spaces/hyphens before character fallback. This is retained as a wrapping-quality concern, not asserted as a confirmed contradiction without a firmer native line-break assessment.'
    else:
     status='passed';reason='Reviewed every original overlapping state viewport, top through footer, against current disclosure/selection visibility and caller text. Title, subtitle, notice, six labels, required reasons, inline selected dossier when expanded, summary, primary label and footer remain readable; no required text missing, clipping or ellipsis was visible. At enlarged iOS text, overlong segments break across lines with characters preserved.'
   elif rid in ['component-canvas-color','notice-surface-color','primary-surface-color']:
    reason='Original typed check remains unassessed: no native pixel atom result was produced by the original run. Screenshots qualitatively show the intended theme and role surfaces, but visual resemblance does not establish the exact approved ARGB value or policy sampling support.'
   elif rid=='title-native-weight' and platform=='ios':
    reason='Original typed check remains unassessed: generic computed SwiftUI title weight is unavailable from public XCUI AX. Visual text weight is not substituted for native scalar600 evidence.'
   elif a['status']=='failed':
    reason='Original machine failure retained unchanged. '+reason
   images=[]
   for index in indices:
    path=corpus/platform/case/obs['snapshots'][index]['screenshot']
    if path not in images:images.append(path)
   findings.append({'case':case,'platform':platform,'state':state,'requirement_id':rid,'assertion_id':a['id'],'aspect':expected.get('property',expected['kind']),'expected':expected['expected'],'unit':expected['unit'],'status':status,'origin':origin,'original_typed_status':a['status'],'original_typed_reason':a['reason'],'reason':reason,'expectation_provenance':expected.get('expectation_provenance',[]),'snapshot_indices':indices,'evidence':[evidence(observation),evidence(original_report),evidence(original_plan)]+[evidence(p) for p in images],**({'machine_failure_id':a['id'],'failure_assessment':'unassessed_pending_product_vs_measurement_classification'} if a['status']=='failed' else {})})
  for state in plan['states']:
   sid=state['id'];s=state_map[sid]
   coverage.append({'case':case,'platform':platform,'state':sid,'original_plan_scope':state['coverage'],'complete':s['complete'],'top_reached':s.get('top_reached'),'bottom_reached':s.get('bottom_reached'),'stable_binding':s.get('stable_binding'),'max_gap':s.get('max_gap'),'binding':s.get('binding'),'snapshot_indices':s['snapshot_indices'],'visually_reviewed_full_sweep':sid in ['baseline','expanded','submitted'],'evidence':[evidence(observation)]})
  checkdir=submission/'own-checks/d0'/case/platform
  for path in [checkdir/'command.json',checkdir/'check.log',corpus/platform/(case+'-command.json')]:
   commands.append({'file':evidence(path),'record':json.loads(path.read_text()) if path.suffix=='.json' else path.read_text()})
write(output/'original-command-records.json',commands)
write(output/'original-cell-dispositions.json',dispositions)
source_checks=[]
for sealed in (submission/'d0/source').rglob('*'):
 if sealed.is_file():
  live=workspace/sealed.relative_to(submission/'d0/source')
  source_checks.append({'path':str(live),'sealed':str(sealed),'sealed_sha256':digest(sealed),'live_sha256':digest(live) if live.exists() else None,'identical':live.exists() and sealed.read_bytes()==live.read_bytes()})
plan_checks=[]
for sealed in (submission/'initial-agent-output/plans').rglob('*'):
 if sealed.is_file():
  live=workspace/'agent-output/plans'/sealed.relative_to(submission/'initial-agent-output/plans')
  plan_checks.append({'path':str(live),'sealed_sha256':digest(sealed),'live_sha256':digest(live),'identical':sealed.read_bytes()==live.read_bytes()})
write(output/'integrity.json',{'sources':source_checks,'plans':plan_checks,'all_source_identical':all(x['identical'] for x in source_checks),'all_plans_identical':all(x['identical'] for x in plan_checks)})
finished=time.time()
review={'version':1,'phase':'original_read_only_self_review','startedAtUnix':started['startedAtUnix'],'startedAtUtc':started['startedAtUtc'],'finishedAtUnix':finished,'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),'wallSeconds':finished-started['startedAtUnix'],'budgetSeconds':720,'status':'needs_review','approved_design_lock_sha256':'c21f3c012a188c7c39e8017dc92e8749b821a74aa3ad84d007732cfffa48e000','original_reports':summary,'original_machine_failure_ids':failure_ids,'machine_failure_assessment':'Original own typed reports contain zero failed assertions. No automatic failures were dropped, reclassified or overwritten. All original U statuses and reports remain preserved alongside manual additions.','original_typed_totals':dict(collections.Counter({k:sum(r['counts'].get(k,0) for r in summary) for k in ['passed','failed','unassessed']})),'review_findings_counts':dict(collections.Counter(x['status'] for x in findings)),'coverage':coverage,'contact_sheets':evidence(output/'contact-manifest.json'),'original_cell_dispositions':evidence(output/'original-cell-dispositions.json'),'original_command_records':evidence(output/'original-command-records.json'),'integrity':evidence(output/'integrity.json'),'findings':findings,'limits':['This is a review of sealed original captures only. No new SDK, app, observer, preview, screenshot or native check execution occurred. Source, bridge, actions, design and plans were not changed.','Exact color ARGB/policy sampling assertions remain unassessed; no offline sampling was substituted for absent original native pixel results.','iOS title-native-weight remains unassessed in all seven states per case.','Disabled choice observations are blocked_disabled, not successful callback stimuli. Their absence of callback is not promoted into an extra callback pass. Disabled native enablement is independently observed and typed checked.','Android dispatch is Compose semantic OnClick in an attached continuous session, not OS physical touch. iOS successful activation uses XCUI taps. No parent app navigation/lifecycle or physical hit-region claims.','Full-page visual wrapping/overlap review covers all98 original full-sweep viewport images across12 exact states. Native facts and allseven planned business checkpoints per case/platform were read. Other target states were not separately certified for full-page manual visual quality.','The P2 Android wrapping question remains U in baseline/expanded/submitted due to qualitative hyphen-break concerns; no visible characters were lost and no ellipsis or overlap was found.','Opening without selection, closing disclosure, moving an already-open dossier to another item, idempotent reselect, RTL, arbitrary new model data, all availability combinations and same-revision recomposition persistence are not exercised by the original public action route. Source declarations do not establish these runtime outcomes.','Reference vector font metrics are not a native pixel baseline; enlarged iOS and Android fonts have different valid native metrics. No font-size inference was made from reference screenshots.'],'commands_and_errors':{'new_contact_sheet_command':evidence(output/'contact-command.json'),'new_review_writer':'python3 agent-output/review/write-review.py','read_only_inspections':'Exact shell read/hash commands and view_image calls are preserved in this chat tool transcript. Their per-command timestamps were not separately recorded.','original_check_exit_codes':[r['record'].get('exitCode') for r in commands if isinstance(r['record'],dict) and 'planSHA256' in r['record']],'original_input_validation_errors':[],'new_failed_attempts':[]},'stop_state':'Review complete; stop until explicit root resume.'}
write(output/'review.json',review)
print(json.dumps({'finishedAtUtc':review['finishedAtUtc'],'wallSeconds':review['wallSeconds'],'originalTypedTotals':review['original_typed_totals'],'reviewFindings':review['review_findings_counts'],'sourcesIdentical':all(x['identical'] for x in source_checks),'plansIdentical':all(x['identical'] for x in plan_checks)},indent=2))
