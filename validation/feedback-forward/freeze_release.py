#!/usr/bin/env python3
"""Freeze only after neutral native and independent completion proof, before design."""
import hashlib,json,shutil,time
from pathlib import Path
import study as s
R=s.R
assert not(R/'design').exists(),'Business design must start after the tool barrier'
assert s.read(R/'benchmark-summary.json')['allEligible']
for folder in ['pass1','pass2','pass3','pass4']:
 root=R/'neutral-review'/folder;proof=s.read(root/'SEAL.json');files=proof.get('files',proof.get('files_sha256'))
 assert files
 for rel,h in files.items():
  path=(root/rel).resolve();assert path.is_relative_to(root.resolve())and s.sha(path)==h,rel
assert s.read(R/'neutral-targeted-v4/result.json')['status']=='verified_capture'
assert s.read(R/'neutral-targeted-v4/result.json')['scope']=='targeted'
assert 'Ran 132 tests'in(R/'operators/unit-all-attempt-11.log').read_text()and(R/'operators/unit-all-attempt-11.log').read_text().rstrip().endswith('OK')
assert(R/'operators/skill-validation-final.log').read_text().strip()=='Skill is valid!'
core=R.parents[1]/'native-ui-agent';files={str(p.relative_to(core)):s.sha(p)for p in core.rglob('*')if p.is_file()and'__pycache__'not in p.parts}
assert files==s.read(R/'operators/candidate-attempt-4.json')['files']
shutil.copytree(core,R/'candidate-v9',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
s.save(R/'candidate-v9-freeze.json',{'frozenAtUnix':time.time(),'files':files,'scope':'Release frozen after paired neutral native proof and independent minimum-context forward validation; before all new product designs/initial sources.'})
operators=['freeze_release.py','study.py','feedback.py','close_session.py','final_self_check.py','evaluation.py','claim_analysis.py','metrics.py','test_metrics.py','delivery_metrics.py','test_delivery_metrics.py','final_outcome_metrics.py','test_final_outcome_metrics.py','FINAL-OUTCOME-METHOD.md','compile_only.py','setup_workspace.py','prepare_arm.py','approve_design.py','prepare_design_request.py','prepare_design_review_request.py','prepare_builder_request.py','prepare_repair_request.py','prepare_quality_request.py','prepare_claim_request.py','gates/config.json','METHODS.md','ENDPOINT-CLARIFICATION.md','ENDPOINT-CLARIFICATION.json','SELF-CHECK-ENDPOINT.md','SELF-CHECK-ENDPOINT.json','PROTOCOL-NOTES.md']
s.save(R/'METHODS-RELEASE.json',{'frozenAtUnix':time.time(),'files':{v:s.sha(R/v)for v in operators},'repository_files':{'tools/native_environment.py':s.sha(R.parents[1]/'tools/native_environment.py')},'scope':'Common data/evaluator/metric/budget/endpoint/guard methods and minimum-context templates before new business design; first engineering revision retained byte-exact.'})
s.cohort('tools',{'release':[R/'PREREGISTRATION.md',R/'PREREGISTRATION.json',R/'baseline-v8-freeze.json',R/'baseline-v8',R/'candidate-v9-freeze.json',R/'candidate-v9',R/'METHODS-RELEASE.json',R/'METHODS-PRE-DESIGN.json',R/'operators/methods-first-revision',R/'benchmark-summary.json',R/'operators/benchmark-requests.json',R/'neutral',R/'neutral-captures',R/'neutral-targeted',R/'neutral-targeted-v4',R/'neutral-review']})
print('Complete neutral/release barrier sealed before business design')
