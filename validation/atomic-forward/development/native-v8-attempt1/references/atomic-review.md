# Contract-bound visual observations and shared acceptance

Use this when visual findings must be auditable against an independent design.
The approved base contract still compiles through `design_contract.py`. Each
manual rule checks one aspect, rather than a sentence combining colors, wrapping,
hierarchy and state. See the complete [neutral example](../assets/atomic-example/).

An independent owner pins a separate `policy.json` canonical SHA256 alongside the
design lock SHA256 before implementation. It names each manual rule exactly once,
its single aspect/method, and the component/host/system responsibility of its
logical target. Visual Boolean propositions come from exact typed source pointers
in the same sealed design, so `actual:true` answers an explicit approved question.
Rendered color atoms use opaque source-backed ARGB. A canvas rule must specify
which layer paints the sampled region; an ambiguous owner is a design issue to
resolve before scoring. Hashes do not establish design correctness or authorship.

## Submit actual observations, not rewritten expectations

```sh
python3 scripts/review_contract.py catalog --plan generated/plan.json \
  --design-lock approved-lock.json --design-sha256 LOCK_SHA \
  --policy policy.json --policy-sha256 POLICY_SHA --platform ios \
  --output catalog.json
```

The catalog provides opaque stable `review_id` identities, original assertion IDs,
targets, explicit propositions, generated expected values/units/operators and
source provenance. Save the catalog digest from its `catalog_sha256` field.

The reviewer submits only:

```json
{
  "version": 1,
  "catalog_sha256": "CANONICAL_CATALOG_SHA",
  "observation_sha256": "EXACT_ORIGINAL_FILE_SHA",
  "decisions": [
    {"review_id": "FROM_CATALOG", "actual": true,
     "reason": "What the original captured state actually shows",
     "snapshot_indices": [3, 4]}
  ]
}
```

Only qualitative atoms accept Boolean/unknown actuals. Missing decisions remain
unassessed. No `expected`, `unit`, `status`, operator or target override is accepted.
Screenshot identities, state/input/action epochs and actual artifacts are checked;
the tool generates evidence hashes, findings and the manual input for native checks.

```sh
python3 scripts/review_contract.py review --plan generated/plan.json \
  --design-lock approved-lock.json --design-sha256 LOCK_SHA \
  --policy policy.json --policy-sha256 POLICY_SHA --platform ios \
  --observation run/observation.json --submission observations.json \
  --output new-review
```

The output contains `catalog.json`, `manual.json`, `findings.json`, `report.json`.
`native_checks.py` can consume the bound manual with `--review-policy` and
`--review-policy-sha256`, together with the independent design lock arguments.
It reconstructs the bundle from its original requests and images. A changed
expected, status, artifact, rationale or stripped binding is rejected. Keep the
policy digest outside the implementation-edited output, just like the design lock.

## What rendered-color evidence establishes

Pixel rules operate automatically on every eligible coherent state frame. The
independent sampling policy fixes a normalized rectangle inside a uniquely
resolved native semantic/control box, minimum support and pixel count, explicit
RGB channel tolerance, and fully-visible versus visible-fragment scope. The
tool recomputes native-to-PNG mapping, clips to the actual viewport, and records
the original PNG SHA256, native selector/box, pixel region and full histogram.
It never accepts AI-entered observed RGB values or chooses samples by closeness
to the expected color. RGB tolerance is not distance between packed ARGB integers.

The assertion concerns the dominant rendered sRGB in that approved region. A
region meant to measure solid fill must be independently suitable for that role;
glyph ink, an overlaid child or a gradient may make it uninformative. Insufficient
support, conflicting values, missing mapping or unsupported color profiles stay
unknown. Transparent expectations need a separate approved compositing model.
This is not a generic computed SwiftUI font/color/padding API, whole-canvas proof,
or physical hit-area measurement. Existing unsupported native-style cells remain.

## Reliable independent acceptance

`acceptance.py` is a shared evaluator, not an extra treatment benefit. An external
environment contract fixes native dimensions, direction, theme and platform font
configuration; known Compose wire aliases are explicit. Unsupported/mismatched
environments gate acceptance to unknown while preserving raw facts.

For qualitative atoms give two independently scoped contexts the same original
anonymous evidence and approved catalog, without each other's answers. Each
returns `{ "review": <submission above>, "attributions": [...] }`. A failure
attribution contains only `id`, `cause` (`product`, `infrastructure`, `observation`,
`uncertain`), `reason`, and original state `snapshot_indices`. Artifact hashes are
generated by the tool. The CLI requires both judge files and a separately pinned
environment file/digest alongside the plan, policy, lock and observation arguments.

Validated native/pixel statuses cannot be voted away. Qualitative judgments must
agree, otherwise the result stays unknown. A strict measured failure does not
automatically establish a product bug: for component-owned targets both independent
cause assessments must agree; missing or disputed attribution stays uncertain.
Host/system responsibility remains explicit. Keep raw judgments, strict F,
disagreements, supported product clusters and schema rejection as separate records.
AI agreement is not human gold and may share systematic errors.

Report true product alarms separately from report-schema/identity rejection.
Never repair a sealed original finding after seeing acceptance answers. Same-cause
manifestations and unrelated experiments must not be pooled as independent bugs.
