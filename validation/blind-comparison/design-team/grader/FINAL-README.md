# FINAL stage preparation

No FINAL native packet has been inspected. These templates contain no FINAL scores. Frozen design/oracle, D0 seals and detection-matching seal are protected by exact SHA-256 fingerprints and are never rewritten by this helper.

Each anonymous FINAL template contains all six initial and both existing repair-holdout fixtures, on both platforms: 16 cases × 23 rules = 368 incidences. The frozen oracle supplies every fixture and rule; no requirement is added. There is one `repair_reassessment` entry for each previously failed D0 case×rule, with every original failed aspect copied from the D0 seal.

```sh
python3 final-grading-helper.py init --anonymous-id submission-06e6f6 --out /absolute/design-team/grader/another-FINAL-record.json
python3 final-grading-helper.py validate /absolute/design-team/grader/FINAL-record.json
python3 final-grading-helper.py derive-new-failures /absolute/design-team/grader/FINAL-record.json
python3 final-grading-helper.py summarize /absolute/design-team/grader/FINAL-record.json
python3 final-grading-helper.py seal /absolute/design-team/grader/FINAL-record.json --out /absolute/design-team/grader/FINAL-sealed.json
```

Replace the example paths with this grader directory's real absolute path. Writes are exclusive. The helper opens no native packet path or evidence file; later packet review remains a separate authorized step. It reads only the frozen design and existing grader artifacts plus explicit grader record inputs.

For `repair_reassessment`, retain every old aspect ID, observation, method and evidence description. Record the new native evidence in that aspect's FINAL `status`, `method`, `execution`, `evidence`, and `observation` fields, and mirror that result in the same aspect of the whole-rule matrix. The entry-level status is `failed` if an old failing aspect is observed still failing; `passed` only when **all** old failing aspects are observed passing; otherwise `not_assessed`. Missing old evidence cannot be repaired by source inspection. For the existing rendered D0 failures, an actual FINAL native image/visual observation is required. D0/self-review screenshots are baseline references, not FINAL evidence.

The whole-rule matrix is independent. An old aspect can be repaired while the rule remains partly unassessed or fails for a new aspect. Conversely, one observed old success cannot cover another old failure or missing observation. Preserve `coverage_complete`, partial coverage, missing branches, per-aspect methods, build/render blockers, and the 1–5 native visual rubric.

Use `derived_new_failures` (or the CLI's printed data) to populate two separate arrays: newly failed **incidences** absent from the D0 failed set, and newly failed **aspects**, including new failures inside a previously failing rule. A holdout failure is newly observed; a defect is a proven newly introduced regression only when the same aspect had an observed passing D0 baseline. The helper does not infer regressions from missing D0 evidence.

Real callback execution still requires native events and recorded actual/expected callback arrays. Source review cannot pass a runtime callback, hit test, or accessibility traversal. The known empty iOS AX export remains a host evidence limitation. Content outside the available viewport without a lower capture remains `not_assessed`; it is neither automatic clipping nor a passing visual check.

FINAL sealing requires actual review timestamps, source hashes/revision from the new anonymous manifest, an explicit FINAL packet root, and an artifact role of `FINAL_rating`. The treatment mapping remains hidden. The separate prior self-review matching phase is truthfully recorded as already seen; it does not modify the sealed D0 baseline.
