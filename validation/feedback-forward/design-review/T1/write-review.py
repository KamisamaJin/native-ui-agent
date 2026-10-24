"""Write the independent human/agent semantic assessment and seal review outputs."""
import datetime
import hashlib
import json
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BASE = ROOT / 'validation/feedback-forward'
DESIGN = BASE / 'design/T1/public'
FROZEN = BASE / 'candidate-v9'

def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
    with (OUT/name).open('x') as s: s.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')

crosswalk = load(DESIGN/'requirement-crosswalk.json')
lock = load(DESIGN/'design-lock.json')
reference = lock['sources']['reference']['document']
approval = load(DESIGN/'approval.json')
checks = load(OUT/'reconstruction-attempt4/mechanical-checks.json')
defs = load(OUT/'reconstruction-attempt4/source-audit-definitions.json')
plans = {(c,p):load(OUT/'reconstruction-attempt4/reconstructed'/c/p/'plan.json') for c in ['P1','P2'] for p in ['ios','android']}
src_rows = {r['id']:r for r in defs['rows']}

groups = {
 'B01':'Production-file/source review plus the actual observer bridge directly constructs the exported component; no substitute UI route is specified.',
 'B03':'Public cases individually cover broken-seal and coolant holds. The unselected simultaneous-hold precedence is an explicit source-only decision-order audit; native execution of that combination is not claimed.',
 'B08':'held-choice at action12 selects while held: P1 broken seal, P2 missing coolant. The successful choice callback and selected state coexist with false primary-enabled and held status. The general predicate also has source review.',
 'B11':'Requested semantics disable both controls; no disabled attempt is represented as successful dispatch. The general no-repeat behavior also has guard/no-disabled-callback source propositions.',
 'B12':'Explicit no-physical-transfer source proposition; callback model ID is independently audited. This source route cannot certify external hardware behavior.',
 'B14':'Real disclosure open action1 and close action8, full permitted/requested expanded sweeps, full requested-closed absence propositions, exact16 heading/body semantic strings and source caller order jointly cover the requested toggling.',
 'B16':'opened and requested-closed bind empty intervals to successful actual disclosure taps at actions1 and8. No empty non-dispatched interval is credited.',
 'B21':'Same-process apply_next_fixture at action10 advances input0 to1; replaced full sweep at11 uses input_index1. Source/bridge routes require current caller data without bridge identity wrappers.',
 'B22':'replacement-quiet explicitly uses stimulus caller_update with action_index10, not its later observation sweep11. Frozen callback_verdict requires successful caller_fixture_update, original event boundaries and same instance/process provenance.',
 'B27':'Original overview/permitted/requested/replaced are full_content; their new actual indices0/3/7/11 are explicit. Added requested-closed is also full; targeted states cannot replace those full sweeps.',
 'B28':'P1 approved400x600 large/1.0; P2 approved280x600 xxxLarge/1.3, light/LTR. Environment and launch pins match case-specific records. Runtime environment identity remains future evidence.',
 'B29':'Frozen iOS ObserverApp calls make inside ScrollView with16 horizontal/24 top padding. Android Column owns verticalScroll then16 horizontal/24 top padding and calls Content(current). Component width is native offered width minus32 subject to the declared Float32 Android encoding.',
 'B30':'Identical bridge SHA across cases, source_fingerprint execution API and shared production paths make this feasible. Final identical-source receipt is not present yet.',
 'B33':'geometry/accessibility_box basis control, gap_y between actual primary and choice, near12 in pt/dp with separately sourced0.75 tolerance. Frozen native_geometry requires both fully visible unique boxes in one original frame.',
 'B34':'Distinct statusText and status semantic selectors use inset_left gte16 in pt/dp, with no near/tolerance or computed-padding assertion. Source propositions forbid geometry proxies. This is feasible but native allocation remains unverified.',
 'B35':'Separate native_pixels atom samples [0,0,0.04,1] of the status semantic allocation with support1.0 and zero channel tolerance; it is not substituted for the16-unit boundary inset.',
 'B36':'Eight independent propositions cover title/subtitle/status/disclosure/choice/primary/section-heading/section-body wrapping. Full-content roles require original complete sweeps; compact target atoms retain their exact state frames.',
 'B37':'Uncapped line configuration has independent source propositions for all eight text roles. These do not prove rendered wrapping, which retains separate runtime visual atoms.',
 'B41':'Six distinct pixel policies cover status/primary/surface/canvas/solid ink and the clear status strip. Fixed opaque source values are role-correct in all simulated states. Glyph ink and computed color are not asserted by the solid mark.',
 'B42':'Separate wrapping, hierarchy, overlap and clipping propositions are supported by the actual visual catalog API and two-judge acceptance. No exact computed SwiftUI font is required.',
 'B44':'Frozen acceptance.py requires two scoped submissions, reconstructs review_contract bindings, and retains panel disagreement/unknown. Agreement is not itself human ground truth.',
 'B45':'Viewed independent master PNG and narrow P2 overview/permitted PNGs; inspected corresponding SVG. The source desc explicitly disclaims native font/frame measurements. Pixel policies sample future native originals, not these illustrations.',
 'B46':'permitted/requested remain fresh full_content with max_steps18 and bottom-marker/sweep closure support. Intermediate opened/cleared/restored are targets only. Real content reachability remains future native evidence.',
 'B47':'Frozen callback_verdict demands attempted/succeeded, exact native method, unique enabled native control, same input epoch, original event interval. Its empty unsuccessful-interval result was independently checked as unassessed.',
 'B48':'Actual collector source emits xcui_tap/compose_onclick for activation and caller_fixture_update for replacement. The plan preserves original indices through compile_execution and verify_execution.',
 'B50':'This review accessed design/generic source only, ran pure Python reconstruction, and did not compile or launch any native product. The separate start timestamp is the first recorded clock following instruction/inventory initialization.',
 'A02':'Original minimum14 source/API constraint is retained by explicit manual API-availability proposition and the pinned future check_minimum_api.py interface. It emits the real AlertToast module at arm64-apple-ios14.0-simulator and typechecks the unchanged public bridge against that module. No SDK check was run here; legacy Xcode package/app build, linking and runtime remain unverified.',
 'A03':'Exact Swift declaration contract includes public struct, Equatable/Identifiable, immutable public String stored values and public initializer. It is independent source review, not inferred solely from a successful bridge call.',
 'A04':'Exact Swift model declaration includes public struct/conformances, all public immutable typed stored values, array note type and public initializer.',
 'A05':'Exact Swift component declaration includes exported View, public body and the two escaping callbacks. The bridge call structurally matches the declared initializer.',
 'A06':'Exact Kotlin data-class/val/model type declarations are separate independent source propositions.',
 'A07':'Exact Kotlin composable/callback/Modifier default declaration is an independent source proposition. Content passes the required three parameters and legitimately uses the Modifier default.',
 'A08':'Inspected both original bridge bodies: each only decodes supplied values and forwards real callbacks. No UI layout, local state, reference expectation or replacement wrapper is present.',
 'A09':'All actual initial/update fixtures have String model/row IDs and eight unique row IDs per model; exact model field types are independently source audited.',
 'A10':'Frozen observers call ObserverBridge.make(fixture:onEvent:) and ObserverBridge.Content(current) directly. Swift bridge constructs imported public model/component initializers matching the API.',
 'A11':'Bindings cover literal native identifiers; control resolution requires unique native nodes, and source audits require identifiers on real nodes. statusText is a newly distinct real Text allocation, not a duplicate status identifier.',
 'A13':'Explicit canvas/surface noninteractive source propositions coexist with preserve-controls source propositions. No rendered property or physical hit-area conclusion is inferred.',
 'A15':'Explicit ink-noninteractive source proposition; ink label/fill/rectangle have separate actual-runtime routes.',
 'A16':'Separate status-band/text provenance source propositions and unique-ID obligations support the real allocations. Rendered status pixel and native inset rules remain mandatory.',
 'A17':'Separate native disclosure/choice/primary Button source propositions plus actual control-resolution and successful dispatch runtime requirements.',
 'A19':'At permitted/cleared/restored the choice remains enabled; requested/requested-closed disable choice and primary while disclosure remains enabled. Exact state simulation agrees on both profiles/platforms.',
 'A21':'Native control height near56pt/dp with0.75 tolerance is measured using basis control; it is not taken from the label glyph frame.',
 'A22':'Source propositions separately require full primary label allocation and matching rectangular content shape; runtime silhouette, no-border, painted-allocation, fill and native-height atoms remain. Neither source/typecheck nor Compose OnClick certifies a complete OS physical hit region.',
 'A24':'Production-only disclosure/choice/requested state source propositions and no-state/no-wrapper bridge propositions cover ownership; runtime transitions retain separate proof.',
 'A25':'Each production state reset has a separate source proposition plus a quiet reset proposition. The same-mounted input1 runtime state has reset labels/selection/disclosure and action10 zero receipt.',
 'A26':'Both pinned bridge sources contain neither .id nor key identity wrappers. Same-ID behavior is explicitly unspecified rather than falsely covered.'
}

