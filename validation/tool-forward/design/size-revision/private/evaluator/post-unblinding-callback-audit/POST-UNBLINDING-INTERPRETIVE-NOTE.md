# POST-UNBLINDING INTERPRETIVE AUDIT — NOT A NEW GRADE

Created 2026-10-19T18:53:15Z. This note was explicitly requested after unblinding. It preserves every sealed grade, matching result, denominator and headline statistic. It adds no replacement score or native rerun.

The baseline tool-v2 submission is `submission-4f4364`; the candidate tool-v3 submission is `submission-b2e249`. The full companion JSON enumerates every D0/FINAL callback assessment with its exact platform/key, original outcome, actual trigger, dispatch evidence, callback interval and source SHA/pointer.

## Reporting qualification

**Baseline D0:** 28 of the 55 sealed FAIL rows are callback count/payload mismatches from 14 iOS activation requests recorded as `unavailable`. None of those 14 native actions is demonstrated as dispatched. All 28 rows also appear among the original 34 FN rows. They must not be described as 28 proven handler bugs, 14 proven handler bugs, or 28 missed business bugs. They are retained atomic observer-contract mismatches under the original scoring implementation. This note does not adjudicate or recount the other FAIL/FN rows.

**Baseline FINAL:** both sealed FAIL rows are `apple::H01/pending-reselection-echo/callbacks.count` and `apple::H01/pending-reselection-echo/callbacks.payload.0`, from the same single `unavailable` native activation request. They establish observed zero callbacks versus an expected one-event interval, but do not establish two final product bugs, or a proven business-handler bug.

**Actually dispatched actions:** neither submission has a sealed D0 or FINAL callback FAIL following demonstrated native dispatch. This observation is limited to the collected action set; it does not prove general handler correctness or absence of other defects. Requested method coverage remains separate: an Android semantic OnClick is not an OS physical tap, and an iOS XCUI tap is not an AX performAction.

**Quiet and blocked intervals:** mount/caller replacement intervals are not activation tests. `blocked_disabled` means the observer declined dispatch; an empty callback interval is real, but does not prove that a handler rejected a delivered input. The same qualification applies to unavailable disabled-control requests whose zero-count row was originally PASS.

## Frozen wording and the interpretive tension

METHODS requires unsupported native properties and unexecuted methods/properties to remain U. The frozen protocol states that an unexecuted script is not an attempt and that a method which cannot be invoked or observed leaves that stimulus/property UNASSESSED. The oracle describes callback evidence as typed invocations from actual native activation. The evaluator method also explicitly separates actual callback count/payload facts from activation-method proof and preserves real callback facts when a different route was used.

The sealed implementation interpreted complete observation of the callback interval as sufficient for a literal count/payload PASS or FAIL, even when the trigger was unavailable. It did separately retain method coverage as UNASSESSED, and its FAIL reasons explicitly said that unavailable dispatch was not a finding that the business handler was wrong. A measured empty interval is a valid fact; absence of a demonstrated stimulus is not evidence that the handler ignored that stimulus. Therefore the literal interval mismatch interpretation does not fulfill the activation precondition for business-defect attribution and is in tension with the frozen unexecuted-stimulus wording. Preserving the original numbers does not resolve that tension.

A count row and its payload row are also two correlated aspects of one expected callback event, not two independent defects. FN metrics containing these rows must be labelled as the original atomic observation-contract metrics, with this qualification, rather than as a proven distinct-business-bug miss rate. No alternative denominator, corrected grade, or replacement statistic is supplied here.

## Complete dispatch inventory

| Phase | Submission | Actually dispatched callback rows | Observer blocked rows | Unavailable rows | Non-activation interval rows | Callback FAIL without dispatch |
|---|---|---:|---:|---:|---:|---:|
| D0 | submission-b2e249 | 60 | 6 | 0 | 34 | 0 |
| D0 | submission-4f4364 | 32 | 3 | 31 | 34 | 28 |
| FINAL | submission-b2e249 | 80 | 8 | 0 | 46 | 0 |
| FINAL | submission-4f4364 | 78 | 7 | 3 | 46 | 2 |

These are atomic callback-row counts; successful-action count and payload rows are listed separately. The JSON also records unique platform/context attempt counts and every exact raw source.

## Exact sealed FAIL keys without demonstrated dispatch

| Phase | Platform | Count key | Payload key | Actual dispatch |
|---|---|---|---|---|
| D0 | apple | `C01/pending-option-echo/callbacks.count` | `C01/pending-option-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C01/pending-submit-echo/callbacks.count` | `C01/pending-submit-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C02/pending-ack-echo/callbacks.count` | `C02/pending-ack-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C02/pending-submit-echo/callbacks.count` | `C02/pending-submit-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C03/pending-ack-echo/callbacks.count` | `C03/pending-ack-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C03/pending-keep-echo/callbacks.count` | `C03/pending-keep-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C03/pending-notes-echo/callbacks.count` | `C03/pending-notes-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C04/pending-new-choice-echo/callbacks.count` | `C04/pending-new-choice-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C05/pending-done-echo/callbacks.count` | `C05/pending-done-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C05/pending-selected-option-echo/callbacks.count` | `C05/pending-selected-option-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C05/pending-submit-echo/callbacks.count` | `C05/pending-submit-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C06/pending-close-echo/callbacks.count` | `C06/pending-close-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C06/pending-refund-echo/callbacks.count` | `C06/pending-refund-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| D0 | apple | `C06/pending-submit-echo/callbacks.count` | `C06/pending-submit-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |
| FINAL | apple | `H01/pending-reselection-echo/callbacks.count` | `H01/pending-reselection-echo/callbacks.payload.0` | `unavailable`; no delivered native action proved |

All rows in this table belong to `submission-4f4364`. All D0 rows in this table are retained in the original FN list. The candidate submission has no callback FAIL keys to list.

## Preserved sources and audit scope

- Machine-readable complete enumeration: `interpretive-audit.json`; SHA256 `d5926c25cddeab7aebe89d78fb679adb49b6a877802352863364670df472150e`.
- All original grades, matching artifacts and D0/FINAL/paired seals were hash-checked before and after this read-only audit and remain unchanged.
- This interpretation is visibly post-unblinding. It is not an independent preregistered regrade, a new ground-truth table, or a causal product diagnosis.
