# Reproduce the published evaluation

The repository contains sealed raw observations, original PNGs, generated hosts,
test/build logs, command records, original and final production sources, independent
designs, original self-check plans, original reviews and all graded dispositions.
Native build caches and xcresult bundles are omitted; portable manifests attest the
retained artifacts. Original failed attempts are not replaced by successful reruns.

From the repository root, Python3.11 and the pinned Python requirements suffice for
the SDK-free audit:

```sh
python -m pip install -r native-ui-agent/scripts/requirements.txt
python -B -m unittest discover -s native-ui-agent/tests -v
python -B validation/multitask-forward/verify_tools.py
python -B validation/multitask-forward/verify_generic.py
python -B validation/multitask-forward/design-v2/T1/private/test_grader.py
python -B validation/multitask-forward/design-v2/T2/private/test_grader.py
python -B validation/multitask-forward/design-v2/T3/private/test_grader.py
python -B validation/multitask-forward/verify_trial.py
python -B validation/multitask-forward/verify_evaluation.py
python -B validation/multitask-forward/verify_claims.py
python -B validation/multitask-forward/test_metrics.py
python -B validation/multitask-forward/metrics.py
python -B validation/multitask-forward/quality_breakdown.py
python -B validation/multitask-forward/pair_metrics.py
python -B validation/multitask-forward/costs.py
python -B validation/multitask-forward/observation_costs.py
python -B validation/multitask-forward/failure_index.py
python -B validation/multitask-forward/build_tables.py
python -B validation/multitask-forward/test_shared_environment.py
python -B validation/multitask-forward/supplement.py verify
python -B validation/multitask-forward/supplement.py metrics
python -B validation/multitask-forward/build_supplement_tables.py
python -B validation/multitask-forward/review_product_summary.py
python -B validation/multitask-forward/implementation_comparison.py
python -B validation/multitask-forward/audit_grader_disagreements.py
python -B validation/multitask-forward/build_gallery.py
python -B validation/multitask-forward/artifacts.py
```

These commands verify existing scores and outputs; they do not regenerate them.
The accepted design denominator, locked expectations and tolerances are immutable.
Old v6 publication checks run through the byte-exact contract-v6 publication alias
in CI. A changed live release must not be used to rewrite an old trial's manifest.

`prospective-seal.json` and the whole-cohort registry establish ordering. `design/`
contains the original proposal rejected for insufficient interaction diversity
before implementation; `DESIGN-ROOT.json` selects accepted `design-v2/`. Each
accepted task contains the approved public brief/API/references/contract and
private heldout stimulus/oracle/table. The full assignment is disclosed only in
the post-grading release record.

`submissions/<unit>/d0` and `final` are production source capsules. Their sibling
original plans and reviews are never repaired after the fact. `own-corpora/` is the
candidate's own public feedback; `common-corpora/` is anonymous independent
acceptance. `evaluation/D0`, `FINAL`, `selfreview`, `paired-D0` are separately sealed
grading stages. `paired-corpora/` contains actual old-collector sessions on the same
D0 sources. `precision-replay/` is an additional zero-SDK same-frame checker
diagnostic, not an additional development experiment.

A fresh native reproduction requires macOS/Xcode, an installed simulator runtime,
JDK21 and the Android SDK, plus upstream checkouts at the pinned Reply/AlertToast
commits. The original absolute command arguments are retained as provenance;
SDK-free verifiers relocate trial paths to the current checkout. Create a NEW trial
directory/registry and new simulator IDs for a fresh experiment. Do not rerun the
publication's write-once batch commands in this directory or replace its screenshots,
expectations, timings or seals. Repeating with new SDK/runtime versions produces a
new acquisition, not a byte-identical historical reproduction.

Read the costs as observed wall time and resource work on a shared Mac. Two native
unit slots, cache/order effects, all-six barriers and overlapped audit acquisition
are included. Token/money costs were not exposed and are not estimated. AI review
is independently scoped but does not substitute for human-labelled ground truth.

The original primary independent oracle rejected Compose `Ltr` because its fixture
used `ltr`. Those input failures and Android U cells are retained. A separately
sealed posthoc adapter and same-source rescore live in `shared-environment-v1/` and
`supplement/`; they use original native observations and do not rerun or repair any
product. The reusable provider-explicit adapter is `tools/native_environment.py`.
Its real-native wire regression checks are SDK-free. Supplemental task results are
sealed before assignment release, and its separate metrics/costs never count as a
v7 treatment benefit. Read `shared-environment-v1/PROTOCOL.md` for the exact scope.
