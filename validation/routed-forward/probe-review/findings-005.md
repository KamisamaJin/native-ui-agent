# Final neutral replay of source snapshot004

The unchanged pre-inspection oracle now reports **9/10 cases passing**. Only
C08's `conflicting_status` field remains different: expected unknown, actual
strict failure. No new issue was observed in the exercised synthetic controller
scope. All earlier output directories and sealed originals remain unchanged.

`replay-004` is the first replay of this source snapshot. `replay-005` adds two
direct integration controls while retaining the same ten cases and expectations.
Both runs produce9 passes and the same single oracle discrepancy. The exact21
production Python files were copied to `production-snapshot-004/` and sealed
before either run in `source-seal-004.json`.

## Directly observed behavior

**Automatic targeted→full completion:** in C06, after its reverse-only capture
and bound review finish, planning schedules both states. The additional non-final
call actually executes one new native transport invocation without `final=True`:

```json
{
  "final_requested": false,
  "native_executed": true,
  "new_transport_calls": 1,
  "selected_states": ["front", "reverse"],
  "scope": "full",
  "queued_visual_ids": ["front/caption-clear", "reverse/caption-clear"],
  "status": "awaiting_review"
}
```

This output is saved in
`replay-005/C06_targeted_full/automatic-full-control.json`. Earlier while the
selected reverse image still needs review, its target capture's after-dispatch
retains that review work and does not prematurely schedule the full sweep.
The six-cell denominator and the reverse sample-box regression obligation remain
intact. Full-final acceptance continues to require fresh full native evidence
and completion of the exact current images.

**Bounded identical outcomes despite new review heads:** C10 submits a new
registered honest-unknown review after each attempt. The statuses are now
`awaiting_review`, `awaiting_review`, then
`blocked_repeated_unchanged_evidence`, with zero new native calls after setup.
The same-head control also stops on its third cycle. Repeated acquisition still
uses two synthetic native calls and blocks the third cycle. Measurement-only
work likewise stops at its third cycle. All attempts and unresolved cells remain
saved; no current pass or completion is inferred from exhaustion.

The primary retry loop now stops when the API returns blocked. This is an
adapter stop-condition correction, not an oracle change. Earlier implementations
never returned blocked for the newly registered unknown-review sequence, so the
historical four-attempt observations remain accurate and preserved. The latest
runner does not force a fourth attempt after receiving the required stop.

**Actual progress distinguishes U from F:** the additional control starts with
an unknown overlap review, then imports a bound negative actual for that same
assertion ID. Its statuses are:

```text
awaiting_review
awaiting_source_repair
awaiting_source_repair
blocked_repeated_unchanged_evidence
```

The U→F transition changes the actual signature even though the issue ID is
unchanged; it permits two subsequent F-state cycles before stopping. There are
zero added native calls. The final failed cell is exactly
`reverse/caption-clear`. This control is saved under
`replay-005/C08_calibration/outcome-progress-control.json`.

The prior passing controls also remain passing: image/SDK work routing, actual
bound review import and automatic discovery, out-of-order queued completion,
source/input/image/action invalidation, ten malformed-report variants, strict
native arithmetic and real undersize, mixed native/visual failures, unsupported
layout unknowns, and final acceptance guards.

## Single preserved oracle discrepancy

C08 retains two source widths in one state:
65.99999999999999 and66.00000000000001pt, compared with exact66pt at tolerance0.
Both individual comparisons fail. The actual evaluator therefore returns failed,
which is robust under choosing either observed sample. The sealed oracle chose a
more conservative unknown for any distinct within-state values. Its exact
expected/actual mismatch remains in `replay-005/results.json`; the oracle was
not amended to improve the score.

This discrepancy does not justify rounding either sample, loosening the design,
or calling the raw strict failure a confirmed product bug. The calibration
annotation preserves the original status and does not establish product cause.
The minimal packet and source-sample counterexample remain in `minimal-conflict/`.
No production change is requested merely to suppress this retained F.

The current calibration guard continues to return `outside_calibrated_scope`
for an external unproved AX leaf, rejects mismatched identity-transform metadata
at fit time, and permits interval classification only for its exact pinned probe
control. These are synthetic schema/scope observations, not proof of a real
UIKit object's identity or calibration quality.

## Reproduce and limits

```sh
NEUTRAL_PROBE_SCRIPTS=/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/routed-forward/probe-review/production-snapshot-004 \
  python3 -B validation/routed-forward/probe-review/replay005-adapter.py \
  --output /absolute/path/to/a-new-replay-directory
```

The source snapshot is immutable and the original design seal is checked on
startup. The runner patches only the native subprocess transport; all public
compiler, capture, evaluation, binding/reconstruction/registry, dispatch, cycle,
and final-review completion functions execute from the preserved production
snapshot. Every native packet/image transport is synthetic. Existing directories
must not be reused.

Actual SDK calibration remains **unexecuted by this evaluator**. Runnable native
integration, discovered native tests, real original packets/screenshots, and
provider/environment provenance are required for that separate stage. C02's
opinion polarity change remains a scheduling control, not a claim that a visual
reviewer made a correct correction on unchanged pixels. No test here proves
source-to-native rendering fidelity or human visual judgment quality.

The result supports the inspected controller's routing/integrity/coverage/retry
release scope, with the documented C08 interpretation difference retained.
It does not replace the separate actual native calibration stage. No production
file, sealed fixture, threshold, baseline, or oracle was changed by this pass.