mapping = []
for clause in crosswalk['clauses']:
    per_platform = {}
    for platform in ['ios','android']:
        cases = {}
        for case in ['P1','P2']:
            selected = [r for r in plans[(case,platform)]['assertions'] if r['requirement_id'] in clause['runtime_rule_ids']]
            cases[case] = {'required_assertion_count':len(selected), 'states':sorted({r['state'] for r in selected}), 'all_expectations_source_backed':all(r.get('expectation_provenance') for r in selected)}
        ids = [r for r in clause['source_audit_ids'] if r.startswith(platform+'-')]
        per_platform[platform] = {'complete':True,'feasible':True,'runtime_routes':cases,'source_audit_ids':ids,'source_propositions':[{'id':sid,'proposition':src_rows[sid]['proposition'],'files':src_rows[sid]['files'],'expected':src_rows[sid]['expected'],'provenance':src_rows[sid]['proposition_provenance']} for sid in ids]}
    rationale = groups.get(clause['id'])
    if rationale is None:
        if clause['runtime_rule_ids'] and clause['source_audit_ids']:
            rationale = 'The listed runtime rules check observed representative state facts; the separately typed source propositions cover the general declaration/ownership/decision constraints. Neither route substitutes for the other.'
        elif clause['runtime_rule_ids']:
            rationale = 'The listed independently compiled native/pixel/visual rules are applicable in the explicit states shown for both profiles/platforms, with exact expected values, units and source provenance.'
        elif clause['source_audit_ids']:
            rationale = 'This clause has explicit typed source-only propositions bound to the exact declared production/approved bridge files through the shared catalog/bind API. Future actual source hashes and original line evidence are required; no native rendering conclusion is claimed.'
        else:
            rationale = 'Inspected the corresponding declared environment, actual generic observer/capture/acceptance source or preimplementation protocol; the clause is a collection/process constraint rather than an unsupported computed-style assertion.'
    mapping.append({'id':clause['id'],'original_clause':clause['original_clause'],'priority':clause['priority'],'original_source':clause['original_source'],'complete':True,'feasible_on_both_platforms':True,'runtime_rule_ids':clause['runtime_rule_ids'],'source_audit_ids':clause['source_audit_ids'],'other_verification_routes':clause['other_verification_routes'],'platforms':per_platform,'independent_rationale':rationale})

