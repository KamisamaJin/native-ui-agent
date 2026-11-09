# Managed execution

`ui_loop.py native` runs resource admission and evidence responsibility checks automatically. It generates guarded native actions; neither arm selection nor remembered optional calls is needed. Raw source, captures, review results and errors remain outside disposable scratch.

## Resources

Optional project `resources` policy: `root`, `max_bytes` (default 20 GiB), `min_free_bytes` (5 GiB), `max_simulators` (1), `sample_seconds` (2), `ttl_seconds` (86400). The scratch root must be disjoint from production source/evidence, newly created or marked by this owner. A live OS lease prevents concurrent acquisition/deletion. There is no global cache/device purge.

iOS `native_options.simulator: "managed"` requires `resources.ios: {device_type, runtime}` using exact installed IDs. Only journaled creates are deleted; caller-supplied device UUIDs are borrowed. Every invocation removes its owned devices. Compiled scratch persists under its budget between feedback cycles and is removed on final capture, error, or explicit cleanup. Borrowed project build paths are measured/budgeted but not deleted. Shared SDK/Gradle caches are not managed.

Public Python API: `with resource_manager.Resources(config, output, final=False) as resources:`; `resources.directory(name)` acquires one owned directory; `resources.native_options()` acquires native handles; `resources.run(argv, env=..., stdout=...)` supervises the actual process group. The root journal, OS lock, markers and acquisition tokens provide ownership, not a filename prefix/PID alone. Reentering one exact root reconciles an interrupted owned process/device. SIGKILL cannot execute Python cleanup; reconcile is required on the next entry. `resources.json` records samples, policy, primary error, cleanup errors and leftovers. Peaks are sampled allocated bytes, not exact transient/APFS physical peaks.

CLI: `python scripts/resource_manager.py cleanup --config PROJECT.json --output FRESH_RECEIPT_DIR`. `inspect` also acquires the exclusive lease and reconciles stale owned processes/devices before returning its state.

## Action guards

Approved launch actions may declare `depends_on: [earlier indices]` and `preconditions: [{target, property, op, expected}]`. If omitted, the default dependency is the preceding action (the first has none). An explicit empty list is an independently approved new branch. Unknown, forward/self/cyclic dependencies are rejected before dispatch. Supported properties are `present`, `enabled`, `selected`, `label`, `value`; operators are `eq`, `contains`. Native absence outside a proven complete scope is unavailable, not guessed false.

The compiler fixes dependencies and predicates in `execution.json`. Both native templates check them before dispatch; blocked descendants do no extra native action or target sweep. One original root diagnostic remains. `action_guard.verify_observation(actions, observation, platform)` independently replays successful stimulus/method, process/input/event binding and actual predicates. Successful dispatch is distinct from a matching callback expectation. State assertions depending on an unestablished route retain U and the upstream receipt. Independent sibling branches can still collect their own evidence. Source-bound final/full admission still requires every mandatory item.

## Responsibility contracts

Set `responsibility_ref: {source, pointer}` to an array inside the separately approved design lock. Each atomic entry has `id`, `clause`, `priority` (`must`/`advisory`), `owner` (`component`/`bridge`/`integration`), `method`, `subject`, `rule_ids`.

Native methods `control`, `geometry`, `callback`, `text_layout`, `visual` must map to actual compatible generated assertion kinds and component scope. `source` requires no rule IDs and binds `subject` through config `evidence_subjects: {subject: [absolute files]}`. Component subjects belong to production roots, bridge subjects to the actual bridge, integration source subjects outside both. Source can prove only a source-review claim; computed-style/executed-integration declarations have no provider and block before SDK use.

For source claims supply an independent `source_review_store` outside production roots. The default chain writes `source-review-template.json` and pending tasks. Reviewers supply only `{version: 1, observations: [{id, observed: bool|null, reason, citations: [{path, line}]}]}`. Expectations (`true`, Boolean), responsibility and subject hashes are generated from the independent claim, not entered by the reviewer.

Bind with `python scripts/evidence_responsibility.py bind --config PROJECT.json --submission ORIGINAL_ACTUALS.json --output NEW_RECEIPT.json`. Entries are append-only and source/claim-bound. Conflicts stay unresolved, edits invalidate only the exact affected subject observations. Next default cycle and final review completion automatically import them into admission. A schema/type match is not proof that a review is correct or that a failure belongs to the component; attribution remains separate. Omitted responsibility contracts retain legacy native-component scope and cannot certify external/source/integration completeness.
