# Neutral replay003: preserved production snapshot

The original ten-case specification and oracle remain unchanged. The new snapshot
again yields **7 passing cases and 3 failing cases**, now with **four unmet oracle
fields**, down from five. The source bytes used for this run are copied to
`production-snapshot-003/` and sealed before execution in `source-seal-003.json`.
The native subprocess transport is synthetic; no real SDK execution or empirical
native calibration is claimed.

## Changes established by the new snapshot

- The same bound unknown image review, without a new review head, returns
  `awaiting_review`, `awaiting_review`, then
  `blocked_repeated_unchanged_evidence`. It adds zero native calls after setup.
- The same calibrated measurement task returns `awaiting_measurement`,
  `awaiting_measurement`, then the same blocked status. C08's
  `calibration_bounded` now passes. Its only remaining oracle failure is the
  two unequal-to66 values described below.
- Native acquisition remains bounded: two synthetic native invocations, then
  a blocked third cycle. Original incomplete evidence and the six unknown cells
  remain retained.
- A target-only scope that has finished its selected work now says
  `awaiting_full_final`, with `delivery_complete:false`,
  `full_coverage_pending:true`, and `full_final_required:true`. Explicit fresh
  full final plus bound image completion still returns accepted.
- Calibration guard controls now reject an external unproved AX leaf as
  `outside_calibrated_scope`; an exact pinned synthetic probe row can receive an
  interval classification; changing the runtime identity-transform metadata
  causes `fit` to return `unsupported_or_incomplete`. These are schema/scope
  integration controls, all synthetic, not empirical provider validation.

The actual additional controls are saved in
`replay-003/C08_calibration/scope-guard-controls.json`,
`replay-003/C08_calibration/calibration-retry-statuses.json`, and
`replay-003/C10_bounded_retry/retry-summary.json`.

## Remaining strict oracle failures

**C06 — automatic full scheduling:** the oracle expects a missing full sweep to
be queued automatically. Actual non-final dispatch has `states:[]` and
`requires_fresh_capture:false` while explicitly saying `awaiting_full_final`.
The gate prevents incomplete delivery; the integration must invoke its final
close path. This is a stronger scheduling expectation than the API implements,
not an observed acceptance bypass. The original oracle stays failed on
`missing_full_sweep_scheduled`.

**C08 — all samples fail an exact equality:** the original two source widths are
65.99999999999999 and66.00000000000001pt in one epoch, against exact66pt. Each is
strictly unequal, so the actual evaluator retains a failed result. The sealed
oracle conservatively expected unknown for distinct within-state values even
when both comparisons fail. This is a contract interpretation difference: a
failure is robust under choosing either observed value, while instability still
limits product-cause attribution. The failed comparison does not establish a
confirmed product bug; the report does not label it one. No rounding, threshold
edit, calibration waiver, or rewritten original is requested or performed. The
minimal original-source samples and expected66/actual failed report remain in
`minimal-conflict/`; current snapshot reproduces the same arithmetic.

**C10 — newly registered review actuals reset the same-work budget:** the sealed
oracle fixes at most three total attempts per work item. The primary replay
submits four separate honest-unknown review records, each retaining its
predecessor through explicit correction. Each new registered review SHA changes
the cycle signature, so all four return `awaiting_review`. Both oracle fields
`max_attempts_per_work_item` (actual4) and `stops_after_exhaustion` (actual false)
remain failed. The new unchanged-review control does stop on cycle3. Thus the
remaining difference is a global per-work-item budget versus an unchanged-
evidence budget, not unbounded unchanged dispatch or unbounded native execution.
Every attempt remains unknown; no passing coverage or acceptance is obtained.

## Replay and interpretation limits

```sh
NEUTRAL_PROBE_SCRIPTS=/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/routed-forward/probe-review/production-snapshot-003 \
  python3 -B validation/routed-forward/probe-review/replay003-adapter.py \
  --output /absolute/path/to/a-new-replay-directory
```

The adapter calls actual public APIs and patches only the subprocess transport.
Every generated packet/image is disclosed as synthetic. The original design
seal is checked at startup. Output directories must be fresh. `results.json`
contains the original oracle's exact expected/actual fields, with no exceptions
or omitted cases. Production modules are imported from the preserved source
snapshot, so later production edits cannot change this replay's code.

The new adapter translates the same sealed fixture and preserves all numeric
thresholds, input/action indices, and six required cells. The calibration fit
control supplies the current public API's explicit context and identity metadata;
its values are synthetic and its provenance states that. It does not assert that
the folded-paper production SwiftUI view has a proved UIKit leaf identity.

C02 intentionally flips an actual from false to true on the same original image
as a scheduling mutation control. The tool validates the binding and consumes
the submitted actual; this does not certify that the second visual opinion is
correct. C09's independent overlap schematic, wrong label, and undersize packet
provide the separate real contradiction controls within the synthetic fixture.

Actual SDK calibration remains **unexecuted**. A runnable real native host/bridge,
test-discovery receipt, original runtime packets, and provider/environment
provenance are required to perform that stage. Neither the passing integration
controls nor the seven-case score substitutes for it.

Historical runs001/002, their original failures, the old adapter copy, and the
historical report are transitively sealed by `seal-runs-001-002.json`. They were
not rewritten after seeing the new snapshot. No production file, sealed design,
oracle expected value, or baseline was changed by this evaluation pass.
