# Anonymous D0 grading preparation

This directory contains preparation only. No anonymous implementation packet has been read or graded. Existing public/private design bytes remain unchanged. The visual reviewer is an independent AI, not a human expert.

`grading-template.json` has 12 platform cases × 23 public rules = 276 incidences for one placeholder anonymous implementation. Every incidence starts `not_assessed` with no evidence, finding, or rating. Copy/init one record per anonymous implementation after the native packets arrive. The helper opens no evidence paths and does not inspect any builder, assignment, Skill, report, or sibling conversation.

```sh
python3 grading-helper.py init --anonymous-id ANON --out /absolute/design-team/grader/ANON-D0.json
python3 grading-helper.py validate /absolute/design-team/grader/ANON-D0.json
python3 grading-helper.py summarize /absolute/design-team/grader/ANON-D0.json
python3 grading-helper.py seal /absolute/design-team/grader/ANON-D0.json --out /absolute/design-team/grader/ANON-D0-sealed.json
```

Use the real absolute directory for the examples above. `init` and `seal` refuse to overwrite existing files. All record paths must be inside this grader directory. The helper reads the frozen design files only to load public rules and record/verify SHA-256 fingerprints; it does not alter them.

For each rule incidence, add separate check records for the relevant public branches, record actual method and evidence path, and write a concrete observation. `coverage_complete` means all applicable required branches are evidenced; it is never inferred from a successful subset. `coverage` is `none`, `partial`, or `complete`. Use the helper's `aggregate_incidence` policy: an observed failure fails the rule, but successful partial checks cannot make the whole rule pass. If no sufficient artifact exists, use `not_assessed`; if an action was not run, use `not_executed`; if an artifact cannot establish a valid measurement, use `unscorable`. Preserve build/render blockers separately and mark dependent checks `blocked` only with an actual blocker. A case below a parent scroll viewport without a lower capture is missing evidence, not automatically clipped by the component.

Callback checks use `scope: runtime_callback`. Passing requires an actual native activation, `native_semantics` event evidence, `execution: observed`, and identical `actual_callback_events` / `expected_callback_events` arrays. Static source wiring may reveal a conclusive defect under a separate `static_contract` check. It cannot establish a successful executed tap. Informational-area inertness requires a real coordinate tap outside buttons to pass.

The common iOS host has no usable AX export even for its control probe. Empty AX is never a component defect. Review A11Y declarations via explicit `source_review` records and retain missing runtime accessibility as `not_assessed`. iOS callbacks without actual UI events remain `not_executed`. Native iOS PNG/OCR can still establish visible strings and visual findings. Android has real unmerged semantics and executable native OnClick; actual artifacts, not platform capability alone, establish each check's result.

For TQ-VIS-01 and TQ-VIS-02, supply `visual_rating: {score: 1..5, specific_observation: "...", evidence: ["..."]}` only after reviewing native images. Frozen anchors are included in the template. Keep visual quality separate from rule conformance, evidence coverage, and build/render blockers. Do not infer a visual score from absent evidence or from source appearance.

Before D0 sealing, record the frozen anonymous revision and review timestamps, change `artifact_role` to `D0_rating`, and explicitly set `sealed_before_self_review_matching: true`. All blindness declarations must remain false. The seal command writes an exclusive snapshot and SHA-256 sidecar. It does not accept self-review content. Only after this seal may a later, separate detection-matching step see self-review claims; it must not rewrite D0 findings or scores. Treatment mapping stays hidden.