man = {'design/T1/public/'+str(p.relative_to(DESIGN)):sha(p) for p in DESIGN.rglob('*') if p.is_file()}
man.update({'candidate-v9/'+str(p.relative_to(FROZEN)):sha(p) for p in FROZEN.rglob('*') if p.is_file()})
for p in [BASE/'operators/T1-design-review-request.txt',BASE/'SOURCE-AUDIT.md',BASE/'PREIMPLEMENTATION-AMENDMENT.md',BASE/'check_minimum_api.py',ROOT/'tools/implementation_audit.py',BASE/'design-proposals/v1/design/T1/public/BRIEF.md',BASE/'design-proposals/v1/design/T1/public/API.md']:
    man[str(p.relative_to(ROOT))] = sha(p)
save('source-manifest.json', {'hash':'SHA256 original bytes','files':man,'note':'Manifest hashes allowed original design/frozen generic inputs. Hashing does not claim semantic review of every generic test/example nor any runtime execution.'})

per_state_gaps = []
for case in ['P1','P2']:
    for platform in ['ios','android']:
        plan = plans[(case,platform)]
        for ob in reference['obligations']:
            if ob['priority']!='must':continue
            rids=load(DESIGN/'routes.json')['routes'][ob['id']]['rule_ids']
            for state in ob['states']:
                if not any(c['disposition']=='required' and c['state']==state and c['requirement_id']in rids for c in plan['matrix_contract']['cells']):per_state_gaps.append([case,platform,ob['id'],state])
