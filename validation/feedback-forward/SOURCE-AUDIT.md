# Shared source-only implementation gate

This gate covers independently fixed source-only obligations. It is shared by
both repair conditions. It does not turn a source statement into a rendered
spacing/color/font fact and does not claim automatic AST/transitive-code proof.
Review actual code; use unknown for missing or unresolved evidence.

`tools/implementation_audit.py` reads the independent design lock and an
`implementation-audit.json` policy with `{version:1,index:{source,pointer}}`.
The indexed list has `{id,clause,priority,files,proposition,expected}`. Propositions
and expected values are source expressions into the same approved lock. They point
to typed string and Boolean values. Production files are exact relative paths;
`@design/Bridge.swift` and `@design/ObserverBridge.kt` refer to the independently
approved thin bridge, whose byte SHA must match launch approvals.

`definitions` validates the independent schema before implementation without
inventing source files. It cannot be bound as an actual pass. `catalog` binds
actual source bytes/line counts and generates independent expected/unit/provenance
and stable review IDs. `bind` recomputes that actual catalog, checks its digest,
and accepts only reviewer actual/unknown, rationale and original file/line evidence.
Use these options for every command: `--design-lock`, `--design-sha256`, `--policy`,
`--policy-sha256`, `--source-root`, `--design-root`, and fresh `--output`.

A submission has exactly:

```json
{
  "version": 1,
  "catalog_sha256": "canonical catalog digest",
  "decisions": [{
    "review_id": "generated identity",
    "actual": null,
    "reason": "Original source review or explicit uncertainty",
    "evidence": [{"file": "production-relative path", "sha256": "original byte SHA", "start_line": 1, "end_line": 20}]
  }]
}
```

Known judgments must cite every declared file, within its original line count.
Expected/status/unit overrides and cross-source catalog reuse are rejected. A
missing judgment remains U; a missing/failed source gate blocks complete release.
The complete self-check ANDs source acceptance with the unchanged runtime gate.
Independent external panels review source propositions on anonymous source capsules,
retain disagreement as U and report source outcomes separately from native facts.

The separate minimum-source API check emits the actual Swift module and typechecks
its unchanged caller for iOS14. It does not link/archive/launch or certify an older
OS runtime. Current Xcode rejects an iOS14 simulator deployment in Xcodebuild, so
that failed engineering attempt is retained. The generic observer probe's iOS15
`dynamicTypeSize` use is correctly rejected at14; a separate compatible source
caller passes. Actual business source must obtain its own fresh source-version
record; neutral success cannot be reused as its compatibility proof.
