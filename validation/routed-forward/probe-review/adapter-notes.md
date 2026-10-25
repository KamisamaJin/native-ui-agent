# Transparent replay adapter

The pre-inspection specification in `../probe-design` is immutable. This adapter
imports current production modules and calls public functions. It does not modify
production scripts, patch planners/evaluators/review logic, or use other studies.

Only `execution_plan.subprocess.run` is replaced during synthetic acquisition.
The replacement reads the actual generated launch inputs and writes synthetic
native packets plus copies of the sealed schematic PNGs. The real execution
compiler, capture receipt generation, source fingerprinting, native evaluator,
environment checker, review catalog, review binding/reconstruction/registry,
default cycle, work dispatch, and completion functions run normally. Every
synthetic transport invocation is logged. None is a real SDK test or calibration.

Schema translation preserves the sealed request: its single indexed
`replace_fixture(index=1)` becomes the production observer's `apply_next_fixture`
with exactly one caller update. The sealed front/reverse input/action indices,
rule IDs, expectations, zero tolerance, and six-cell denominator are unchanged.
The compiled typed reference, route index, policy, launch approval and environment
are generated from the sealed fixture in each isolated lab. The launch bridge is
a synthetic-only capsule, not a runnable native integration. No generated native
packet is represented as genuine native evidence.

Semantic normalization maps `review_images` to `image_review`, `acquire_native`
to SDK acquisition, and `accepted` to completion. Queue IDs come from actual
dispatch/review-request outputs; failed IDs come from actual recomputed reports.
Method names in C09 come from assertion kind plus actual evaluator evidence:
native control/AX, native geometry, and bound visual decision. A field that is
not established by the exercised API remains absent or carries its actual
value, so the original oracle rejects it. Observed raw outputs remain available.

`complete_review` requires a prior fresh full final cycle. Final-cycle setup
acquisition is counted separately from the zero-acquisition image completion
window tested in C01/C03. Historical failed image actuals may guide repair after
source edits; they must not establish current acceptance. C06 explicitly tests
both non-final targeted dispatch and a fresh full final completion.

Run with `python3 -B validation/routed-forward/probe-review/replay.py --output DIR`.
DIR must be new. The replay verifies the original specification seal first.
