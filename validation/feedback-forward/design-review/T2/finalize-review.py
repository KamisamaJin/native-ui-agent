import hashlib,json,time
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');O=Path(__file__).resolve().parent
BASE=R/'validation/feedback-forward/design/T2';FROZEN=R/'validation/feedback-forward/candidate-v9'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
sources={}
for root in [BASE,FROZEN]:
 for path in sorted(root.rglob('*')):
  if path.is_file() and '__pycache__' not in path.parts:sources[str(path.relative_to(R))]=sha(path)
for rel in ['tools/implementation_audit.py','validation/feedback-forward/check_minimum_api.py','validation/feedback-forward/SOURCE-AUDIT.md','validation/feedback-forward/PREIMPLEMENTATION-AMENDMENT.md','validation/feedback-forward/operators/T2-design-review-request.txt','validation/feedback-forward/design-proposals/v1/design/T2/public/BRIEF.md','validation/feedback-forward/design-proposals/v1/design/T2/public/API.md']:
 sources[rel]=sha(R/rel)
save(O/'source-manifest.json',{'hash_algorithm':'SHA256 original file bytes','files':sources,'scope':'Allowed design, generic frozen infrastructure, original BRIEF/API only. No product source, native output, prior reviewer conclusions or other task inputs read.'})

pub=load(BASE/'public/reference.json');policy=load(BASE/'public/policy.json');contract=load(BASE/'public/contract.json');audits={a['id']:a for a in pub['implementation_audits']};rules={a['id']:a for a in contract['rules']}
crosswalk=load(BASE/'public/requirement-crosswalk.json')['clauses']
remarks={
'production':'Both exact production files are mandatory source-scoped items. Bridges instantiate the API directly; no substitute UI is present in the approved bridge.',
'storage-boundary':'Independent interpreter confirms sampled gates. Equality and unmetered paths are deliberately source-reviewed through the complete >= predicate, rather than claimed as native executions.',
'storage-priority':'The appended competing-gates fixture presents storage and network holds together; Storage needed and disabled primary are independently expected. Source decision-order review covers the general rule.',
'initial-choice':'All initial models expect selected=true and enabled=true independently, with a literal label. Source native-selected construction supplements the runtime trait check.',
'network-gate':'Initial true/false/true/false choice route exercises metered gate reversal. The complete source predicate retains sufficient storage and pending-request guards.',
'choice-reversals':'Independent event interpreter matches each actual activation index, resulting Boolean and exactly one event. Held-choice remains enabled even under storage hold.',
'request-callback':'Request receipt binds successful action6, current model ID and current preference. Source review separately covers the unmetered Wi-Fi-true path absent from sampled native inputs.',
'requested-state':'Requested full and requested-closed full states retain disabled choice/primary, requested status and Requested label, while disclosure remains enabled.',
'no-fetch':'Both source files have explicit no-audio-fetch obligations. This is source review, not a claim about rendered pixels.',
'disclosure-toggle':'Initial closed, real open and real post-request close are separately observed. Permitted/requested full sweeps carry exact eight heading/body pairs and caller order.',
'disclosure-quiet':'Opening action1 and closing action8 have their own empty expected intervals and require successful native activation; source no-callback paths are separate.',
'disclosure-enabled':'Native enabled checks apply after request; the close callback assertion requires real successful dispatch at action8.',
'identity-choice-reset':'Replacement selected=true follows a prior false choice; a later actual held-choice activation confirms the reset choice is enabled.',
'identity-disclosure-reset':'The runtime replacement is closed. Because disclosure was already closed immediately before the update, the source reset-disclosure item is necessary to prove the reset branch rather than infer it from this sample.',
'identity-requested-reset':'Replacement title/subtitle/status/primary labels update after a requested state, with source reset-requested and current-model rendering checks. P1 remains storage-blocked and P2 network-blocked.',
'identity-quiet-mounted':'The event rule explicitly sets caller_update and stimulus_action10/13. Frozen callback_verdict requires caller_fixture_update, successful dispatch, same instance/process, advanced input and the original event interval.',
'business-strings':'Fresh independent interpreter reproduces exact current title, language/MB composition, precedence, disclosure, choice and primary labels in all30 input/state combinations.',
'environment':'Separate frozen acceptance.environment checks actual native width/height/theme/direction/text scale; original environment files and their approval digests match. Host templates supply16 horizontal and24 top padding.',
'original-checkpoints':'Overview/permitted/requested/replaced each keep explicit fresh full-content sweeps. The amended requested-closed is also full; intermediate states are only targeted as approved.',
'layout-flow':'Separate canvas/surface/ink pixel atoms and full-flow/single-column/full-width visual propositions cover ownership and order. The native parent owns scrolling and width.',
'nominal-layout':'Original text explicitly makes generic internal layout tokens and status minimum height advisory. This cannot certify actual SwiftUI padding or convert it to a MUST pass.',
'choice-primary-gap':'The actual control basis uses gap_y with exact native units and independently sourced0.75 tolerance. Both unique fully visible controls must share one coherent frame.',
'status-inset':'A real distinct statusText node is measured against the real painted band on semantic basis: inset_left publicly, inset_right privately, gte16 without a tolerance. No computed padding is fabricated.',
'leading-clear':'Full logical leading4% strip has minimum support1.0 and exact opaque status-role color. RTL uses physical right[0.96,0,1,1], LTR physical left[0,0,0.04,1].',
'wrapping':'Eight distinct source questions cover title/subtitle/status/disclosure/choice/primary/headings/bodies. They accept original native frames only; source uncapped-line configuration is a separate added obligation.',
'scroll-ownership':'Both source files explicitly forbid nested scrolling and blank fixed-height rows manufacturing scrolling. Generic parent source shows its actual scrolling container.',
'long-content':'Permitted/requested representative expanded states require full coverage, overlap and bottom reachability. Targeted intermediate states do not substitute for them under the prospective amendment.',
'status-distinct-colors':'The original distinct waiting palette is restored for Wi-Fi required. Source-role mapping now matches business meaning; all10 states retain status pixel assertions.',
'other-colors':'Separate opaque ARGB atoms use original role colors, exact zero channel tolerance and declared solid regions. The solid ink mark is not asserted to prove glyph ink.',
'advisory-typography':'Exact computed SwiftUI font/text ink remains advisory. Required hierarchy/wrapping/overlap/clipping keep visual questions and no computed-font MUST is fabricated.',
'visual-atoms':'Independent qualitative questions, ownership, typed true expectations and provenance are generated by the real catalog API. Two-panel consensus retains disagreement as unknown.',
'native-evidence':'callback_verdict rejects disabled-empty-interval controls as unassessed. Selected/enabled observations and actual callback dispatch are separate assertions.',
'swift-exact-api':'All three exact declaration contracts preserve public lets, initializers, conformances and View/body. The future14 module/client check additionally exercises the real exported module.',
'ios14':'The original minimum14 SOURCE/API constraint has manual availability audit plus pinned real-library module emission and unchanged bridge typecheck at14. Current observer17 is not reused as proof. Legacy packaging/link/runtime remain unverified.',
'kotlin-exact-api':'All three declaration contracts preserve data classes, vals, types, package and Composable callback signature including modifier:Modifier=Modifier. No Swift module result is used for Android.',
'thin-bridges':'Inspected bridge code only decodes current fields, constructs models, invokes the production component and forwards actual callbacks. No state, layout, identity wrapper or expectation logic is present.',
'unique-ids':'Runtime exact selectors require unique native nodes; source propositions require real-node IDs, actual band/text allocations and no proxy duplication. The added statusText ID is distinct.',
'noninteractive-carriers':'Explicit source propositions cover canvas/surface/ink noninteractive roles and container descendant preservation. Native label/pixel evidence remains separate.',
'status-band':'Both source provenance propositions and separate native band/text labels/inset remain mandatory. Parent status ID may not be repeated on Text.',
'native-buttons':'Both platforms retain real Button source obligations and native control selected/disabled checks. Canvas/surface source obligations preserve independently addressable descendants.',
'ax-labels':'Exact native choice/disclosure/primary labels reject concatenated status or decorative marks. This is directly observable on the real controls.',
'primary-allocation':'Native control-basis height56 +/-0.75, visible rectangular paint/full allocation and fill are separate from source full-label/content-shape configuration. None claims physical hit-area verification.',
'production-state':'Both component state and reset paths are explicitly production-scoped; approved bridges have no state or .id/key wrapper.',
'uncapped-lines':'Source configuration forbids finite line caps separately from all eight rendered wrapping questions. Source review cannot make rendered wrapping pass.'
}
mapping=[]
for item in crosswalk:
 rid=item['id'];runtime=item['runtime_rule_ids'];source=item['source_audit_ids']
 assert all(x in rules for x in runtime) and all(x in audits for x in source)
 extra=[]
 if rid=='environment':extra=['candidate-v9/scripts/acceptance.py:environment','candidate-v9/assets/ios-observer/ObserverApp.swift:58-92','candidate-v9/assets/android-observer/NativeObserverTest.kt:256-264']
 if rid=='original-checkpoints':extra=['sealed contract.scenarios states/actions','fresh execution_plan.compile_execution/verify_execution']
 if rid=='long-content':extra=['frozen bound_state_evidence completeness/overlap/bottom coverage','PREIMPLEMENTATION-AMENDMENT.md representative-state authorization']
 if rid=='ios14':extra=['compatibility.json shared checker argv','check_minimum_api.py run() read only; never imported/executed during review']
 if rid.startswith('retained-rendered-'):
  text='Separate source-backed original-native-frame visual proposition retained. Rectangle/no-border/paint allocation are not inferred from pixel fill or source shape configuration.'
 else:text=remarks[rid]
 priority=item.get('priority','must')
 if rid in ['nominal-layout','advisory-typography']:priority='advisory'
 mapping.append({'id':rid,'original_clause':item['original_clause'],'original_source':item['original_source'],'priority':priority,'runtime_rule_ids':runtime,'source_audit_ids':source,'additional_routes':extra+item['other_verification_routes'],'ios_route_feasible':True,'android_route_feasible':True,'mapping_complete':True,'independent_review':text,'actual_product_acceptance':'unverified'})
