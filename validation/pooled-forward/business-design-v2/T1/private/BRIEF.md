# T1 — Shipment release checklist

PRIVATE — embargoed until ALL10 final production-source/selfclaim seals. No implementation/repair worker may read this directory earlier.

Deliver `ShipmentReleasePanel`, a reusable additive AlertToast public SwiftUI View and Reply production Compose component. Use the exact typed API in API.md. Caller data is immutable; production owns actual UI decisions, state, and replacement transitions. `onEvent(String)` forwards local request payloads only.

## Business rules

1. Every lot is displayed in caller order. An available lot toggles membership in a multi-selection. Held lots remain visible, disabled, and show their supplied hold reason; a held lot cannot be selected.
2. Initially no lots are selected and Packing list checked is off. Any selection change clears packing approval. At least one selected available lot and packing approval are required to release.
3. Summary is exactly '{N} lots selected · {U} units', where U sums current selected quantities. Status strings and punctuation are fixed by the public outcome ledger.
4. A successful release emits exactly one 'release|{entityId}|{comma-separated selected IDs in ascending Unicode lexical order}'. No other user action emits an event. A recorded release locks all controls and primary submission; duplicate submission is disabled.
5. On replacement with the same entityId, preserve only selected IDs that are still present and available, recompute quantities from replacement data, clear packing approval and recorded status, and emit no event. On a changed entityId, clear all selection, approval, and recorded status, even when labels or IDs are reused.
6. The release callback is a local request/receipt, not proof of a network shipment. No network, timer, random, async, or full application navigation is involved.

## Layout and style

The annotated initial/ready SVGs are independent structural and qualitative references, not candidate renders or cross-renderer glyph pixel oracles. Native tokens in reference.json are normative. Order: heading, entity, description, prerequisite choices, dependent option rows, summary, status, final review/approval, primary. T4 puts its current preview between Preview notice and wording approval. Credit/modes/intake checks precede their dependent choices. Every section participates in one eager vertical flow. Keep all supplied text, selected decisions, disabled options and their reasons visible through natural wrapping; no ellipsis, internal scrolling, overlay, or horizontal overflow.

The panel is opaque white,16pt/dp inset,16pt/dp radius. Option rows use12pt/dp inset,8pt/dp gaps/radius, and an empty trailing24pt/dp paint gutter. Major sections use16pt/dp gaps. Selection marks are leading. Primary fills available content width, has48pt/dp control-box height and8pt/dp radius, with its fixed centered short label. Selected rows retain selected fill when recorded state locks controls; unselected disabled rows use disabled fill. Enabled unselected rows are white. Primary uses its separately sourced enabled/disabled opaque fills; do not blend native disabled alpha over them.

iOS uses explicit system22pt semibold heading and16pt regular body intent at Large Dynamic Type. Android reuses Reply titleLarge22sp/600 and bodyLarge16sp/400. iOS typography/layout/ink questions are qualitative source-backed atoms; no generic computed font, color, layout-box or padding extraction is claimed. Android available TextLayout font/color facts are separate native atoms. The48pt/dp primary assertion measures its actual control accessibility box, not physical OS touch area.

## Host, data and bridges

Approved viewport:390logical width,600height, light, LTR; iOS Large or Android font_scale1.0. iOS host inset16horizontal/24top offers358pt child width. Android uses matching host insets at requested390x600dp,density2.75 with `paparazzi-float32-screen-config-v1`; requested390dp may serialize389.81818dp. This encoding is not product tolerance. The existing host owns scrolling. No whole-app navigation claim is made.

Each family includes initial, same-entity and changed-entity typed payloads. The schema contains no decisions or expected state. The pinned thin bridge only decodes and calls production with the same callback; Android applies the real stock non-dynamic light theme. It has no replacement UI, business state, identity reset or synthetic callback. API placement and thin-bridge source responsibilities are separately audited.

## Scenarios and denominator