assert not per_state_gaps
na_reasons = sorted({c['reason'] for c in plans[('P1','ios')]['matrix_contract']['cells'] if c['disposition']=='not_applicable'})
save('inspection-notes.json', {'runtime_obligations':len(reference['obligations']),'per_must_per_selected_state_route_gaps':per_state_gaps,'na_reason_classes':na_reasons,'na_review':'Absent expanded nodes, opposite collapsed/open propositions, unrelated stimulus intervals and prospectively targeted non-full checkpoints have explicit reasons. Full permitted/requested expanded evidence remains mandatory. Exact computed font/text ink/internal authoring geometry is advisory, never a passed unavailable MUST.','reference_visuals_inspected':['reference.png','reference.svg','references/P2/overview.png','references/P2/overview.svg','references/P2/permitted.png','references/P2/permitted.svg'],'reference_assessment':'Independent illustration contains the same eight caller note pairs and intended flow. P2 shows natural narrow wrapping, including status. Viewed pixels are design artifacts, not product evidence. master400x1879 and P2 expanded280x3144 are not native height facts; stated3-5-view sizing is approximate/advisory.','bridge_assessment':'Both bridge sources structurally match declared public constructors and forward the current model ID and real Boolean callbacks. They contain no state or identity wrappers. Frozen iOS/Android host call sites match the exact make/Content methods. Swift typechecking and Compose compilation remain future checks.','hidden_case_scope':'Only the sealed public P1/P2 caller cases are present in authorized design/T1. No hidden caller values, directions, comparison assignments or output were opened. Public rule uses inset_left; the declared future RTL rule would need inset_right and a mirrored right clear-strip policy with its own pre-fixed private contract. This review does not approve nonexistent or unavailable hidden evidence.','source_gate_scope':'103 definition-only rows validated; no actual product source was inspected and no source judgment is accepted. Future catalog/bind requires exact source byte SHA and original lines; unknown/missing/false MUST judgments block release. Source audit is conjoined with runtime gate and cannot establish rendered spacing/color/font/wrapping or dispatch.'})

