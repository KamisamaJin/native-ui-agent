# T4 — Service outage notice composer

PRIVATE — embargoed until ALL10 final production-source/selfclaim seals. No implementation/repair worker may read this directory earlier.

Deliver `OutageNoticePanel`, a reusable additive AlertToast public SwiftUI View and Reply production Compose component. Use the exact typed API in API.md. Caller data is immutable; production owns actual UI decisions, state, and replacement transitions. `onEvent(String)` forwards local request payloads only.

## Business rules

1. Begin with no audience, troubleshooting off, no preview, no wording review. Audiences are single selection and enabled only when allowed and recipients > 0. Show zero-recipient and blocked audiences; keep their descriptive reasons readable.
2. Include troubleshooting steps is enabled only for a nonempty workaround. An actual audience or troubleshooting change invalidates the preview and wording review. Preview notice is enabled when an allowed audience is selected and creates the exact deterministic preview: 'Subject: {subject}\nAudience: {audience label} ({recipients})\n{message}', appending '\nWorkaround: {workaround}' only when troubleshooting is on. Previewing again clears wording review.
3. Before a preview exists, its content is absent and Customer wording reviewed is disabled/off. Publish notice requires a current preview and wording review. The preview remains visible after publication.
4. Publish emits exactly one 'publish|{entityId}|{audienceId}|{current recipient integer}|steps:{on or off}', then locks all controls. Preview and decision actions emit zero events. This is a local publication request, not an actual outbound message.
5. Same-entity replacement preserves the audience only if still allowed with positive recipients, preserves troubleshooting only if a nonempty workaround remains, and always clears preview, review, and recorded state. Changed entityId clears every decision. Replacement emits nothing.
6. Summary is '{selected audience label} · {count} recipients' or 'No audience selected', followed by ' · Steps included'/' · Steps omitted'. Exact status/preview content is part of the public outcomes; no recovery time, delivery channel, or other text is invented.

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
