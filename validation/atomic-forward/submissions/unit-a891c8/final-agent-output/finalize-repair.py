from pathlib import Path
import collections,datetime,hashlib,json,time
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
workspace=base/'cache/unit-a891c8'
output=workspace/'agent-output/repair'
submission=base/'submissions/unit-a891c8'
started=json.loads((output/'phase-start.json').read_text())
review_path=submission/'original-review/review.json'
review=json.loads(review_path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def evidence(path):return {'path':str(path),'sha256':sha(path)}
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
source_checks=[]
for sealed in (submission/'d0/source').rglob('*'):
 if sealed.is_file():
  live=workspace/sealed.relative_to(submission/'d0/source')
  source_checks.append({'path':str(live),'sealed_path':str(sealed),'sealed_sha256':sha(sealed),'current_sha256':sha(live) if live.exists() else None,'identical':live.exists() and sealed.read_bytes()==live.read_bytes()})
plan_checks=[]
for sealed in (submission/'initial-agent-output/plans').rglob('*'):
 if sealed.is_file():
  live=workspace/'agent-output/plans'/sealed.relative_to(submission/'initial-agent-output/plans')
  plan_checks.append({'path':str(live),'sealed_path':str(sealed),'sealed_sha256':sha(sealed),'current_sha256':sha(live),'identical':sealed.read_bytes()==live.read_bytes()})
write(output/'integrity.json',{'checkedAtUnix':time.time(),'source_files':source_checks,'plan_and_action_files':plan_checks,'all_sources_identical':all(x['identical'] for x in source_checks),'all_plans_actions_identical':all(x['identical'] for x in plan_checks)})
assert all(x['identical'] for x in source_checks)
assert all(x['identical'] for x in plan_checks)
confirmed=[f for f in review['findings'] if f['status']=='failed']
assert not confirmed
unresolved=[]
for key,reason in [
 ('component-canvas-color','Original exact native-pixel color/support assessment is absent. No original confirmed product contradiction supports a production change.'),
 ('notice-surface-color','Original exact native-pixel color/support assessment is absent. No original confirmed product contradiction supports a production change.'),
 ('primary-surface-color','Original exact native-pixel color/support assessment is absent. No original confirmed product contradiction supports a production change.'),
 ('title-native-weight','Generic SwiftUI computed title weight is unavailable in public XCUI AX; this is an observation limitation, not an established style defect.'),
 ('content-wrapping','Original P2 Android review records qualitative hyphen-priority concerns while preserving every visible character and finding no clipping or ellipsis. It remains unassessed. A line-breaking-policy change is not supported as a confirmed repair from this evidence and cannot receive a second feedback cycle here.')]:
 matches=[f for f in review['findings'] if f['status']=='unassessed' and f['requirement_id']==key]
 if matches:unresolved.append({'requirement_id':key,'count':len(matches),'original_finding_ids':[{'case':f['case'],'platform':f['platform'],'state':f['state'],'assertion_id':f['assertion_id']} for f in matches],'reason':reason,'evidence':[evidence(review_path)]})
commands=[{'kind':'read_only_inspection','description':'Read assigned repair prompt, immutable original review, approved public BRIEF and production Compose text code. Exact read commands and timestamps are preserved in the chat tool transcript.','outcome':'completed','source_mutation':False},{'kind':'record_and_integrity','argv':['python3',str(output/'finalize-repair.py')],'startedAtUnix':time.time(),'outcome':'completed','source_mutation':False}]
write(output/'commands.json',commands)
log='No production code was changed. No compile-only was needed because all production sources match the originally compiled and sealed D0 sources. No render, observer, preview, screenshot, App launch or native check was executed. All original findings, expectations and unsupported checks remain unchanged.\n'
(output/'decision.log').write_text(log)
finished=time.time()
record={'version':1,'phase':'one_repair','status':'no_supported_production_repair','startedAtUnix':started['startedAtUnix'],'startedAtUtc':started['startedAtUtc'],'finishedAtUnix':finished,'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),'wallSeconds':finished-started['startedAtUnix'],'budgetSeconds':900,'changed_files':[],'original_findings_addressed':[],'decision':'The immutable original review contains zero confirmed failed findings and zero original typed machine failures. Retain source without cosmetic churn; no supported production repair is established.','original_review':evidence(review_path),'original_review_counts':review['review_findings_counts'],'original_typed_totals':review['original_typed_totals'],'original_machine_failure_ids':review['original_machine_failure_ids'],'unresolved_and_why':unresolved,'additional_limits':['The original public route does not exercise no-selection guidance opening, closing disclosure, moving an open dossier, idempotent reselect, RTL, arbitrary data/availability combinations or same-revision persistence. These runtime gaps remain unresolved; no source declaration is promoted into runtime acceptance.','All exact expected values, units, plans/actions, host, bridge, design and tool settings were left unchanged.','Original compile-only succeeded for both unchanged source files. No new compile was run because no production edit was made.'],'commands':str(output/'commands.json'),'logs':[str(output/'decision.log')],'integrity':evidence(output/'integrity.json'),'failures':[],'production_source_hashes':[{'path':x['path'],'sha256':x['current_sha256']} for x in source_checks if x['path'].endswith(('RiverSensorTriageBoard.swift','RiverSensorTriageBoard.kt'))],'acceptance_claim':'None. Final sources require root cohort seal and separately authorized final collection.','stop_state':'Repair record complete; no further repair or capture authorized.'}
write(output/'repair.json',record)
artifacts=[output/'phase-start.json',output/'repair.json',output/'integrity.json',output/'commands.json',output/'decision.log',output/'finalize-repair.py']
write(output/'repair-seal.json',{'sealedAtUnix':time.time(),'files':[evidence(p) for p in artifacts],'source_files':[{'path':x['path'],'sha256':x['current_sha256']} for x in source_checks],'plans_and_actions':[{'path':x['path'],'sha256':x['current_sha256']} for x in plan_checks]})
print(json.dumps({'finishedAtUtc':record['finishedAtUtc'],'wallSeconds':record['wallSeconds'],'status':record['status'],'changed_files':record['changed_files'],'unresolved':sum(x['count'] for x in unresolved),'all_sources_identical':True,'all_plans_actions_identical':True},indent=2))
