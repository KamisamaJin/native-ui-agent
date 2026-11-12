This narrow independent review found six reproducible reliability weaknesses in the prospective author adapter and provides a separate corrected revision. The original adapter, author tests, author freeze, metric rules and all prior freezes remain unchanged. No actual denominator, case packet, grade, report, map, source or PNG body was read or applied. All data in this directory's HOST fixture are synthetic.

The author freeze was verified at SHA256 `d76216dbcc573d1a3732046e6034849332534ed9cc99f514e3347a69c850d71c`; its original four tests reproduce. Frozen source `coverage_registry.py` has SHA256 `75e5018b4974c4f9b62a251b9ccefcdd2ddb7d6569fe0a93177666746942ad69`. Byte-exact allowed source snapshots are under `vendor/`. `test_metrics_v2.py` was read but never imported/executed because its import-time HOST writes would leave this review directory. Only the side-effect-free frozen `metric_rules_v2.coverage()` function was used with synthetic rows.

The frozen generator's denominator-construction code establishes the relevant schema: required native/image cells contain an explicit `assertion_id = state/rule`; N/A cells legitimately omit assertion_id; source cells omit it and explicitly retain family/state/rule, with three original source duties per platform/family. `GENERATOR-SCHEMA-PROVENANCE.json` records exact source hashes and narrowly selected construction/task-order/seal excerpts. No generated design JSON was opened. The full prospective seal authenticates complete original cells and task order; this adapter does not infer missing individual cells/states from evaluated results or construct a new design oracle.

Retained synthetic original admissions are in `HOST/review-attempt01/RETAINED-ORIGINAL-ADMISSIONS.json`:

- A required native cell missing assertion_id is accepted and silently receives a generated ID. Revision requires the exact original assertion_id.
- An unknown/misspelled kind is treated as native/image. Revision accepts only the frozen generator's five native kinds and source.
- A missing entire public source family can be masked by the remaining private source family. Revision checks both native/image and source representation for all five tasks × both platforms × both original families. It does not invent or enforce individual source-duty/state IDs.
- A source cell carrying a conflicting assertion_id is accepted and that field silently ignored. Revision rejects the conflicting identity.
- Returned X/Y rows share a mutable list, and returned evidence aliases caller input. Revision deep-copies sibling rows and their evidence. Both the initial call and later output mutations preserve caller inputs.
- The CLI accepts duplicate JSON identity keys. Revision rejects duplicate/nonfinite JSON, malformed/duplicate seal entries, inconsistent original count metadata, wrong/missing external pins, and missing inventory membership.

Legitimate N/A identities remain clearly labeled `mechanical-N/A-state/rule-identity`; this does not claim that an unavailable obligation is a compiled assertion or a pass. Required IDs retain `original-required-assertion_id`. Source IDs retain `explicit-source-family/state/rule-composite`. These labels live in the separate `projection_identity_metadata`, while `coverage_denominators` retains the exact six-field row schema required by frozen metric_rules_v2. Native/source U and explicit N/A remain distinct. The adapter emits no `passed_ids`, result truth, source approval, delivery decision, or arm assignment.

The revised pure APIs are `coverage_registry_v2.projection(cells, tasks, evidence)` and `registry(cells, tasks, evidence)`. `projection()` includes per-cell identity metadata; `registry()` returns only metric-compatible rows. Evidence must contain explicit absolute path/SHA256 references; this pure API validates their structure without claiming to authenticate supplied files. `sealed_projection(...)` reads only the three explicitly supplied files: original denominator, public packet task order, and the full seal. It verifies all external SHA pins and the two input memberships in that seal, preserves original bytes, and follows no other packet/source/image/report refs. The root operator must supply an independently held prospective seal pin and original file pins. The adapter cannot establish when a seal was created or authenticate an arbitrary newly authored denominator as historical truth.

`coverage_registry_v2.py` is the standalone CLI handoff, Python 3.9+ standard library. It keeps the original flags, writes a new read-only output, refuses overwrite, and emits version2 with `coverage_denominators` plus separate identity metadata. Root owns actual application:

```sh
python3 -B validation/pooled-forward/publication-coverage-review/coverage_registry_v2.py \
  --denominator "$DESIGN_ROOT/MASTER-DENOMINATOR.json" \
  --denominator-sha256 "$EXTERNALLY_VERIFIED_DENOMINATOR_SHA256" \
  --public-packets "$DESIGN_ROOT/PUBLIC-PACKETS.json" \
  --public-packets-sha256 "$EXTERNALLY_VERIFIED_PUBLIC_PACKETS_SHA256" \
  --seal "$DESIGN_ROOT/SEAL.sha256" \
  --seal-sha256 "$EXTERNALLY_HELD_PROSPECTIVE_SEAL_SHA256" \
  --output "$NEW_OWNED_OUTPUT_JSON"
```

The fixed generic sealed CLI fixture is retained under `HOST/review-attempt01/`; its denominator SHA is `a804bfc4203409bee255fb50e58d0a6ffefb5212edb23c0c5f43cdc5715100ae`, public-packets SHA is `e83e7cdf07205c10ab3c241f150ba51f5678238d5aad8ff7d3ac32fe4060a57b`, and seal SHA is `d411c2803cffb339cf9f266730ed7bf9b86417d2c93b30bed423595a9c55ce7f`. These are synthetic pins, never substitutes for actual historical design authority.

Reproduce the entire bounded review into a fresh owned directory:

```sh
python3 -B validation/pooled-forward/publication-coverage-review/run_review.py \
  --output validation/pooled-forward/publication-coverage-review/HOST/new-review
```

The final retained result is `HOST/final-review/RESULT.json`, SHA256 `05fe31b946d39233d57c25d5de63dcae8c3de0ea3d2ddbbb1922b87862ee260c`. All 20 independent controls, the generic sealed CLI, and the four unchanged original author tests passed in that run. The earlier successful attempt and its runner source remain retained. Tests cover exact cell roundtrip, both platforms/families/multiple states, all three original source duties, original admissions, defensive copying, absent/conflicting required IDs, mechanical N/A, unknown kinds, duplicate/missing coarse scopes, external input/seal pins, missing inventory membership, duplicate JSON/seal entries, original count consistency, no overwrite, unchanged input bytes, and metric-compatible preservation of U/N/A. A deliberate single-cell omission stays omitted: complete-cell truth is explicitly the prospective-seal boundary, with no inferred replacement obligation.

There are fewer than 300 files. Temporary CLI fixtures stay under this review directory and are removed; the generic base fixture, exact generic sealed inputs/output, source snapshots, original author logs, revised logs, and original admission records are retained. `FREEZE.json` pins every retained source, fixture, result, provenance excerpt and this documentation. No changes were made outside this review directory.
