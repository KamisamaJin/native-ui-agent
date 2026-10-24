#!/usr/bin/env python3
"""Close the new source-only adapter before initial component authoring."""
import time
import study as s
R=s.R
s.tool_verify()
for folder in ['source-neutral-forward','source-neutral-cli-check','source-neutral-minimum-api']:s.verify_dir(R/folder)
assert(R/'operators/source-audit-controls-final.log').read_text().rstrip().endswith('OK')
stock=s.read(R/'operators/stock-production.json')['files']
for name in ['builder-T1','builder-T2']+list(s.read(R/'private/assignment-draft.json')['units']):assert s.fingerprint(R/'cache'/name)==stock
study_files=['PREIMPLEMENTATION-AMENDMENT.md','PREIMPLEMENTATION-AMENDMENT.json','SOURCE-AUDIT.md','test_implementation_audit.py','approve_expanded_design.py','source_check.py','complete_self_check.py','REPAIR-SOURCE-EXTENSION.txt','source_evaluation.py','QUALITY-SOURCE-EXTENSION.txt','close_quality.py','shared_amendment.py','freeze_amendment.py','close_initial.py','collect_case_set.py','check_minimum_api.py','BUILD-API-EXTENSION.txt']
s.save(R/'PREIMPLEMENTATION-METHODS.json',{'frozenAtUnix':time.time(),'study_files':{v:s.sha(R/v)for v in study_files},'repository_files':{'tools/implementation_audit.py':s.sha(s.REPO/'tools/implementation_audit.py')},'scope':'Shared preimplementation-only source audit and explicit state/transport supplement. Runtime tool/evaluator/metric freeze remains unchanged; no product source or native business feedback exists.'})
print('Shared source/transport supplement frozen before initial product implementation')
