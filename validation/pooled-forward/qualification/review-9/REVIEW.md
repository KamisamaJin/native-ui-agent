# Independent frozen review9 delta

**Not qualified: SC18 confirmed.** The five review8 failure families now close correctly in both arms, but complete local native singleton queries still require visibility to establish their mathematical presence/cardinality facts.

Both verifiers report `valid:true, complete:true, count:1, visible:false` for the bound current native query and then return U for `present:true` and local `unique:true`. This reproduces with a valid iOS full tree, emitted `offscreen_not_resolved` explicit query, and actual-shaped Compose semantics. Two offscreen distinct matches correctly establish presence P. Under the unchanged sealed native D/M definition, one actual match is enough for presence and a complete singleton domain proves local uniqueness. Visibility and activation remain separate facts; the target-only state correctly stays `complete:false` for full content.

**174 raw assertions:162P/12F.**10 F rows demonstrate SC18. Two F rows preserve an old synthetic positive containing a partial parent graph: it removed an ancestor while retaining its reference. That is an invalid complete-tree format under the new guard; old outcomes remain unchanged, and separate query-only, legacy-flat and full-tree-plus-query wire positives pass.

SC13–17 controls pass: unknown query schemas/resolutions, cyclic/disconnected graphs, duplicate identity records and contradictory headers reject; complete local zero-result queries decide their local negatives. Typed reference controls, prior PNG16/joint/domain/compiled-host rejections, strict raw geometry, relevant CSP alternatives/budget, candidate default9P and baseline default2P pass. The18-path common port has15 whole files identical and preserves the original treatment-policy exclusions.

One check-wrapper error occurred after19P typed checks per arm; its initial source/error are retained. A completion script ran only the missing width/CSP checks. No candidate failure was erased or rerun into a replacement outcome.

All evidence is HOST/SIMULATED. No actual SDK, native packet, benchmark, performance sample or business task was run. Operators were excluded and delegated separately. Prior review8 source, reports, all raw outcomes and seal remain unchanged; all current first failures are archived before closure. The user gate remains unstarted.

Read-only repro:

```sh
python3 -B validation/pooled-forward/qualification/review-9/checks/repro_existing.py --arm candidate-v13.8 --case ios-explicit-offscreen-count1-presence
python3 -B validation/pooled-forward/qualification/review-9/checks/repro_existing.py --arm baseline-v12.6-common-5 --case android-offscreen-count1-local-cardinality
```
