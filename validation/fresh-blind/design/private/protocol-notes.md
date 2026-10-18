# Private protocol notes — freeze before implementation

This file and oracle.json contain evaluation inputs and must not be supplied to implementers. The brief contains every acceptance requirement; private files add concrete values and expected outcomes, not new requirements. No previous implementation, README, skill, report, assignment, or experimental outcome was read while designing this component. Only the expressly allowed upstream Package.swift was inspected to establish Apple deployment compatibility.

The public sample is not an evaluation case. Exactly initial_01–initial_06 are initial fixtures; exactly repair_holdout_01–repair_holdout_02 are repair holdout fixtures. The two complete update models inside repair_holdout_01 are steps of that case, not extra evaluation fixtures. Keep concrete holdout values hidden during repair.

## Execution and evidence

Run each fixture through actual production components. Apple: real iOS app plus XCUITest native accessibility/actions. Android: existing Compose Paparazzi semantics/actions/render host. Fixture bridge, reducer, event trace and host IDs remain outside production. Verify iOS14/macOS11 compatibility separately through compilation/source inspection: a current iOS runtime alone does not prove macOS11 compatibility.

Host supplies width320/390, horizontal16/top24 margins, resulting panel width288/358, parent vertical viewport600, theme/font/direction. Exclude host IDs beginning __observer from product judgments. Requested fontScale1.8/2.0 maps to the nearest supported native accessibility category on Apple. Record the actual category/effective setting. Native line breaks and accumulated heights are not required to match across systems. Full wrapping, readability, information preservation and action reachability are required.

At checkpoints save screenshot, actual native tree/Compose semantics where supported, model identifier, events and action result. Inspect long content through scroll progression, not only its footer. scroll_until is an instruction to use ordinary parent gestures until the target becomes reachable; it does not authorize handler invocation, artificial helper controls or direct movement of production layout. Save initial, middle and footer views for long cases; allow extra ordinary scroll gestures.

A native disabled control can reject activation. Its observed disabled semantics plus rejected activation and unchanged event log can establish the negative-action requirement. A script failure before activation is missing action evidence. A missing expected element is a product failure only when successful evidence capture establishes its absence, rather than an acquisition failure. Do not use screenshots to claim native state or source annotations to claim actual accessibility exposure.

The caller echoes select/fee actions. Changed selection clears feeAccepted; same selection is a no-op. A confirm/retry/done event only records the event. Do not change mode automatically. Complete fixture updates replace the model through the same component instance. If the bridge echo fails, distinguish that host defect from the production view and retest if possible.

The oracle's applicableRuleIds defines the case×rule denominator. Source-only checks, especially R01, are reported separately, not multiplied across runtime cases. Check methods list possible evidence channels; unsupported channels must be labeled missing. If another adequate channel proves a narrow assertion, describe precisely what was established without claiming the unavailable channel. Reuse a verified screenshot only for properties it can actually show. Keep source declarations, actual AX/semantics, action/callback traces, caller-update evidence and screenshots distinct.

## Blinding and reports

Later grading uses treatment-neutral artifact labels. Do not inspect treatment assignments, prompts, agent identities, other implementations or previous reports. Do not infer a treatment from coding style. Grade each anonymous platform artifact against this frozen brief/oracle before comparing labels.

Report initial and holdout phases separately, and each platform separately before aggregation. Per platform, initial denominator59 case×rule pairs and holdout denominator25. Each pair is one unit even when several checkpoints exercise it. Any adequately observed required-checkpoint failure fails that pair; preserve all supported manifestations. Report pass/fail/unobserved, observed denominator, and source-check results separately. Do not enlarge a denominator with unrelated branch rules.

Report defect/root-cause clusters separately from case×rule counts. Multiple manifestations of one demonstrated implementation cause count as one cluster. A detailed observation of a shared cause may count as cluster detection without pretending every affected rule was explicitly reported. Exact-rule attribution requires explicit supported identification of that rule's violation. Keep root-cause detection and rule-attribution completeness as separate outcomes.

Possible finding families (not presumed defects): mode/content branching; controlled selection derivation; fee/confirmation gating; native action/accessibility exposure; adaptive type/parent scrolling; palette/hierarchy/direction; API/deployment integration. Split or combine only on demonstrated causes. A reused conditional can create one cluster across many rules; unrelated inaccessible controls and clipping constraints need not be merged just because they affect one case.

Use the public anchored visual1–5 rubric per case/platform with screenshots and brief rationale. Missing screenshot is unscored, never automatically1. A callback-only defect does not reduce a supported visual score unless a visible consequence also meets the rubric. Label missing evidence explicitly in the final report.

## Freeze

The four artifacts are frozen when SHA256 values are sent to the coordinator. Do not edit the brief, reference, oracle or these notes after implementations begin. Document later ambiguities outside this directory as protocol deviations, using the existing public requirements and conservative unobserved labeling. Never alter expectations to fit a treatment.
