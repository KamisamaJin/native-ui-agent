# Independent publication metric and evaluator replay

This directory is a separate publication revision. Earlier metric, native-chain, history, backend and criteria freezes are unchanged. All applications here are synthetic. No actual grade, alarm, image judgment, X/Y map, automatic/evaluated report body or production source was opened. Actual replay remains gated on root's separately verified ALL30 CAUSE barrier.

## Metric review

The frozen `business-quality-tools/metric_rules.py` and its 11 tests are retained byte-exactly under `vendor/original-metrics/`, together with the original freeze and fixed `BUSINESS-METRICS.md`.

The independent synthetic review reproduces these limitations:

- A true post-seal private alarm receives worker initial-detection credit because v1 does not represent visibility or original source-version provenance.
- A post-seal independent-validation record can enter attempted repair because v1 accepts any evidence-bearing repair correspondence without worker/public provenance.
- Mandatory U/N/A platform/state denominators are absent. A producer can supply pass gates while an accompanying mandatory coverage row is U; v1 reports complete delivery and omits that coverage. V1 describes itself as arithmetic rather than a coverage certifier, so this is an input/output reliability boundary as well as a missing required metric.
- Individually finite nonnegative costs can overflow their aggregate to infinity. Invalid clocks themselves are correctly rejected.
- A null unresolved-quality inventory is treated as empty by v1. The revision requires an explicit inventory instead of interpreting missing/unknown metadata as complete.

V1 already correctly retains all five attempts, zero-denominator N/A, unknown cause relations, separate positive-validation claims, and the resolved-alarm FDF denominator. Those rules are retained. Unknown/unadjudicated alarms must remain a separate denominator; they are not silently converted into false alarms.

`metric_rules_v2.summarize(cases, arm, assignment, *, shared_costs, coverage_denominators)` is the independent revision. It requires:

- An actual Boolean `worker_visible`, plus `provenance = {phase, source_version, evidence}` on each defect alarm and attempted repair. `source_version` is the exact lowercase 64-character source-content SHA. Phases are `worker_public` and `independent_private_after_seal`. Private post-seal evidence cannot establish worker detection or attempted repair.
- Separately reported public/private alarm counts and adjudicated/unadjudicated denominators. Defect alarms and positive-validation claims remain distinct.
- A separately authenticated applicability registry for each of five cases and each X/Y version. Registry rows identify platform, state, family, applicable IDs, predeclared N/A IDs and frozen evidence. Final mandatory rows must exactly partition that registry into P/F/U; dropped states, denominator changes, N/A-as-pass and pass gates contradicting F/U are rejected.
- Explicit shared initial/oracle, design preparation, common infrastructure and grading/matcher costs reported separately. All five own-attempt costs and hidden per-arm validation costs remain in the defined ratios. Aggregates must remain finite.

The tests provide the exact small input schema and preserve v1 inputs/results. This helper still cannot authenticate adjudication/reveal, decide genuine causes, establish visibility from a bare assertion, verify timing ledgers, or certify frozen applicability. Those are upstream independently sealed evidence requirements. No actual metric calculation is performed here.

## Portable evaluator API

```python
from replay import replay

result = replay(
    pinned_resolver,
    {"path": ORIGINAL_PACKET_KEY, "sha256": EXTERNAL_PACKET_SHA},
    {"path": ORIGINAL_CODE_INVENTORY_KEY, "sha256": EXTERNAL_CODE_INVENTORY_SHA},
    {"path": ORIGINAL_WORKER_KEY, "sha256": EXTERNAL_WORKER_SHA},
    cause_admission_ref=EXTERNALLY_PINNED_ROOT_ADMISSION,
)
```

The reader supplies `read_bytes`, `read_json`, `hash` and `directory` as in the frozen publication Resolver. Every original input uses its original absolute key and external byte pin. Original JSON bytes are carried unchanged into the isolated child through Base64; embedded original paths, actuals and expected values are never rewritten. Image access uses only the verified restored native/capture directory layout returned by the reader. Accessed input bytes and namespaces are checked again after replay.

