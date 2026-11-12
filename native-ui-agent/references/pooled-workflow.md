# PR-scoped native workflow

`ui_loop.py native --config PROJECT.json --output NEW_CYCLE` owns the default state machine. It resolves previous capture/history, imports registered actuals, measures patches, routes work and emits typed `handoff.json`. Keep roots stable within one PR and use a new root for another PR. State is locked, durable and bound to owned root inodes outside production/original captures.

```json
{
  "workflow": {"root": "/absolute/PR/workflow", "max_cycles": 30},
  "platform_source_roots": {
    "ios": ["/absolute/project/ios/Sources"],
    "android": ["/absolute/project/android/app/src/main"],
    "shared": ["/absolute/project/shared-inputs"]
  },
  "dependency_files": {"shared": ["/absolute/project/shared-tokens.json"]},
  "dependency_environment": {"ios": ["PRODUCT_THEME"], "android": ["PRODUCT_VARIANT"]}
}
```

`source_roots` remains the complete production-root set. Groups name only exact roots from it; unclassified/overlapping roots conservatively affect both platforms. Same relative filenames retain distinct namespaces. Conventional package/lock/Gradle settings, declared extra files, bridge/fixtures/templates/tools, approved rules and selected environment/toolchain identities are also pinned. This validates a declared boundary, not arbitrary compiler dependency completeness. The integration owner must establish actual closure. Unknown external inputs cannot authorize reuse. Source actuals remain separately bound to exact subjects; they do not certify runtime behavior.

Conventional build environment selectors and declared additional names are pinned by presence and value hash, using effective native-option overrides. They are never logged as raw values. Platform-only selectors invalidate that platform; shared names invalidate both. These declared selectors also bind the iOS compiled-cache key. Caller fixture changes can require fresh native evidence while retaining a correctly matched compiled host. Review custom build scripts for additional files and environment inputs before approving `all_dependencies_pinned`.

## Bounded owned devices

Managed iOS pooling is default. `resources.pool` accepts `idle_seconds` (300, max 1800), `max_age_seconds` (3600, max 7200) and `max_uses` (12, max 100); `pool: false` requests one-shot retirement. Existing simulator/byte/free-space limits and exclusive leases still apply. Active, idle and retirement-pending slots count toward the cap. Compatibility binds installed type/runtime and current toolchain identity.

Each native capture removes the generated observer's prior app data on its positively owned device and records a fresh native fixture/process/input/event identity. Reusing a device is not reusing a running view or screenshot. Borrowed devices are not put into the owned deletion/reset set. A separately journaled guardian retires idle expiry and reconciles interrupted controllers after the resource lock becomes available; it cannot delete beneath an active lease. Persisted times use a shared kernel clock and host boot identity, not process-relative Python clocks. Final/error/explicit cleanup retires owned devices and private compiled scratch before final acceptance.

## Original capture adoption

Ordinary `--final` may adopt an original FULL packet only through `capture_validity_ref: {source, pointer}` into an independently approved design source containing:

```json
{"scope":"deterministic_component_fixture","max_age_seconds":1800,
 "reset":"fresh_native_fixture","external_state":"all_dependencies_pinned"}
```

The design owner fixes the finite window (1–3600 seconds) before implementation/collection; this example is not blanket approval. Missing policy/reset evidence, live external inputs, expiry/future timestamps, changed host/context/dependencies, partial or failed native/environment evidence, and missing/tampered members prevent adoption. The complete original package is byte-inventoried, including collector reports, logs, coverage, observations, images and tool/input records. It is reconstructed before admission; headers alone cannot pass.

Reuse keeps original timestamps, session IDs and exact source/input/image/capture references. It emits `native_executed:false`, `capture_reused:true` and a NEW final resource-retirement receipt. All current source/image duties and full final gates still apply; F/U remain visible. Review completion rechecks validity, so a late review can require reacquisition. Explicit `--fresh` requires a NEW full native packet for feedback or final; it cannot be combined with diagnostic `--intake`. Without approved validity, finalization reacquires full evidence.

## Repair handoff

Routed failures emit `repair-task.json` with original task/capture/rule/state/context identity and actual diagnostic source occurrences. Locations are candidates, causes remain hypotheses, and image/measurement/environment/unknown work stays distinct. The next default invocation measures actual platform-source changes and creates an append-only completion proof automatically. `patched_needs_native_retest` proves handoff, not correctness. Fresh affected-code evidence plus full final gates establish repair.

An explicit worker can also use `ui_loop.py complete-native-repair --config PROJECT.json --task TASK --task-sha256 SHA --output NEW_COMPLETION`. Unchanged source, foreign/stale/duplicate tasks or altered evidence reject completion. Open repairs cannot be cleared by changing their oracle/bridge/environment/tools; a new scope requires independent admission. A separate worker CLI call is optional; measured tool proof and native recheck are mandatory.

A per-platform result covers only its configured native plan. Whole-PR delivery also requires the other platforms and independent source/integration/quality duties. Before deleting a workspace, archive and verify original packages, failures, state/handoff journals and final retirement receipts. Shared SDK caches and user resources are not owned cleanup targets.
