# Requirement decisions and source-bound feedback

Use this for a complex UI change when findings need to drive implementation and
verification decisions. The tools reuse existing observations; they do not infer
generic computed SwiftUI styles or automatically prove root causes.

## Approved obligations and launch inputs

The independent design source JSON includes an obligation index. Every entry has
exactly `id`, `clause`, `priority` (`must`/`advisory`), `states` (approved state IDs)
and `risk` (`layout`/`style`/`behavior`/`content`). The owner must check that this index
represents the intended requirements; hashing cannot prove prose completeness.

An independently approved routes file has this shape:

```json
{
  "version": 1,
  "index": {"source": "reference", "pointer": "/obligations"},
  "routes": {
    "action-state": {
      "rule_ids": ["primary-enabled", "activation-receipt"],
      "reason": "Native control plus successfully dispatched callback checks",
      "regression_obligations": ["action-appearance"]
    },
    "action-appearance": {
      "rule_ids": ["primary-fill"],
      "reason": "Approved rendered region",
      "regression_obligations": []
    }
  }
}
```

Every index obligation needs a disposition; unknown rule IDs are rejected. An empty
route retains its rationale, and a MUST without an applicable route blocks release.
Independently declared N/A cells stay N/A. An outside-ledger discovery is not an
automatic false alarm: check whether the original requirement lacks a route.

Each case/platform also has a JSON launch record inside a source in the design
lock: exactly `scenario`, `platform`, `fixtures_sha256` (canonical JSON digest) and
`bridge_sha256` (original file-byte SHA). This pins actual caller inputs and the
thin bridge independently from implementation. Record its exact source/pointer.

```sh
python3 scripts/requirement_routes.py audit --plan plan.json \
  --design-lock lock.json --design-sha256 LOCK_SHA \
  --routes routes.json --routes-sha256 ROUTES_SHA --output coverage.json
```

`route` takes the same arguments plus `--report` and `--observation`. Its output
separates contract-route repair, missing capture, environment repair, oracle
disagreement, source diagnosis and unresolved capability/locator investigations.
Optional `--discoveries` accepts original `{obligation_id,reason,evidence}` records;
it does not turn them into TP/FP or extend their detection scope.

## Compile one execution manifest

`execution_plan.py` reconstructs the approved business route and after-target
extensions from the parent design plan. It does not accept a separate base action
file as an equivalent route. Full executions retain business actions. Targeted
feedback keeps the original action prefix/indices through its last selected state,
omits only unrequested observation work, and retains the complete parent plan and
expectations. Initial states need explicit approved checkpoint actions.

```sh
python3 scripts/execution_plan.py --plan plan.json \
  --design-lock lock.json --design-sha256 LOCK_SHA \
  --fixtures approved-fixtures.json --bridge Bridge.swift \
  --launch-source launch --launch-pointer /caseA/ios \
  --state expanded --state updated --output feedback-plan
```

Without `--state` the manifest requests full coverage. It writes `execution.json`,
derived runtime `fixtures.json` and `actions.json`. `--strategy legacy` is a neutral
comparison option; optimized execution defaults to `coalesced`.

Add `--run --execution feedback-plan/execution.json --source-root /actual/component/source`
and the normal platform options (`--package`, `--simulator`, `--developer-dir`,
`--build-cache` for iOS; `--project`, `--java-home`, `--android-sdk` for Android),
using a DIFFERENT fresh output directory. Source roots are explicit production
files/folders, not generated test/build folders. Evidence must be outside them.
The runner rebuilds the manifest, records source/input fingerprints before SDK
execution, checks them afterward, and immediately computes required coverage and
automatic parent-plan checks. `--policy` and `--policy-sha256` enable bound pixel
checks without qualitative votes. Each failed attempt has its own fresh directory.

Source identity is a changed-root fingerprint, not a complete compiler dependency
proof. The integration owner must choose actual relevant production roots. Test
environments, locked fixture/bridge bytes and real dispatch still need preflight.

The iOS coalesced mode uses each fresh full-state scan for its target observations,
reads coverage facts from that same AX/image packet, and omits unrequested auxiliary
initial/before-update/final scans. It keeps native activation, immediate frames,
settling waits, interval coverage and epoch checks. It does not reuse an old image
across code/state changes. Operation timings are nested inclusive walls, not additive
elapsed time. `captured_partial` is collection success within a targeted scope,
not complete business/visual acceptance.

## Recheck a change

`retest_plan.py` consumes an evaluated parent report, original failed assertion IDs,
approved obligation dependencies, changed production paths and before/after source
SHA digests. It closes the declared regression dependencies and proposes selected
states for diagnostic feedback. It does not prove that all other states are safe.

```sh
python3 scripts/retest_plan.py --coverage coverage.json --plan plan.json \
  --report original-report.json --failed-id expanded/primary-fill \
  --change change.json --output retest.json
```

`change.json` contains `changed_files`, `source_before` and `source_after`. Keep the
original finding, source cause hypothesis and minimal patch, then use this plan to
obtain new evidence. Select a project precedent for the affected component/style
when appropriate; retain its actual source location and deployment constraints.
Do not replace the independent design with an implementation-derived expectation.

After diagnostic feedback, perform a fresh FULL final run and required page/E2E
checks. `requirement_routes.py admit` consumes the evaluated complete parent report
and returns blocking MUST obligations. `--scope targeted` can never return accepted.
An unavailable critical style or disputed oracle is unverified, not fixed.

For normal development, run checks as soon as a source-bound capture is ready.
Record queue/synchronization separately from compile/native/check/agent work.
Research trials additionally isolate arms and seal every source version and all
external/heldout judgments; global cohort barriers are not a daily PR workflow.
