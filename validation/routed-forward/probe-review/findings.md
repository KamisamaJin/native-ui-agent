# Independent neutral forward replay

The sealed ten-case oracle was not changed. Both retained runs finish with
**7 passing cases and 3 failing cases** (five unmet oracle fields). The second
run strengthens the first adapter's direct observations without changing the
result. `replay-001` retains the original failures; `replay-002/results.json` is
the definitive strengthened replay. No production file was edited by this pass.

All acquisition was synthetic. Only the subprocess native transport was mocked;
the actual execution compiler/receipt generation, native checks, environment
checks, review catalog/bind/registry/reconstruct, default cycle, dispatch, and
final image completion APIs ran. This establishes controller integration behavior
for supplied packets, not real native execution, rendered production output,
independent human visual accuracy, or empirical SDK calibration.

| Sealed case | Result | Actual behavior |
|---|---|---|
| C01 review routing | Pass | One missing reverse visual judgment produced `review_images`; no new native invocation. |
| C02 actual import | Pass | Bound `actual:false` became exactly one reverse visual failure and repair state. A registered explicit correction changed the subsequent plan and retained the original. |
| C03 queued completion | Pass | Reverse-first completion kept front pending. Explicit unknown kept it pending. Both valid reviews completed the existing full final capture with zero additional native invocations. |
| C04 stale identity | Pass | Source change required fresh work; input, image, and action-byte drift were rejected. Original capture archives were retained. |
| C05 report integrity | Pass | All ten fixed malformed/tampered variants were rejected, with zero coverage credit or product-failure conversion. |
| C06 targeted→full | **Fail, one field** | Six-cell ledger and full-final delivery gate were correct; non-final dispatch did not automatically schedule its remaining full sweep. |
| C07 strict metrology | Pass | Exact iOS/Android samples passed; real undersize failed; malformed samples and unavailable/cross-frame relations stayed unknown; thresholds stayed66/0. |
| C08 calibration | **Fail, two fields** | Original strict status and threshold were preserved, but distinct same-state off-target samples collapsed to failed, and a measurement queue remained dispatchable four times. |
| C09 mixed methods | Pass | Actual wrong label, real undersize, and bound overlap became three reverse-only failed cells; unsupported layout remained unknown. A separate positive visual review did not erase native undersize. |
| C10 bounded retry | **Fail, two fields** | Repeated native acquisition was bounded; review-only unknown tasks remained dispatchable four times without a stop. |

## F1: targeted feedback completion leaves explicit full-sweep debt

Reproduce using `replay.py` and inspect
`replay-002/C06_targeted_full/targeted-reviewed/retest-plan.json`:

```json
{
  "status": "feedback_complete",
  "states": [],
  "full_coverage_pending": true,
  "delivery_complete": false,
  "full_final_required": true,
  "requires_fresh_capture": false
}
```

Three front cells remain `unassessed`, correctly labelled
`deferred_full_coverage`. The reverse repair's approved regression obligation
is retained. The sealed oracle requires the controller to schedule the missing
full native sweep and then its image work, so `missing_full_sweep_scheduled`
remains false and the case fails.

This is **not an acceptance bypass**. `feedback_complete` means diagnostic work
completion in this API. The receipt continues to say delivery is incomplete and
full final is required. Explicit `final=True` acquires both states; before image
review it is not accepted; completing both current bound reviews returns
`accepted` with `native_executed:false` in
`replay-002/C06_targeted_full/full-reviewed/completion.json`.

An integration that always invokes its final close path can satisfy delivery.
The API risk is that a caller treating the non-final status alone as workflow
completion could stop with full coverage debt. The original oracle intentionally
requires stronger automatic forward scheduling; that requirement was not
relaxed after seeing the API.

## F2: conflicting exact native values collapse when both fail equality

The minimal packet is in `minimal-conflict/observation.json`; expected is in
`minimal-conflict/plan.json`. Both samples share one input, instance, event epoch,
state, and full-content capture. Their exact original CGRect extents are:

```text
sample0 width = 65.99999999999999 pt
sample1 width = 66.00000000000001 pt
approved operator = eq
approved expected = 66 pt
approved tolerance = 0
sealed oracle status = unassessed
actual native_checks status = failed
```

`replay-002/C08_calibration/conflict-raw.json` preserves the original evaluator
report and exact rational source evidence. The minimized packet takes its frames
directly from that report, preserving both samples. Run:

```sh
python3 -B validation/routed-forward/probe-review/minimal-conflict/reproduce.py
```

The script exits1 while the actual result is failed. An optional first argument
selects a preserved production scripts directory. This reproducer also failed
against the later current `native_checks.py`, whose SHA matched the tested
replay's native evaluator.

Mechanism: native geometry evaluates each sample against the expected value,
then `all(result)` passes and `not any(result)` fails. Because neither sample
equals66, the second branch wins; actual-value disagreement is not detected when
both Boolean comparisons agree. The source values remain present, and no epsilon
or threshold change occurs. The sealed contract requires real within-state
conflict to remain unknown even when both strict comparisons are false. This
counterexample isolates that semantic gap; it is not proof of a product defect.

## F3: non-native review/measurement dispatch has no observed retry stop

`replay-002/C10_bounded_retry/retry-summary.json` shows the distinction:

```text
native acquisition cycle statuses:
  capture_required, capture_required, blocked_repeated_unchanged_evidence
actual synthetic native calls: 2

image-review cycle statuses:
  awaiting_review, awaiting_review, awaiting_review, awaiting_review
new synthetic native calls after setup: 0
```

Each image attempt has a separate saved submission, bound receipt, correction
history, and cycle receipt. The actual observation remains unknown. Every prior
cycle is supplied by exact path/SHA in `history`. No pass is fabricated and the
required cell remains pending, but the fourth dispatch is still allowed.

`replay-002/C08_calibration/calibration-retry-statuses.json` likewise records four
`awaiting_measurement` cycles, with one total setup acquisition and no subsequent
native invocation. The profile is synthetic and exercises diagnostic plumbing
only. Raw failed/unknown statuses are unchanged by annotation; the fitting stage
does not certify UIKit identity or real provider behavior in this replay.

Mechanism in the tested cycle: its repeated-signature stop counts only prior
cycles with `native_executed is True`. A review-only or measurement-only cycle
never increments that count. The original oracle requires bounded retry for all
work items (at most three total attempts), so `calibration_bounded`,
`max_attempts_per_work_item`, and `stops_after_exhaustion` fail. These results
do **not** demonstrate unbounded SDK execution. A product integration could
separately cap non-native dispatch; that layer was not exercised here.

The first run used repeated valid negative image judgments. The second run
strengthens this into repeated honest unknown judgments, which is closer to a
failed review attempt and avoids treating a known product failure as a review
transport error. Both original outcomes remain saved.

## Scope and reproducibility limits

- Original design seal:
  `6b205ffdd4eaf79433e44daf8ef4c056d95cab54e2ef4401440d3819d4367045`.
- The second adapter bytes are copied to `replay002-adapter.py`. Run it with a new
  `--output` directory to reproduce the full synthetic procedure. Existing output
  directories are never reused or repaired.
- Each run records production script SHA256 values in
  `production-input-hashes.json`. Production `ax_calibration.py`,
  `retest_plan.py`, and `feedback_loop.py` changed after replay002 while the owner
  continued implementation. The historical results were not overwritten and
  must not be presented as a replay of that later snapshot. Production source
  bytes were not snapshotted before those concurrent edits; exact old-source
  restoration needs the owner's matching source revision. Native evaluator
  hashes remained unchanged for the minimized counterexample.
- Adapter improvement between runs added direct calibration retry observations,
  height controls, and a positive-visual/native-failure control. It did not change
  any sealed expectation. The first run's `calibration_bounded:false` was a
  provisional adapter classification; only replay002's four actual default-loop
  calls establish that field.
- C10's `complete_with_required_failure` checks the low-level admission API with
  an explicitly synthetic failed report. It is a gate control, not evidence of a
  production bug or trusted acquisition. Actual valid failed evidence is
  independently exercised in C02/C09.
- This replay tests decisions, schema rejection, stale-binding rejection,
  coverage accounting, and strict measurement arithmetic for supplied packets.
  It does not establish actual test discovery, native app launch, real AX leaf
  identity, empirical calibration residuals, source-to-native rendering fidelity,
  or visual reviewer correctness. Actual SDK calibration is **unexecuted** here;
  a runnable native observer/bridge and real native runtime output are required.

No sealed original, expected threshold, oracle assertion, or production script
was changed to improve the score.