`CODE-INVENTORY.json` separately pins unchanged backend modules against exact `BASELINE-COMMON-FREEZE-6` (A) and `CANDIDATE-FREEZE-10` (B). Each evaluation starts a fresh Python `-I -S -B` child: no A/B module cache mixing, CWD/PYTHONPATH/user-site import fallback or bytecode writes. The child checks inventoried bytes again before imports and rejects writes/process/network effects during evaluation. This is a trusted pure replay boundary, not an adversarial OS sandbox.

The recorded dependency is Pillow 11.3.0 and its package/native-library byte inventory, with an explicit CPython 3.9 Darwin interpreter/version pin. Pillow's frozen supported major-version range is enforced. Restore relocation works without original data paths; another host runtime/ABI needs its own independently pinned compatible dependency inventory. No claim of cross-OS binary portability or historical SDK freshness is made.

The packet schema is `version: 1`, `kind: original-fact-evaluator-replay-packet-v1`, with:

- `backend: A|B`, `platform: ios|android` and `data_scope`.
- Pinned `plan`, `lock`, `policy`, native `observation`, actual-only `submission`, `capture_request`, and `capture_receipt` refs. Lock/policy refs additionally require separately trusted `canonical_sha256` values.
- `native_root` and exact capture receipt `image_hashes`. Request/receipt/plan/observation/image bindings, PNG membership, hashes and safe screenshot-relative paths are checked before evaluation.
- Optional `expected_artifacts` refs for `catalog`, `manual` and `report`. Rebuilt values must match exactly. The known catalog self-digest envelope is validated separately. No arbitrary report-field projection or verdict adjustment is allowed. Reports carrying additional emitter-specific transport fields require a separately documented comparison adapter; this version does not silently drop them.

The child calls the unchanged `review_contract.catalog`, `review_contract.bind` and `native_checks.evaluate`. Actual-only submissions cannot supply expectations, units, verdicts or replacement image identities. Missing actuals, insufficient coverage and epoch conflicts remain U. A reproducible F report is still a successful **replay**, not a product pass.

## Barrier and unsupported boundaries

Synthetic mode accepts only `/recorded/...` data keys. Actual mode is `actual-after-all30-cause` and requires an externally pinned root admission of kind `verified-all30-cause-replay-admission-v1`, `actual_replay_authorized: true`, and the exact packet ref in `allowed_packet_refs`. Its pinned `verification` must be a separately produced verified cause-barrier report (`phase: cause`, 15 groups, 30 distinct contexts, matching `cause_index`). The evaluator does not read grade bodies to self-authorize. Root must independently verify that barrier before supplying this admission. Without it, fact and expected-report bodies are never read.

Three claims remain separate:

1. `provenance_bytes_verified` covers the explicit supplied pins and native/request/receipt/image bindings. Full acquisition/capsule/config/positive-resource provenance remains the separate frozen native-chain verifier's responsibility.
2. `backend_native_replay: reproduced` covers the unchanged backend's supported native/pixel/actual binding. A source-domain packet is returned as **unsupported**: its unchanged `coverage_domain.verify_packet` resolves embedded original production roots and needs additional parent/provider/compiled-source proof. This implementation neither opens those original paths nor monkeypatches a missing proof into P. A reader-aware independent domain verifier would be a separately labeled artifact, not this historical live-path backend check.
3. Source-responsibility replay is explicitly unsupported, and `current_source_delivery_verified` is always false. Current-source eligibility, source/native/image delivery obligations, genuine cause truth and resource closure cannot be manufactured from a backend native report.

## HOST and freezes

Run `python3 -B .../test_metrics_v2.py` and `python3 -B .../test_replay.py`. Small fixtures use the frozen generic atomic-example contract plus two generated PNGs; no business/product data is involved. Tests retain source snapshots, logs, small fixtures and original v1 reproduction outputs. They exercise real Resolver restoration with absent original keys, changed/missing PNG/catalog/actual/code bindings, same-state epochs, explicit F/U and the actual-data barrier. The whole HOST tree contains hundreds of files, not another large acquisition corpus.

`FREEZE.json` pins this revision, dependencies, tests, original specification/freeze copies and author results. No actual dataset application is authorized or claimed by this freeze.
