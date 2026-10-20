# Multi-task blind evaluation tables

Three task pairs; both arms already include v6 contract and observer infrastructure. Null denominators are N/A. F counts below are strict scored failures; confirmed natural product defects are reported separately.

## Common acceptance

| Arm | Stage | P | F | U | N/A | U / applicable |
|---|---|---:|---:|---:|---:|---:|
| baseline-v6 | D0 | 527 | 45 | 866 | 146 | 60.22% |
| baseline-v6 | FINALPublic | 572 | 0 | 866 | 146 | 60.22% |
| baseline-v6 | FINALHidden | 285 | 0 | 431 | 76 | 60.20% |
| baseline-v6 | FINAL | 857 | 0 | 1297 | 222 | 60.21% |
| candidate-v7 | D0 | 527 | 45 | 866 | 146 | 60.22% |
| candidate-v7 | FINALPublic | 572 | 0 | 866 | 146 | 60.22% |
| candidate-v7 | FINALHidden | 285 | 0 | 431 | 76 | 60.20% |
| candidate-v7 | FINAL | 857 | 0 | 1297 | 222 | 60.21% |

## Original descriptor-matched detection ledger

This is the frozen deterministic strict identity ledger: FP includes expected/unit identity rejection and must not automatically be interpreted as a false product alarm. Independent product dispositions are reported separately below. Conditional ledger rejection=FP/(TP+FP); U is retained, with bounds over all claims. Classical FPR is N/A because no complete true-negative claim universe was labelled. Cluster and row recall here require strict original descriptor-matched independently confirmed product F rows, not every numeric F. Unmapped impressions remain U; explicit successful observations are excluded from the failure-claim denominator.

| Arm | Origin | TP | FP | U | Detected product rows | Row recall | Detected clusters | Cluster recall | Conditional false discovery | All-claim bounds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline-v6 | machine | 26 | 0 | 0 | 26/45 | 57.78% | 3/5 | 60.00% | 0.00% | 0.00% – 0.00% |
| baseline-v6 | manual | 19 | 8 | 17 | 19/45 | 42.22% | 2/5 | 40.00% | 29.63% | 18.18% – 56.82% |
| baseline-v6 | combined | 45 | 8 | 17 | 45/45 | 100.00% | 5/5 | 100.00% | 15.09% | 11.43% – 35.71% |
| candidate-v7 | machine | 26 | 0 | 0 | 26/45 | 57.78% | 3/5 | 60.00% | 0.00% | 0.00% – 0.00% |
| candidate-v7 | manual | 6 | 17 | 6 | 6/45 | 13.33% | 1/5 | 20.00% | 73.91% | 58.62% – 79.31% |
| candidate-v7 | combined | 32 | 17 | 6 | 32/45 | 71.11% | 4/5 | 80.00% | 34.69% | 30.91% – 41.82% |

## Sealed independent product dispositions

These are integer sums of the original already sealed independent selfreview judgments, not new claim reclassification or a human gold standard. Two grader-labelled false alarms have contradictory original pixel evidence; see [GRADER-DISAGREEMENTS.md](GRADER-DISAGREEMENTS.md). Those labels are preserved, but objectively adjudicated product FDR remains unavailable. Identity-rejected compatible descriptions remain U when a concrete false product alarm is not established. No new detection credit or expected/unit repair is granted. Qualitative/ineligible unknowns are separate. Classical FPR remains N/A.

| Arm | Origin | TP | Grader-labelled FP | Eligible U | Additional qualitative U | Conditional false discovery | All-claim error bounds |
|---|---|---:|---:|---:|---:|---:|---|
| baseline-v6 | machine | 26 | 0 | 0 | 0 | 0.00% | 0.00% – 0.00% |
| baseline-v6 | manual | 19 | 0 | 10 | 15 | 0.00% | 0.00% – 56.82% |
| baseline-v6 | combined | 45 | 0 | 10 | 15 | 0.00% | 0.00% – 35.71% |
| candidate-v7 | machine | 26 | 0 | 0 | 0 | 0.00% | 0.00% – 0.00% |
| candidate-v7 | manual | 6 | 2 | 15 | 6 | 25.00% | 6.90% – 79.31% |
| candidate-v7 | combined | 32 | 2 | 15 | 6 | 5.88% | 3.64% – 41.82% |