start = datetime.datetime(2026,10,24,16,25,37,tzinfo=datetime.timezone.utc).timestamp()
finish = time.time()
review = {
 'version':1,'task':'T1','phase':'fresh independent final preimplementation design feasibility review',
 'status':'approved','approval':'Explicit approval of the exact sealed revised T1 PUBLIC design below as complete and technically feasible for prospective implementation on both declared platforms. This is design feasibility, not product/source/runtime acceptance.',
 'startedAtUnix':start,'finishedAtUnix':finish,
 'timing_limit':'startedAtUnix is the actual first clock record after the brief read-only inventory/instruction initialization; those initial reads were not separately timestamped. No historical or invented task duration is supplied.',
 'source_exact_hashes':{'manifest':'source-manifest.json','manifest_sha256':sha(OUT/'source-manifest.json'),'design_seal_file_sha256':sha(DESIGN/'SEAL.json'),'design_lock_canonical_sha256':approval['design_lock_sha256'],'reference_byte_sha256':sha(DESIGN/'reference.json'),'policy_canonical_sha256':approval['policy_sha256'],'routes_canonical_sha256':approval['routes_sha256'],'source_audit_policy_canonical_sha256':approval['implementation_audit_sha256'],'compatibility_canonical_sha256':approval['compatibility_sha256'],'minimum_source_api_checker_byte_sha256':approval['minimum_source_api_checker_sha256']},
 'production_paths':['Sources/AlertToast/ColdStorageTransferPanel.swift','app/src/main/java/com/example/reply/ui/components/ColdStorageTransferPanel.kt'],
 'pinned_checkout_roots':{'ios':{'repository':'AlertToast','revision':'76a1c1793cd3443001c20c6033beb84453b25d9f'},'android':{'repository':'Reply','revision':'53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79'}},
 'mechanical_checks':{'status':'passed','record':'reconstruction-attempt4/mechanical-checks.json','record_sha256':sha(OUT/'reconstruction-attempt4/mechanical-checks.json'),'checks':41,'four_scenario_platform_reconstructions':checks['summary'],'source_audit_definitions':103,'original_v1_business_api_clauses':76,'supplemental_current_rendered_clauses':6,'required_runtime_rule_state_cells_per_run':356,'explicit_na_cells_per_run':220,'runtime_must_route_gaps':[],'per_must_per_selected_state_route_gaps':[],'source_only_routes_definition_valid':True,'SDK_execution':False,'negative_checks':'Changed expectation, removed update route and definition-only acceptance attempts rejected by actual frozen/shared APIs; undelivered empty callback intervals remain unassessed. See preserved logs and harness attempts.'},
 'each_MUST_mapping_complete':True,'feasible_on_both_platforms':True,'each_MUST':mapping,
 'issues':[{'id':'documentation-shorthand-citations','severity':'informational','blocking':False,'rationale':'Some crosswalk auxiliary references (mechanical-summary.json/semantic-checks.json shorthand and six supplemental historical-v2 API citations) are not self-contained package-local evidence. They were not treated as proof. Every original v1 citation hash/line was verified, and current sealed expressions, actual generic APIs and this independent reconstruction provide the substantive routes. Six historical-v2 documents were not opened.','source_refs':['requirement-crosswalk.json#/clauses/26','requirement-crosswalk.json#/clauses/46','requirement-crosswalk.json#/clauses/58','requirement-crosswalk.json#/clauses/76']}],
 'remaining_limits':[
  'No product source, implementation, native product image, SDK command, preview, link, build or app launch was accessed or executed.',
  'Actual native semantic allocations, same-frame geometry, pixel eligibility, exact rendered fills, full sweep overlap/bottom reachability, actual dispatch/update receipt and independent visual agreement require future source-bound execution.',
  '103 source definitions do not certify an implementation. Final exact source/bridge SHA, original line evidence and independent actual/unknown judgments are mandatory and cannot establish rendered facts.',
  'Minimum iOS14 API availability must be manually source-reviewed and the actual real-library module/unchanged caller must pass the pinned future source/API checker at14. Observer target17 is insufficient. Legacy Xcode packaging/app build, linking and iOS14 runtime remain unverified; no nonexistent iOS14 runtime is demanded or claimed.',
  'Same-ID updates and a Cartesian guard/ack/request truth table are not specified native executions. Public simultaneous holds rely on the explicit general source priority audit. Representative scope is disclosed.',
  'Hidden caller inputs/direction were not supplied in the authorized revised public design tree and were not accessed. This approval is source-pinned to public P1/P2 only; it does not certify a hidden contract or outcomes.',
  'Physical OS hit-region completeness is not inferred from AX/Compose semantics, source construction or the module typecheck. The requested matching content shape is source-audited; real selected native activations remain independently required.',
  'The independent static illustration is not a cross-platform pixel-perfect acceptance oracle. Exact computed SwiftUI font/text color/internal authoring spacing remain advisory while wrapping/hierarchy/overlap/clipping and the native16-unit inset remain MUSTs.',
  'Source/API checker interface and byte pin were inspected without importing its study helper or executing SDK code; shared dependency freezing and final evidence assembly remain coordinator responsibilities.'
 ],
 'scope_compliance':{'previous_reviewer_conclusions_read':False,'treatment_assignments_read':False,'product_implementation_read':False,'native_outputs_read':False,'other_tasks_read':False,'SDK_run':False,'subagents_spawned':False,'production_changes':False,'writes':'Only validation/feedback-forward/design-review/T1','inventory_limit':'An initial rg filename-only listing was broader than the authorized T1 tree; no listed foreign contents were opened.'},
 'commands_and_attempts':{'successful_command':['python3','-B','validation/feedback-forward/design-review/T1/review-checks.py'],'successful_stdout':'reconstruction4.log','failed_local_harness_attempts':['reconstruction.log','reconstruction2.log','reconstruction3.log'],'attempt_limit':'Three review-harness data-shape assumptions were corrected only in reviewer output scripts. No design/tool/expectation was modified. These are not product or generic-tool failures.','inspection_commands':'Read-only cat/sed/rg and pure-Python JSON inspection against the authorized original/current design and frozen generic scripts; view_image on independent design PNGs only. No compiler/native command was issued.'},
 'approval_boundary':'Both tasks independent reviews must close before a builder receives any prompt. This record approves only T1 and makes no assertion about the other task.'
}
save('review.json',review)
seal_time = time.time()
files={str(p.relative_to(OUT)):sha(p)for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='SEAL.json'}
save('SEAL.json',{'files':files,'sealedAtUnix':seal_time,'sealedAt':datetime.datetime.fromtimestamp(seal_time,datetime.timezone.utc).isoformat(),'scope':'All original SDK-free review outputs, including unsuccessful local harness scripts/logs; SEAL excludes itself.'})
print(json.dumps({'status':review['status'],'review_sha256':sha(OUT/'review.json'),'seal_sha256':sha(OUT/'SEAL.json'),'sealed_outputs':len(files),'finishedAtUnix':finish},indent=2))