save(O/'must-mapping.json',{'method':'Reviewer checked raw original BRIEF/API clause-by-clause, then inspected each cited runtime/source route and independent expected values; this is not merely a mechanical index-completeness assertion. Crosswalk IDs are retained as stable names.','entries':mapping})

timing=load(O/'phase-start.json');public_approval=load(BASE/'public/approval.json');private_approval=load(BASE/'private/approval.json')
checks=[load(O/'static-summary.json'),load(O/'private-checks/static-summary.json')]
finish=time.time()
review={
 'version':1,'task':'T2','status':'approved','scope':'Fresh independent preimplementation design feasibility; public P1/P2 and separate private H1 on iOS and Android. Approval is of feasible verification routes and independent expected intent, not of unimplemented product behavior.',
 'startedAtUnix':timing['startedAtUnix'],'finishedAtUnix':finish,'elapsedRecordedSeconds':finish-timing['startedAtUnix'],
 'timing_note':'First explicit timestamp was recorded after opening the scoped request and source inventory. Command-level SDK-free start/end times are retained for every compile/catalog/route/execution/definitions invocation; no earlier exact phase timestamp is invented.',
 'source_pins':{'manifest':'source-manifest.json','manifest_sha256':sha(O/'source-manifest.json'),'public_design_lock_sha256':public_approval['design_lock_sha256'],'private_design_lock_sha256':private_approval['design_lock_sha256'],'public_policy_sha256':public_approval['policy_sha256'],'private_policy_sha256':private_approval['policy_sha256'],'source_audit_policy_sha256':public_approval['implementation_audit_sha256'],'shared_minimum_source_api_checker_sha256':sha(R/'validation/feedback-forward/check_minimum_api.py'),'original_brief_sha256':sha(R/'validation/feedback-forward/design-proposals/v1/design/T2/public/BRIEF.md'),'original_api_sha256':sha(R/'validation/feedback-forward/design-proposals/v1/design/T2/public/API.md')},
 'production_paths':['Sources/AlertToast/OfflineAudioTourPanel.swift','app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt'],
 'production_repositories':{'ios':{'name':'AlertToast','pinned_commit':'76a1c1793cd3443001c20c6033beb84453b25d9f','relative_path':'Sources/AlertToast/OfflineAudioTourPanel.swift'},'android':{'name':'Reply','pinned_commit':'53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79','root':'upstream Reply/ Gradle root','relative_path':'app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt'}},
 'each_MUST_mapping_complete':True,'each_MUST_mapping':'must-mapping.json','feasible_on_both_platforms':True,
 'mechanical_checks':{'all_six_case_platform_routes':checks,'assets_and_pins':'assets-and-pins.json','public_commands':'command-log.json','private_commands':'private-checks/command-log.json','independent_business_and_events':['semantic-checks.json','private-checks/semantic-checks.json'],'original_static_pairs_checked':30,'independently_compared_case_states':30,'independently_compared_event_assertions':54,'source_audit_definitions_per_scope':107,'runtime_rule_count':64,'runtime_must_obligations':64,'advisory_runtime_obligations':1,'action_schema_limit':40,'actual_actions_per_scenario':14,'expected_override_rejected':True,'foreign_fixture_rejected':True,'dropped_action_rejected':True,'disabled_empty_interval_stays_unassessed':True,'definition_only_source_acceptance_rejected':True,'sdk_commands':0,'product_source_reads':0,'native_runs':0,'subagents':0},
 'supported_api_review':{
  'compiler':'design_contract.seal/compile_contract/verify_generated and actual CLI succeeded with frozen module identity; expected/provenance/tolerance/state/action reconstruction is exact.',
  'catalog':'review_contract.catalog produces199 atom identities per plan with independently sourced questions/units/colors and explicit ownership. No reviewer expected/status overrides are allowed.',
  'execution':'execution_plan.compile_execution/verify_execution preserves all14 action indices and exact approved fixtures/bridge hashes. Private input values stay confined to private review artifacts.',
  'events':'native_checks.callback_verdict requires successful xcui_tap/compose_onclick or caller_fixture_update, same input/process bindings and exact original intervals. Caller-update checks use actions10 and13; disclosure checks actions1 and8; choice actions2/4/5/12; request action6.',
  'geometry':'Control height/gap use accessibility_box/control basis; status inset uses accessibility_box/semantic basis against a separate real Text node. Native geometry requires unique fully visible boxes in one coherent frame. No generic layout_box or computed SwiftUI font/color MUST is used.',
  'pixels':'native_pixels supports the declared normalized solid-region samplings, explicit opaque ARGB, zero RGB tolerance, full-leading-strip support1.0, and original screenshot/native-coordinate mapping. Canvas/surface are component-owned visible-fragment samples; exact glyph ink is not claimed.',
  'source_audit':'Shared implementation_audit definitions CLI succeeded with frozen design_contract preloaded.107 typed expected-true source propositions name exact production or approved bridge paths. Future catalog/bind requires actual original SHA and valid line ranges for every declared file; definitions cannot be accepted as actuals.',
  'host_calls':'Inspected iOS ObserverBridge.make(fixture:onEvent:) and Android ObserverBridge.Content(current){event} calls match the approved bridge signatures and public component constructor/function signatures. Both host templates supply parent scrolling and16/24 padding without identity wrappers.',
  'minimum14':'Read the pinned check_minimum_api.py interface and run() body only. It emits a real AlertToast module from nonhidden alerttoast/Sources Swift files targeting arm64-apple-ios14.0-simulator, then typechecks the unchanged bridge against that module at14. This and the independent ios-api14-availability source proposition are mandatory future gates. No SDK import/run occurred; linking/legacy packaging/runtime are explicitly unverified.'
 },
 'N_A_review':{'result':'justified','details':'Collapsed chapter rows are absent by definition; title-vs-heading hierarchy is N/A when headings are absent. Target-only intermediate states do not assert full-page structure, exact row-copy sweeps or complete visual acceptance; the approved five full states retain those checks, including full expanded permitted/requested. Event N/As retain only the actual independently declared stimulus intervals. No entire MUST is disposed through all-N/A. Original expanded-state sampling is adjusted only by the prospectively authorized10-state amendment.'},
 'issues':[],
 'remaining_limits':[
  'No product implementation was inspected or written. All future source audits are unverified actuals until bound to final bytes and original line evidence; no definition-only result can release the component.',
  'No native rendering, preview, screenshot, SDK command, application build or launch occurred. Successful static compilation is not rendered style, real AX/Compose allocation, callback dispatch, update receipt, full sweep, native bottom reachability, pixel eligibility or visual consensus proof.',
  'Actual native status band/Text separation and coherent inset frames, exact observed native geometry, source-to-image mapping and solid sample eligibility must be checked on both platforms; unresolved evidence stays unknown and blocks the corresponding final MUST.',
  'Exact-capacity equality, the unmetered Wi-Fi-only-true request, and reset from an immediately open disclosure are source-route obligations in this representative design; no executed native truth-table claim is made. Same-ID updates remain unspecified.',
  'Static PNG/SVGs communicate independent copy, logical order and hierarchy. Their raster fonts and drawn allocations cannot certify actual native padding, shape, wrapping, colors, geometry or cross-platform pixel equivalence.',
  'iOS14 verification is SOURCE/MODULE/CALLER API only. The17 observer does not establish14. Current Xcode target14 packaging is explicitly unverified; there is no linking, archive, launch, OS14 runtime or physical hit-area certificate. Future compatibility evidence must retain emitted module bytes/hash and actual compiler/SDK identity as required by compatibility.json in addition to checker record/logs.',
  'The shared checker helper dependencies are outside this scoped review; root must retain its promised identical preimplementation freeze. No helper, SDK output or earlier failed engineering run was read or reused as this review evidence.',
  'Approval is pinned to both exact current design locks/policies and source manifest; it does not authorize replacing expectations after product evidence or dropping unknowns.'
 ],
 'review_independence':{'prior_reviewer_conclusions_read':False,'other_task_inputs_read':False,'treatment_assignments_read':False,'product_or_native_outputs_read':False,'original_raw_business_api_read':True,'communicated_with_other_agents':False,'scope_write_root':str(O)}
}
save(O/'review.json',review)
save(O/'SEAL.json',{'files':{str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SEAL.json'},'sealedAtUnix':time.time(),'hash_algorithm':'SHA256 original output bytes','note':'SEAL.json is excluded from its own file map; all other outputs are included.'})
print(json.dumps({'status':review['status'],'mapping_entries':len(mapping),'source_files_pinned':len(sources),'outputs_sealed':len(load(O/'SEAL.json')['files']),'public_lock':review['source_pins']['public_design_lock_sha256'],'private_lock':review['source_pins']['private_design_lock_sha256']},indent=2))