Field adapters, exact original source hashes and the identity ledger alongside each task are in [review-product-summary.json](review-product-summary.json). This distinction does not turn a qualitatively related finding into exact descriptor-matched row/cluster credit.

## Per-task quality and repair

| Task | Arm | D0 P/F/U/NA | FINAL public P/F/U/NA | FINAL heldout P/F/U/NA | Original combined cluster recall | Public product cluster repair |
|---|---|---|---|---|---:|---:|
| T1 | baseline-v6 | 175/20/293/40 | 195/0/293/40 | 97/0/147/20 | 2/2 (100.00%) | 2/2 (100.00%) |
| T1 | candidate-v7 | 175/20/293/40 | 195/0/293/40 | 97/0/147/20 | 1/2 (50.00%) | 2/2 (100.00%) |
| T2 | baseline-v6 | 188/8/294/38 | 196/0/294/38 | 95/0/143/26 | 1/1 (100.00%) | 1/1 (100.00%) |
| T2 | candidate-v7 | 188/8/294/38 | 196/0/294/38 | 95/0/143/26 | 1/1 (100.00%) | 1/1 (100.00%) |
| T3 | baseline-v6 | 164/17/279/68 | 181/0/279/68 | 93/0/141/30 | 2/2 (100.00%) | 2/2 (100.00%) |
| T3 | candidate-v7 | 164/17/279/68 | 181/0/279/68 | 93/0/141/30 | 2/2 (100.00%) | 2/2 (100.00%) |

Macro task summaries, platform/class breakdowns, exact missed rows, strict row transitions and new P→F are in [metrics.json](metrics.json). Hidden inputs were unavailable during repair, so they have no D0 hidden repair denominator.

## Actual end-to-end cost

The per-unit endpoint is its own FINAL raw corpus seal, including earlier barriers, resource waits and shared experiment scheduling. Complete cohort closure also includes all final typed checks and is reported separately. It is not a production-latency estimate. Native command sums include overlapping iOS/Android work and must not be added as elapsed wall time. Model wall includes compile waits.

| Task | Arm | Implementation→own FINAL seal (min) | Model phase wall sum (min) | Own native command sum (min) | Waiting/coordination (min) |
|---|---|---:|---:|---:|---:|
| T1 | baseline-v6 | 74.74 | 13.24 | 12.25 | 49.85 |
| T1 | candidate-v7 | 74.72 | 10.43 | 13.04 | 52.09 |
| T2 | baseline-v6 | 77.06 | 11.54 | 17.68 | 48.27 |
| T2 | candidate-v7 | 77.19 | 11.35 | 17.92 | 48.43 |
| T3 | baseline-v6 | 82.23 | 12.52 | 22.06 | 48.11 |
| T3 | candidate-v7 | 81.70 | 10.05 | 21.10 | 51.09 |

Cohort first implementation→last public endpoint: **94.23 min**. Complete public cohort closure: **94.29 min**. Implementation→assignment reveal: **175.79 min**. Preregistration→reveal (including engineering/design/neutral controls): **224.88 min**. Shared audit native command sum: **177.05 min**. Token and money costs are unavailable.

## Same-source measurement diagnostic

| Comparison | Cells | U→assessed | Assessed→U | P↔F conflicts | Before U | After U |
|---|---:|---:|---:|---:|---:|
| collectorSessions | 3024 | 0 | 0 | 0 | 1660 | 1660 |
| sameFrameCheckers | 296 | 0 | 0 | 0 | 0 | 0 |

Collector sessions compare actual native acquisitions with the same source/public inputs and fixed common oracle. Same-frame checkers run both frozen checkers on identical observation bytes, with zero new SDK calls. These diagnose measurement; they are not extra independent development trials.

## Limits

Only three prospective task pairs were tested. Independent AI acceptance is not a human-labelled gold standard. Fixed selected-rule coverage is not complete design-brief coverage. iOS computed typography/color and unsupported evidence remain unknown. Shared device/cache/order/barrier costs prevent a causal speed claim. All strict failures and their separate cause classifications remain published.
