# Immutable first-D0 clock recovery

V4 fixes a shared controller durability gap found in independent HOST/SIM review
before business source or SDK execution. V3 could retain a complete D0 result and
`request_finished`, stop before `repair_started`, then wrongly use D1's completion
time when publishing the missing source anchor. V4 never derives an anchor from
current time, recovery time, event-publication time, guard startup or D1.

The sole source of the start/deadline is the authenticated **first diagnostic**
result for that exact arm:

* Original request ID, task/arm, source fingerprint and input/tool/readset digest.
* Immutable `result.json` file SHA and its original `finished_at_clock` and
  `finished_at_unix`.
* Exactly all assigned profile outcomes, each pinned by its original file SHA,
  matching the result and preserving passing initial integrity proofs.

The fixed deadline is always that result's original finish time plus 1200 seconds.
Honest terminal failures still qualify under v3; native success is never required
or fabricated. No approval, repair, oracle, tool, resource, queue-cap, platform
guard or frozen default-service semantics change in v4.

## Write-ahead completion authentication

After all profile outcomes have been recorded, the helper appends
`d0_result_prepared` **before** writing the first D0 aggregate. This event pins:

* The exact expected serialized aggregate file SHA and owned result path.
* Per-profile original outcome file paths and SHAs (or an explicit missing-file
  marker, which can never become a valid completion retrospectively).
* Original source and readset digests.

The helper then writes the aggregate using its usual exclusive, flushed immutable
file operation, and appends `request_finished`. Recovery may recreate missing
completion bookkeeping only if the aggregate exactly matches that write-ahead
hash, all originally pinned outcomes match, all assigned profiles are present,
timestamps are finite and consistent with original preparation, and initial
source/readset integrity remains proven. A result is never overwritten, silently
completed, re-collected or retried during recovery.

| Process failure point | Next-boundary behavior |
|---|---|
| Before preparation | No authenticated aggregate; ticket remains pending and source stays locked. |
| Prepared, result absent | No completion or guessed clock; pending/locked. |
| Result truncated or mismatched | Reject recovery; preserve bytes and keep source locked. |
| Complete sealed result, before `request_finished` | Recover the finish event from that exact result, then its original anchor. |
| After finish, before anchor | Publish only the first result's original ID/time/hash-bound anchor. |
| After anchor, before/during guard startup | Validate the existing original anchor; never replace or extend it. |

## Recovery before action

Every state boundary runs deadline recovery before queueing, serving, source
acknowledgement/unlock, review/admission, final sealing or hidden authorization;
the status command also performs it. Existing anchors are checked against the
same first-result proof at foreground boundaries. The watchdog uses its already
validated event cache for stable existing anchors and continues enforcing their
fixed deadlines.

A recovered anchor explicitly retains `d0_request_id`, `d0_result` path/SHA,
original finish times, source/readset digests and fixed deadlines. Its event may
be published later; publication is not a new start. If recovery occurs after the
original 1200 seconds, source is frozen immediately **before** queue/unlock can
continue. A discontinuity where the kernel clock precedes the original finish
also freezes conservatively. A missing or corrupted proof does not authorize a
replacement clock; owned source permissions are protected and the action rejects.

D1 may have been legitimately queued within the original window. It can collect
read-only outcomes later at the frozen bytes, but cannot create, replace or reset
the first-D0 anchor. Inactive arms acquire no anchor. All original results,
failures, partial artifacts, immutable source capsules and predecessor freezes
remain retained.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B test_blind_study.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_domain_admission.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_terminal_d0.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_anchor_recovery.py
```

The first three suites are copied unchanged from v3. The focused cut matrix
covers preparation, result persistence, finish publication, anchor publication,
guard startup, the independently reproduced D1 extension, correct remaining time
within the original window, immediate expiry after it, truncated/tampered proof,
missing outcome integrity and inconsistent existing anchors. All data and service
calls are synthetic HOST/SIM; subprocess/SDK/native forwarding is forbidden.
This change is shared study-controller correctness, not a new treatment benefit.
