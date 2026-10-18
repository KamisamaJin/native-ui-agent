# Pre-registered blinded comparison

Registered before any experimental implementation. A separate fresh-context designer creates the public brief, reference and a sealed oracle. Both implementations start from the same pinned upstream source and common build/capture harness. Only one receives the frozen Skill; neither receives hidden fixtures, prior validation results or the other implementation.

## Sample and scope

- One complex transfer-queue UI requirement implemented in two native platforms (Reply/Compose and AlertToast/SwiftUI), one run per treatment. This is a paired pilot with two task-platform observations, not a statistically powered trial. Multiple cases/criteria within one task are correlated.
- Same inherited model and reasoning settings, fresh context (`fork_turns=none`), no model override. Exact provider model build/seed/token usage is not exposed by the subagent interface; do not invent it or claim seed-level reproducibility.
- Independent designer chooses public requirements and all grading rules before implementation. Six initial fixtures and two repair holdouts test only published requirements. Hidden concrete inputs are sealed by SHA-256 and published after submissions.

## Arms and materials

- Random assignment of opaque workspace labels to with-Skill and without-Skill, sealed before implementation. Builders necessarily know whether they receive Skill instructions; the grader does not know treatment identity.
- Same source revisions, platform versions, public design, data API, native harness, capture capabilities and time limits. Control may render, inspect and write tests; screenshot access is not withheld. Common harness preparation is excluded from treatment elapsed time and reported separately.
- The Skill snapshot is fixed at experiment start; no tuning during the comparison.
- Independent contexts and material/path restrictions provide procedural blinding. All agents share a host/filesystem; this is not a hardened adversarial OS sandbox. Report accidental leaks, protocol deviations, unavailable evidence and this isolation limit explicitly.

## Stages and budgets

1. **D0 implementation:** up to 20 minutes per arm for both platform components, including compile fixes and a public normal capture. Freeze source before inspecting native output for stylistic repairs. Public design can be inspected before implementation.
2. **Self-inspection:** up to 8 minutes. Both arms may render public/self-chosen cases and read images; no production edits. Submit observed issues with published `rule_id`, triggering condition and evidence. Generic speculative risks and unverified items are not detections.
3. **Blind D0 scoring:** coordinator runs sealed initial fixtures and provides anonymized native artifacts to the independent grader. Grade rule-by-case incidences, method and evidence; no source edits. Builders do not see hidden results before both self-inspections are sealed.
4. **Repair:** provide each arm its confirmed D0 failures under the same feedback policy; up to 12 minutes, one repair submission. Hidden examples become visible when feedback includes them; do not claim this phase is still blind to all fixtures. No artificial defects or coaching to favor an arm.
5. **Blind final scoring:** re-run initial plus unrevealed repair holdouts and grade anonymous artifacts. Publish mapping only after ratings are sealed. Report regressions and holdout results separately.

Budgets are maximum wall-clock limits, not fixed token counts. Record actual UTC start/end, elapsed time, native rendering time and external waits separately where observable. Shared hardware/build cache and scheduler contention can confound elapsed time; timing is descriptive, not a causal speed estimate. Completion before a deadline is allowed. A failed build/render is a blocking defect; do not convert unavailable visual criteria to passes or inflate one blocker into many independent defects.

## Metrics fixed before outcomes

- **Confirmed D0 defect incidences:** evaluated case × rule failures, with distinct root-cause/rule categories also reported. Unassessed evidence is separate, not passed.
- **Miss rate:** oracle-confirmed D0 incidences not specifically observed in sealed self-inspection (FN) / all confirmed D0 incidences (TP+FN). The blind grader matches a report's rule and concrete triggering condition to each failure; unsupported risks are not TP. If denominator is zero, report N/A, not 0% detection failure or 100% success.
- **False positives:** specific self-reported defects not supported by the oracle; report counts separately.
- **Repair success:** D0 failed incidences that pass after repair / D0 failed incidences that can be re-evaluated. Report unresolved, unavailable and newly introduced failures separately. Zero denominator is N/A.
- **Final acceptance:** pass/fail/unassessed on initial fixtures and untouched holdouts, per platform and arm. Also report task-level blockers.
- **Elapsed:** implementation, self-inspection and repair wall time, plus observable native execution time. Never substitute screenshot command duration for total developer time.

No significance claim, extrapolated percentage PR-quality improvement, selective removal of inconvenient cases, new hidden requirements or relaxed thresholds after results. Corrections to a broken harness must apply symmetrically, preserve the previous evidence/version and be disclosed. The current Skill is not changed until all outcomes are sealed.
