# Independent neutral forward review

The nine-case Pulse Lab specification was authored and frozen before reading the service implementation. Its manifest hash remains `a30eae2498ec90cd5071e99dd30a01ee8eaad89637980f316b6b6238d0c03b74`. `../probe-design/verify_manifest.py` passes for all 35 files.

This review preserves the initial tool snapshot and its observed gaps, then replays a second snapshot supplied after generic service fixes. No live tool file was changed by this reviewer. The native subprocess alone is replaced with a synthetic transport. The contract compiler, exact approved launch binding, routes, locator diagnostics, retest planner, native checks, source maps, receipts, image pinning, clone adoption, repeated-history bound, and admission run unmodified.

## Results

| Probe | Initial pinned tools | Second pinned tools |
|---|---|---|
| Approved Step absence in Idle | Native assertion passes; acquisition requires the absent node, so final capture stays invalid. | Full-content acquisition permits the intended absence; native check and admission pass. |
| Missing Step / duplicate Pause identifiers | Honest failed checks and `diagnose_product`; source/topology diagnostic list is empty. | Failed status retained; each issue has a native topology diagnostic. A real production-file repair to v2 triggers fresh source-bound rechecking and passes the typed subset. |
| Missing native packet | Invalid capture; repeated identical-history scan blocks immediately. | Two unchanged failed native acquisitions are allowed, then the third cycle blocks. Open post-acquisition tasks and rejected admission are preserved. |
| Observation references missing PNG | Rejection escapes before capture/cycle receipts are written. | Invalid receipts retain the evidence error and open tasks; a pinned previous receipt can recover through a new complete capture. |
| Running → Paused during settlement | Mixed bound values stay unassessed, but the next normal cycle blocks before observing the settled state. | Mixed values stay unassessed; the next normal cycle captures settled Paused and passes. Explicit final always captures again. |
| Production v2 → v3 Reset regression | Actual changed file is measured; stale v2 evidence cannot satisfy current final; Paused Reset Count 2 fails the approved Count 0 check. | Same correct behavior. |
| Immutable evidence / clone / intake | Image tampering rejected; identical clone adoption before edits permits source-change planning; intake cannot be final. | Same correct behavior. |

The second replay completes all seven probe groups with their expected assertions. This is a successful regression replay of the supported typed subsets, not a claim that all nine prose/visual cases pass end to end.

## Reproduction

From the repository root, use fresh output directories:

```sh
python3 -B validation/default-forward/probe-review/replay-original.py --output validation/default-forward/probe-review/reproduce-before
python3 -B validation/default-forward/probe-review/replay_after.py --output validation/default-forward/probe-review/reproduce-after
```

The first program reproduces the original observations against `tool-snapshot`; the second asserts corrected behavior against `tool-snapshot-fixed`. Both use the unchanged frozen source/evidence fixtures. Their only assertion differences are the expected outcomes of the reported generic fixes; the native transport and contract translation remain the same.

Authoritative raw results are `replay-final/summary.json` and `replay-after/summary.json`. Every subdirectory retains config, independently typed contract/lock, source versions, cycle traces, original capture request, automatic report, execution coverage, routes, diagnostics, and admission when available. Important examples:

- Original absence dead end: `replay-final/absence/cycle/capture/automatic.json` versus `execution-coverage.json` and `result.json` in that directory.
- Corrected absence: `replay-after/absence/cycle/admission.json`.
- Corrected failed-target diagnostics: `replay-after/missing/cycle/after-diagnostics.json` and `replay-after/ambiguous/cycle/after-diagnostics.json`.
- Recoverable missing PNG: `replay-after/missing-png/cycle/capture/result.json`, `cycle/after-routes.json`, and `recovered-cycle/admission.json`.
- Source regression: `replay-after/clean-and-edit/edited-intake/retest-plan.json`, `edited-final/capture/automatic.json`, and `edited-final/admission.json`.
- Settled-state retry: `replay-after/pending-then-settled/settled-default-cycle/cycle.json` and `admission.json`.

## Residual limits

- The raw approved-prose/native-evidence/source request is unsupported directly: CLI intake returns `Configuration/evidence error: 'plan'`. This is an integration boundary, not an incorrect native decision. These tools consume an independently approved typed contract with scenarios, states, actions, bindings, expectations, and requirement routes; they do not derive a complete oracle from arbitrary prose. The disclosed adapter supplies those items and therefore earns no state-discovery or prose-translation credit for the service.
- No native SDK compilation, simulator/device execution, actual action dispatch, accessibility-runtime fidelity, or complete visual R8 judgment was tested. The fixture PNGs were visually inspected only as synthetic drawings.
- The final replay uses a conservative bound of two unchanged native acquisitions; the frozen spec supplies an upper bound of three. The bounded stopping property is verified, not an exact three-attempt policy.
- Missing-identifier source diagnosis is literal: no `session.step` occurrence exists in v1, so its source-occurrence list is empty. Native absence and source identity remain explicit; the service does not invent a replacement selector or edit source automatically.
- `cycle.status` describes capture validity. A source-bound capture with a failing product assertion may still say `verified_capture`; consumers must inspect `admission.json` before declaring completion. The v3 regression is correctly `not_accepted`.

`comparison.json` records both snapshot hashes and before/after results. The review `SHA256SUMS` seals all retained files except itself; verify with `shasum -a 256 -c SHA256SUMS` from this directory. Earlier adapter development summaries are retained separately; their first text-role mapping errors were fixed in the adapter before the authoritative replays and are not service findings.
