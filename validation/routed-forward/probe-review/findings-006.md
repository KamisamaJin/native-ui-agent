# Frozen candidate: final independent neutral replay006

**Result:9 of the original10 cases pass.** The only remaining mismatch is the
unchanged C08 oracle's unknown expectation versus the actual robust strict
failure for two samples that are both unequal to66pt. The oracle, thresholds,
baseline, and historical results were not changed. No additional controller
issue was observed within this synthetic integration scope.

The exact21 Python source files used are preserved in
`production-snapshot-006/`, with pre-execution manifest `source-seal-006.json`
(SHA256 `0cf9da888d0c3c06dec61f4365bc841d61dba4cc2f4bd57bbbf22e603157664d`).
`replay006-adapter.py` is the exact adapter used. The final seal records whether
live production still equals this snapshot at sealing time.

The full expected/actual outcome is `replay-006/results.json`. The principal
controls confirm:

- C06 targeted review completion schedules both states. A non-final default
  cycle actually invokes the synthetic native transport once with full scope
  and queues both original state images for review. It does not claim delivery
  before full final evidence and image completion.
- C10's repeated same unknown, including newly registered review heads, returns
  two waiting cycles then a blocked third cycle. Same-head image review,
  measurement-only tasks, and repeated incomplete native acquisition are also
  bounded. Required unresolved cells and all attempts remain retained.
- The U→F outcome-progress control changes the signature despite retaining the
  same assertion ID. Actual progress permits a fresh pair of F-state cycles,
  followed by blocking. It does not launch the SDK again.
- C01–C05 and C07/C09 continue to confirm image/native work routing, actual review
  import and discovery, queued completion, stale-evidence rejection, malformed
  report rejection, strict metrology, genuine synthetic contradictions, and
  separation of visual approval from exact native measurements.

The direct artifacts are
`replay-006/C06_targeted_full/automatic-full-control.json`,
`replay-006/C10_bounded_retry/retry-summary.json`,
`replay-006/C08_calibration/calibration-retry-statuses.json`, and
`replay-006/C08_calibration/outcome-progress-control.json`.

Snapshot006 additionally requires explicit native `pt` units and the actual
identity transform matrix. The older synthetic fit inputs in this adapter lack
that matrix; the API correctly returns `unsupported_or_incomplete` and both
external/pinned classification attempts remain `outside_calibrated_scope`.
This is honest rejection of incomplete synthetic metadata, not a demonstrated
failure to classify a fully valid native calibration. No claim of a successful
positive empirical calibration is made. The raw scope controls remain in
`replay-006/C08_calibration/scope-guard-controls.json`.

The C08 mismatch retains widths65.99999999999999 and66.00000000000001pt versus
exact66pt at tolerance0. Each comparison strictly fails; the actual evaluator
keeps failed, and calibration preserves that raw status. The original oracle
required unknown for distinct within-state values. This difference is reported
without converting the strict failure into a confirmed product cause, rounding
it to pass, or requesting a change merely to satisfy the oracle. Original source
samples and the minimal counterexample remain available under `minimal-conflict/`.

Reproduce with a new output directory:

```sh
NEUTRAL_PROBE_SCRIPTS=/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/routed-forward/probe-review/production-snapshot-006 \
  python3 -B validation/routed-forward/probe-review/replay006-adapter.py \
  --output /absolute/path/to/a-new-replay-directory
```

Only the native subprocess transport is mocked; public capture/evaluation,
source fingerprints, binding/reconstruction/registry, dispatch, default cycle,
and final completion APIs execute normally from the preserved snapshot. All
transport packets and screenshots are synthetic. The schematic's C02 opinion
polarity flip is an import/scheduling control, not a correctness claim about
visual reviewers.

Actual SDK calibration remains **unexecuted by this independent evaluator**.
Real native host integration, test-discovery receipts, original runtime packets,
provider identity, and environment provenance are required for that separate
stage. The9/10 result supports the inspected routing/integrity/coverage/retry
scope with its explicit C08 semantic difference; it does not substitute for
native runtime or empirical calibration evidence. No production tool was edited
by this pass, and no business fixture was consulted.