Scenario `hidden-edge` in contract.json fixes the original tap/apply_next_fixture/sweep/checkpoint route. Initial, ready/recorded, preview and replacement states have explicit full sweeps. Intermediate decision states have checkpoint/targets coverage and active local wrapping/mark/semantic/paint/callback checks. Every state has an independent after-target list. Earlier business stimuli are linked through `stimulus_action`; the compiler derives native target observation work. Whole-flow questions are scoped only to full-sweep states, without carrying an earlier pass into a target-scoped state. Every tap requires native enabled=true; toggles additionally require their exact previous selection. No direct state injection or invented action kind is allowed.

Callbacks require actual successful original native dispatch by the requested method. Missing, disabled, blocked, wrong-method or unexecuted actions cannot establish a callback pass/fail. Disabled choices are assessed as native facts without pretending to activate them. Every successful non-submit tap has an exact empty event interval; each successful submit has the exact one-element interval; successful caller replacement is silent. Full sweep evidence is distinct from those immediate intervals.

outcomes.json fixes exact business text, summaries, previews, disabled/selected decisions and payloads. denominator.json contains every rule×selected-state×platform/aspect cell with its exact source/operator/unit or explicit N/A reason. Native semantic facts, callbacks, rendered opaque pixels and atomic visual propositions are distinct. Unsupported iOS computed style, effective padding/glyph ink, physical hit area and whole-app concerns are N/A with reasons in reference.json#/scope, without padded mandatory U rows.

The routes close meaningful regression dependencies: eligibility/selection changes require replacement, current content, callbacks, paint and visible cue checks; typography/business text changes require complete long-content layout checks. A repair in one state never proves another state's evidence.

## Local accessibility metadata

Actions/options use exact unique natural labels. Only the panel and dynamic text fields use a small static component-local accessibilityIdentifier/testTag map in bindings.*.json. Keys contain no business record IDs and require no global registry. Dynamic text exposes its actual label; no unverified cross-platform native-value mapping is assumed. Preserve separate action/description children. The surface exposes its panel box without merging children away. Actual Button/Compose action nodes expose enabled/selected facts.

## Frozen identity

Public/private contracts, references, fixtures, bridges, API/schema, policy, routes, environments, outcomes, denominator and SVGs are physically separate. Public source documents contain no private data. seal.json records canonical digests; root SEAL.sha256 fixes all five public/private families together before implementation. Hash identity is not semantic approval. An independent format/design reviewer validates compilation and scope before initial code. No expectation or tolerance may be changed after seeing candidate results.


## V2 frozen-tool representation and admission

Business values, fixture/bridge bytes, exact propositions, action stimuli, guards and coverage are unchanged. The reserved explicit state ID initial is renamed start everywhere; this is identity syntax only. Numeric font-weight unit spelling is scalar rather than number, with the same600/400 values. The full shared denominator and explicit platform/state N/A cells remain in denominator.json.

Frozen design_contract has no per-platform N/A syntax. Use ios/contract.json and android/contract.json with their matching lock, plan, policy, routes and environment. Each namespace contains only rules actually applicable to its intended platform. The other platform's expression slot is required only by the frozen parser; it is expressly unapproved for runtime use and proves no measurement on that platform. There is no new iOS computed-font capability or new mandatory iOS unknown. Cross-platform use of a projected lock is forbidden by PROFILE-APPROVAL.json and admit_profile.py. The integration coordinator must run that admission check against actual config paths/hashes before any native acquisition.

The family root reference/denominator/outcomes/API/fixtures/bridges are the canonical shared design; master-contract.json records the complete original rule universe, not a frozen-parser input. Use the two platform namespaces for frozen tools. Their projection-map.json records every original denominator cell, including explicit N/A cells outside the parser's intended rule universe. No cell is silently deleted.

Frozen visual categories are coarse: hierarchy groups visual organization (size, weight, ink/contrast, spacing/inset) while clipping includes visible rounded corner boundaries. Every original primitive rule property, exact question and expected Boolean remains separate and unchanged. This is taxonomy compatibility, not new evidence capability. Native control facts, callbacks, opaque pixel fills and qualitative judgments remain separate.
