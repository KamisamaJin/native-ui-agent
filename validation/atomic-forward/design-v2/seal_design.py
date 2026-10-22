#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parent
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write_once(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
 p.chmod(0o444)
def inventory(b,exclude):return {str(p.relative_to(b)):sha(p) for p in sorted(b.rglob('*')) if p.is_file() and str(p.relative_to(b)) not in exclude and '__pycache__' not in p.parts}
v=load(R/'validation-summary.json');integ=load(R/'delivery-integrity.json');auth=load(R/'authored-at.json');end=now();start='2026-10-22T01:37:31Z'
write_once(R/'FINAL-PHASES.json',{'actual_design_started_at':start,'actual_initial_revised_proposals_authored_at':auth['actual_all_design_authored_at'],'actual_final_design_finished_at':end,'actual_validation_started_at':v['actual_validation_started_at'],'actual_validation_finished_at':v['actual_validation_finished_at'],'final_delivery_integrity_checked_at':integ['checked_at'],'v1_preserved_sha256':integ['v1_preserved_sha256'],'native_sdk_invocations':0,'design_quality_approval':False,'process_scope_record':'REVISION-RECORD.json'})
for t in auth['tasks']:
 tid=t['id'];b=R/tid
 write_once(b/'seal.json',{'version':1,'proposal':'design-v2','task':tid,'domain':t['domain'],'interaction_structure':t['structure'],'status':'sealed_preimplementation_revision_for_new_independent_design_review','actual_design_started_at':start,'actual_design_finished_at':end,'actual_validation_started_at':v['actual_validation_started_at'],'actual_validation_finished_at':v['actual_validation_finished_at'],'integrity_checked_at':integ['checked_at'],'sealed_at':now(),'selected_per_case':{'states':7,'rules':14,'cells_per_platform':98,'required':81,'not_applicable':17},'public_approval':load(b/'public'/'approval.json'),'private_approval':load(b/'private'/'approval.json'),'v1_preserved_sha256':integ['v1_preserved_sha256'],'native_sdk_invocations':0,'design_quality_approval':False,'files_sha256':inventory(b,{'seal.json'}),'immutability':'Exclusive write and0444; revisions require new directory.'})
write_once(R/'seal.json',{'version':1,'cohort':'atomic-forward-independent-design-v2','status':'sealed_preimplementation_revision_for_new_independent_review','actual_design_started_at':start,'actual_design_finished_at':end,'actual_validation_started_at':v['actual_validation_started_at'],'actual_validation_finished_at':v['actual_validation_finished_at'],'integrity_checked_at':integ['checked_at'],'sealed_at':now(),'v1_preserved_sha256':integ['v1_preserved_sha256'],'v1_files_verified':integ['v1_sealed_files_verified'],'frozen_skill_files_verified':54,'case_platform_compile_catalog_runs':18,'native_sdk_invocations':0,'design_quality_approval':False,'task_seals':{t:sha(R/t/'seal.json') for t in ['T1','T2','T3']},'private_handling':'Only T*/public minus compiled builder-facing; H1/internal/attempt material private.','files_sha256':inventory(R,{'seal.json'}),'immutability':'Exclusive write and0444. Excludes its own digest by definition; parent records exact hash. No post-seal additions/edits.'})
print(json.dumps({'cohort_seal_sha256':sha(R/'seal.json'),'task_seals':{t:sha(R/t/'seal.json') for t in ['T1','T2','T3']},'actual_design_finished_at':end,'files':len(load(R/'seal.json')['files_sha256'])},indent=2))
