#!/usr/bin/env python3
"""Seal the complete independently authored cohort after all pure admissions."""
from author import *

def main():
    shared=load(ROOT/'SHARED-PREFLIGHT-SUMMARY.json');summary=load(ROOT/'PURE-COMPILATION-SUMMARY.json');mapping=load(ROOT/'APPROVAL-MAPPING.json')
    assert shared['passed_count']==40 and shared['passes_each_arm']=={'candidate-v13.9':20,'baseline-v12.6-common-6':20} and summary['all_twenty_pure_chains_passed']
    correction=load(ROOT/'CORRECTION-LEDGER.json')
    assert correction['original_inventory_preserved'] and correction['frozen_corpus_unchanged']
    clause_routes={
        'catering-package':[['root-buffet-enabled'],['root-boxed-enabled'],['detail-reusable-enabled'],['detail-compostable-enabled']],
        'training-pathway':[['root-guided-enabled','root-independent-enabled'],['root-guided-enabled'],['root-independent-enabled'],['detail-certificate-enabled'],['detail-practice-enabled']],
        'subscription-capacity':[['root-scale-enabled'],['root-team-enabled'],['detail-annual-enabled'],['detail-monthly-enabled']],
        'visitor-preclearance':[['root-research-enabled','root-office-enabled'],['root-research-enabled'],['root-office-enabled'],['detail-research-badge-enabled'],['detail-visitor-escort-enabled']],
        'candidate-disposition':[['root-continue-enabled'],['root-archive-enabled'],['detail-technical-enabled'],['detail-recruiter-enabled'],['detail-skills-gap-enabled'],['detail-role-closed-enabled']],
    }
    requirement_index=[]
    for t in TASKS:
        rows=[]
        for i,clause in enumerate(t['rules']):rows.append(dict(id='B'+str(i+1).zfill(2),clause=clause,provider='typed-native-control',rule_ids=clause_routes[t['id']][i]))
        roots=['root-'+k+'-selected' for k,_ in t['roots']];details=['detail-'+k+'-selected' for k,_ in t['details']]
        rows += [
            dict(id='S01',clause='A fresh, changed-entity, or changed-published-revision input clears all transient selections, confirmation, and receipt.',provider='state-bound-native-controls',rule_ids=roots+details+['ack-selected','receipt-label','submit-enabled']),
            dict(id='S02',clause='A different eligible root clears detail and confirmation; reselecting the same root is idempotent.',provider='state-bound-native-controls',rule_ids=roots+details+['ack-selected','status-label','summary-label']),
            dict(id='S03',clause='A different eligible detail clears confirmation; confirmation toggles only when root and detail are valid.',provider='state-bound-native-controls',rule_ids=details+['ack-enabled','ack-selected','submit-enabled']),
            dict(id='S04',clause='Same-pair replacement preserves valid state/receipt, invalidates root before detail, updates display, and emits no business callback.',provider='state-bound-native-controls-and-successful-update',rule_ids=roots+details+['ack-selected','receipt-label','title-label','context-label','notes-label','replacement-events']),
            dict(id='S05',clause='Successful enabled recording emits one exact ordered event, then visibly records and disables all interaction; other successful taps are quiet.',provider='unique-successful-native-activation-and-callback',rule_ids=['submit-enabled','activation-events','receipt-label','ack-enabled']+['root-'+k+'-enabled' for k,_ in t['roots']]+['detail-'+k+'-enabled' for k,_ in t['details']]),
            dict(id='C01',clause='Full caller text, exact summary/status branches and exact receipt text remain displayed after real actions and caller updates.',provider='native-labels-plus-source-backed-visual',rule_ids=['title-label','context-label','notes-label','status-label','summary-label','receipt-label','body-wrap','content-overlap','horizontal-fit']),
            dict(id='V01',clause='The real component uses opaque designed surface/primary/first-row fills, visible selected check, and supported control-box height.',provider='native-pixels-and-geometry-and-Boolean-visual',rule_ids=['surface-fill','primary-fill','first-option-fill','selection-mark','primary-height','first-option-height','confirmation-height']),
            dict(id='V02',clause='Typography follows the independent 24/15 system type intent. Android available text layout is precise; iOS uses the explicit visual hierarchy/wrapping proposition.',provider='platform-scoped-native-or-Boolean-visual',rule_ids=['type-hierarchy','body-wrap']),
            dict(id='SRC01',clause='Real production API is exactly the immutable input and View/composable signature in API.md.',provider='source-review-still-unassessed',responsibility_id='production-api'),
            dict(id='SRC02',clause='Actual bridge only decodes the fixture, applies the stock Android theme, and passes the same callback to the real component.',provider='source-review-still-unassessed',responsibility_id='thin-bridge'),
            dict(id='SRC03',clause='Actual additive production placement/product/package and bridge-to-production call match API.md.',provider='source-review-still-unassessed',responsibility_id='production-placement'),
        ]
        write(ROOT/'public/tasks'/t['id']/'REQUIREMENT-MAP.json',dict(version=1,task=t['id'],clauses=rows,scope='Semantic index into the sealed atomic denominators and three required source-review duties. No source or native actual is approved.'))
        for family in ['public','private']:
            for platform in ['ios','android']:
                profile_id=family+'-'+t['id']+'-'+platform;entry=mapping['profiles'][profile_id];plan=load(ROOT/entry['paths']['plan'])
                available=set(plan['matrix_contract']['selected_requirements'])
                semantic=[]
                for row in rows:
                    atoms=[r for r in row.get('rule_ids',[]) if r in available]
                    if row['id']=='V02' and platform=='android':atoms += [r for r in available if r.startswith(('title-','context-')) and any(r.endswith('-'+p) for p in ['font_sp','font_weight','color_argb','overflow','ellipsized','lines'])]
                    semantic.append(dict(requirement_id=row['id'],source_clause=row['clause'],atomic_assertion_ids=[a['id'] for a in plan['assertions'] if a['requirement_id'] in atoms],source_responsibility=row.get('responsibility_id'),actual='unassessed' if 'responsibility_id' in row else 'not-run'))
                requirement_index.append(dict(profile_id=profile_id,requirements=semantic,explicit_unavailable_projections=[dict(property='generic-computed-padding-and-corner-radius',disposition='N/A',reason='Public native packets expose no generic computed modifier/style-tree provider. Numeric tokens remain design intent, not measured effective padding or corner radius.'),*([dict(property='generic-SwiftUI-computed-typography-color-text-layout',disposition='N/A',reason='Public iOS AX has no generic SwiftUI computed font/color/layout provider. Exact per-state N/A cells remain in MASTER-DENOMINATOR; required Boolean visual atoms remain separate.')] if platform=='ios' else [])]))
    write(ROOT/'MASTER-REQUIREMENT-INDEX.json',dict(version=1,profiles=requirement_index,atomic_denominator='MASTER-DENOMINATOR.json',source_duties_each_profile=3,scope='Semantic completeness ledger; atomic observed actuals and source truth are deliberately unassessed. Capability admission is not business correctness.'))
    read_paths=[TOOLS.parent/'SKILL.md',TOOLS.parent/'assets/ios-observer/CONTRACT.md']
    read_paths += sorted((TOOLS.parent/'scripts').glob('*.py'))
    read_paths += sorted((REPO/'validation/pooled-forward/baseline-v12.6-common-6/scripts').glob('*.py'))
    read_paths += [TOOLS.parent/'references'/n for n in ['design-contract.md','native-precision.md','protocol.md','state-evidence.md','atomic-review.md','managed-execution.md','decision-feedback.md','native-tools.md']]
    read_paths += sorted((TOOLS.parent/'assets/design-example').glob('*.json'))
    read_paths += [TOOLS.parent/'assets/atomic-example'/n for n in ['contract.json','reference.json','policy.json','environment.android.json','environment.ios.json']]
    read_paths += [TOOLS.parent/'assets'/n for n in ['profile.example.json','profile.ios.example.json']]
    read_paths += [REPO/'validation/pooled-forward/cache/hosts/alerttoast/Package.swift',REPO/'validation/pooled-forward/cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/theme/Theme.kt',REPO/'validation/pooled-forward/cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/theme/Type.kt',REPO/'validation/pooled-forward/cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/components/ReplyEmailListItem.kt',REPO/'validation/pooled-forward/business-design-v2/_authoring/revise.py',REPO/'validation/pooled-forward/design_capability_preflight.py',REPO/'validation/pooled-forward/operators/design-capability-preflight-freeze.json']
    write(ROOT/'READ-SET.json',dict(version=2,context='/root/v13_business_design2',independent_business_topics=[t['id'] for t in TASKS],content_sources=[dict(path=str(p.relative_to(REPO)),file_sha256=sha(p),scope='Frozen allowed pure dependency/schema/reference or stock host API/theme; no implementation/runtime evidence.') for p in sorted(set(read_paths))],preserved_own_original_design=dict(path='validation/pooled-forward/business-design-cohort2',seal_sha256=correction['original_seal_sha256'],scope='Parent explicitly authorized reuse of these independently authored five cases for a pre-code numeric transport-domain correction. Read for regeneration and byte-preservation checks only; all existing corpus expectations remain unchanged.'),inventory_only=['frozen candidate file names, including test names; no test content read','stock host file names; no rendered images or compiled content read'],prohibited_not_read=['candidate production implementations','earlier rejected shipment/appointment/invoice/outage/equipment business sources or initial UI','native benchmark/result/qualification evidence','native screenshots or rendering','SDK tools or caches'],generic_scaffold_ranges_read={'business-design-v2/_authoring/revise.py':'lines1-90 only during original independent design; parent explicitly authorized generic schema scaffold'},extra_authorized_generic_preflight='Root explicitly authorized both frozen SUT pure tool roots and the shared pre-code script; only own placeholder/capability metadata generated.'))
    write(ROOT/'AUTHOR-DECLARATION.md','''# Independent preimplementation business design declaration

Author context: `/root/v13_business_design2`. The five selected topics are catering
package configuration, training pathway enrollment, subscription capacity changes,
visitor access preclearance, and recruiting candidate disposition. They were chosen
without earlier business sources, candidate code, screenshots, or suspected defects.
The parent accepted these as new distinct topics. READ-SET.json records permitted
source identities; the earlier generic schema scaffold was authorized separately.

This v2 revision preserves those exact five independently authored cases. A later
independent pre-code review found that the public JSON schemas admitted integers
outside Kotlin Int/Gson asInt's shared signed 32-bit transport domain. The parent
authorized this correction before any production UI implementation. The original
829-file cohort and seal remain byte-for-byte unchanged. CORRECTION-LEDGER.json
records the numeric schema bounds, documentation clarification, regenerated
identities, and complete unchanged-corpus checks. No business case, fixture,
outcome, action, style token, native unit, or denominator cell was changed.

All five public APIs, business predicates, schemas, public and private inputs,
original actions, exact outcomes, authored SVG/token references, observation
bindings, native/visual routes, and complete denominators were fixed together
before any production UI code. ALL-INPUTS-FIXED.json records that staging boundary.
There is no production UI implementation in this bundle. Files under
`pure-subjects` are labelled non-UI capability placeholders, never an initial UI.

Every task has11 public states and18 original actions; each heldout family has13
states and21 original actions. Hosts own vertical scrolling. Changes of caller
entity or published revision are observable reset keys; the same pair preserves
valid local state and reconciles invalid selections. No test requires resetting an
indistinguishable identical-value epoch. No network, time, random, async, overlay,
popup, lazy container, or test bridge business logic is specified or implemented.

Both platforms require complete separate locks. Each has both typed expression
slots because the frozen compiler requires them. The opposite slot is explicitly
schema-only and forbidden for runtime use. The external actual-platform guard
binds exact lock, plan, policy, routes, environment, fixtures, bridge and launch
identity. A placeholder profile is refused by the native entry.

Responsibility groups are derived from applicable rule IDs only, before the final
cohort seal. Every required native group has actual matching compiled assertion
IDs/kinds and the real component owner; no empty required native font group exists
on iOS. iOS unavailable exact TextLayout cells are N/A in the master denominator,
with source-backed Boolean visual style questions retained separately. Opaque
rendered gutter pixels and native control-box geometry do not claim computed
SwiftUI styles, effective padding, or physical touch geometry.

All20 profiles passed the frozen candidate CLI seal/compile/catalog/routes/
execution/audit chain. The frozen baseline rebuilt all20 plans/actions exactly,
and both frozen SUTs passed all20 shared subprocess-forbidden full-chain capability
preflights (40 checks total).
Source API, thin bridge and production placement remain three MUST source duties
in every profile. Capability compatibility against labelled placeholders is not
source approval. All native/runtime and actual source truth remains unassessed;
no native build, rendering, source approval, defect injection or quality claim was
made. CLI stdout/stderr and all generated pure artifacts are retained unchanged.

This seal fixes independently authored design intent for the parent's separate
design review. It does not assert human approval or authorize a native run before
that review. Hashes establish identity, not authorship, business correctness,
native capability truth, or product quality.
''')
    write(ROOT/'README.md','''# New independently authored five-task business cohort

The bundle is sealed for independent preimplementation design review. It contains
five new business components and no production UI implementation or native result.

This v2 corrects only the pre-code integer transport-domain contradiction. Every
fixture Int has an explicit shared signed 32-bit bound, preserving tighter existing
minima and portfolioScore's maximum 100. accountBalanceCents explicitly allows
-2147483648 through 2147483647. Revision is a caller-owned comparison key; no
increment, sum, or product is required by the published business decisions. The
finite frozen corpus does not certify arbitrary implementation arithmetic.
CORRECTION-LEDGER.json proves all existing corpus business/style/evidence inputs
remain unchanged and the original829-file sealed cohort remains intact.

Workers receive only `public/tasks/<task>/`. Each public brief, API, schema, SVGs,
tokens, complete public flow, typed expected-state sources, platform lock, bindings,
actions, and exact thin bridge is sufficient to implement the same published rules
for both platforms. Keep `private/` and its fixtures/expectations physically withheld.
Root manifests contain identities/coverage metadata and are coordination artifacts.

The topics are catering package configuration, training pathway enrollment,
subscription capacity changes, visitor access preclearance, and recruiting candidate
disposition. Public flows have11 states/18 original actions each; heldout flows have
13 states/21 original actions each. Both platform projections are separately pinned.

`PURE-COMPILATION-SUMMARY.json` retains120 successful frozen pure CLI invocations.
`SHARED-PREFLIGHT-SUMMARY.json` retains40 additional subprocess-forbidden complete
capability checks: all20 in each frozen SUT, plus20 exact baseline plan/action
rebuilds. `PROFILE-ADMIT-DECLARATION.json` records20 positive and300 rejected
mapping checks. These are compatibility results only, with zero native runs and
zero actual source approvals. All three required source duties remain unassessed.

`MASTER-DENOMINATOR.json` is the exact all-task/all-family/all-platform atomic ledger.
`MASTER-REQUIREMENT-INDEX.json` connects published business/lifecycle/style/source
clauses to it and explicitly records unavailable computed-style projections.
`READ-SET.json` and `AUTHOR-DECLARATION.md` record independence and limits.

Always run `scripts/admit_profile.py` with an independently retained canonical
APPROVAL-MAPPING digest and the actual native platform before acquisition. Runtime
work must use `scripts/native_entry.py`, a config bound to actual production/source
subjects and native host options, and the parent's independent all-five review
receipt. Never run a schema-only opposite platform slot or a pure placeholder
profile. The frozen native SUT files were not edited.

`SEAL.sha256` pins every existing authored/pure artifact by original bytes.
`SEAL-IDENTITY.json` pins that inventory and the canonical approval mapping. Later
independent review records belong outside the sealed business input set.
''')
    write(ROOT/'PUBLIC-PACKETS.json',dict(version=1,worker_read_scope='Only public/tasks/<assigned-task>/**',tasks=[dict(task=t['id'],public_packet='public/tasks/'+t['id'],private_packet='withheld',swift_api=t['api'],kotlin_api=t['api']) for t in TASKS],private_source_must_not_be_in_worker_context=True))
    now=datetime.now(timezone.utc).isoformat()
    write(ROOT/'TIMELINE.json',dict(version=2,original_seal_sha256=correction['original_seal_sha256'],all_inputs_fixed=load(ROOT/'ALL-INPUTS-FIXED.json')['fixed_at_utc'],last_pure_cli=max(load(ROOT/p['path'])['recorded_at_utc'] for p in summary['cli_receipts']),shared_preflight_complete_before_seal=True,sealing_at_utc=now,production_implementation_started=False,native_runs=0,source_approvals=0,phase_order=['preserve original independently authored cohort and pre-code rejection','apply explicit shared Int32 schema bounds and documentation clarification','all-five corrected inputs fixed','twenty frozen candidate pure CLI chains','twenty exact frozen baseline plan/action rebuilds','forty shared complete capability preflights across both SUTs','exact-platform positive/negative guard checks','unchanged corpus and original seal verification','semantic/read-set declaration','new revision cohort inventory seal','parent independent review pending']))
    inventory=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p.name not in ['SEAL.sha256','SEAL-IDENTITY.json']:
            assert p.suffix!='.pyc' and '__pycache__' not in p.parts
            inventory.append(sha(p)+'  '+p.relative_to(ROOT).as_posix())
    write(ROOT/'SEAL.sha256','\n'.join(inventory)+'\n')
    identity=dict(version=2,original_seal_sha256=correction['original_seal_sha256'],sealed_at_utc=now,seal_file_sha256=sha(ROOT/'SEAL.sha256'),inventory_files=len(inventory),approval_mapping_canonical_sha256=digest(mapping),approval_mapping_file_sha256=sha(ROOT/'APPROVAL-MAPPING.json'),task_count=5,profile_count=20,shared_pure_preflight_passes=40,shared_passes_each_frozen_sut=shared['passes_each_arm'],baseline_exact_rebuilds=20,atomic_denominator_counts=load(ROOT/'MASTER-DENOMINATOR.json')['counts'],native_runs=0,source_approvals=0,independent_design_review='pending-parent-review',scope='Preimplementation Int transport-domain correction, authored-intent and pure capability identity only; original corpus preserved.')
    write(ROOT/'SEAL-IDENTITY.json',identity)
    print(json.dumps(identity))

if __name__=='__main__':main()
