#!/usr/bin/env python3
"""Closed-study failure pointers; strict outcomes remain in original reports."""
import json
from pathlib import Path
R=Path(__file__).resolve().parent
entries=[
 {'phase':'shared study integration','kind':'pre_sdk_environment_path_failure','evidence':['OPERATIONS-AMENDMENT.json','corpora/initial/public','gates-v1'],'reason':'Both wrappers failed before SDK. Shared exact-approved environment alias corrected the legacy path assumption; original failed files and gate registry retained, no product/expectation/tool changes.'},
 {'phase':'independent design','kind':'preimplementation_rejected_designs','evidence':['design-v1/SEAL.json','design-v2/SEAL.json','design-review/REVIEW.md','design-review-v2/REVIEW.md','design-review-v3/REVIEW.md'],'reason':'Ordering/exclusion, alignment/timing/method responsibility and ROI safety clarified before first code. Old shared-substring exclusion ambiguity fixed without data/style/action changes.'},
 {'phase':'blind','kind':'conditional_false_alarms_and_missing_route_validity','evidence':['adjudication/causes.json','quality-panels/panel-one/alarm-judgments.json','quality-panels/panel-two/alarm-judgments.json'],'reason':'Four unique original F are conditional expectations after native activation was not dispatched. Raw F/U preserved; accessibility causes separate from unproven business behavior.'},
 {'phase':'blind','kind':'final_required_unknowns','evidence':['results.json','adjudication/causes.json','self-review'],'reason':'Each final version retains13 native geometry U and6 source-only U across two scopes. Oversized controls lack a fully visible measurement frame; three method/bridge propositions exceed declared source evidence. No complete delivery or successful cost inferred.'},
 {'phase':'calibration','kind':'native_transport_failure','evidence':['operators/ax-runtime-value-limit.json','evidence/ax-run-1'],'reason':'Original V1 native AX value was truncated to512 bytes; all612 runtime values invalid JSON. V2 compact transport was independently preflighted before new SDK run.'},
 {'phase':'neutral','kind':'retained_independent_oracle_difference','evidence':['probe-review/findings-006.md','probe-review/replay-006/results.json'],'reason':'Final independent ten-case synthetic replay9/10. Two different samples both strictly fail equality; oracle asks U. No threshold/status rewrite to fit oracle.'},
 {'phase':'calibration','kind':'limited_empirical_support','evidence':['calibration-review/REVIEW.md','calibration-review/after-check/REPORT.md','calibration/profile-final.json'],'reason':'All actual residuals zero; floor factor1 is not a verified positive residual law. Ordinary external AX target scope unproved and excluded. Caller metadata/record membership is not runtime authenticity.'},
 {'phase':'benchmark','kind':'excluded_development_attempts','evidence':['operators/benchmark-d0.log','operators/benchmark-results-attempt-1-empty.json','RELEASE.json'],'reason':'Preflight canonical-digest integration error and pre-release pilots, release serialization path error, initial analysis legacy-schema mismatch retained; excluded from sealed primary timing.'}
]
for folder in ['corpora','feedback','self-review','quality-evaluation']:
 for path in sorted((R/folder).rglob('*.json')):
  try:value=json.loads(path.read_text())
  except (ValueError,OSError):continue
  if isinstance(value,dict)and(value.get('status')in {'invalid_or_incomplete_capture','wrapper_failure','not_accepted','blocked_repeated_unchanged_evidence'}or value.get('error')):
   entries.append({'phase':folder,'kind':'original_failure_or_block','evidence':[str(path.relative_to(R))],'status':value.get('status'),'reason':value.get('error')or value.get('reason')or value.get('scope_limit')})
print(json.dumps({'scope':'Pointers only; raw F/U and independent attribution are never overridden. Negative controls and old failed attempts remain in their sealed directories.','entries':entries},indent=2))
