# Recorded native acquisition chain

`native_chain.py` independently checks the recorded initial/final native acquisition and licensed continuation chain. It performs no SDK/device commands, process execution, permission changes, cleanup, original-file writes, product grading, treatment comparison or judgment replay. It does not import the controller or operator runners. Frozen source copies in `schema-code/` are reference/test bytes; only the separate pure Resolver is imported by an author application or restore test.

The expected cohort is five tasks × `{I,A,B}` × `{ios,android}`: 30 effective scopes. An intact chain is separate from complete acquisition and delivery. Honest native failures remain explicit records. `status: verified` means the declared records pass these structural checks; it never means every scope acquired facts, every product passed, or delivery was accepted.

`recorded_native_first_executions` counts recorded fresh inner executions. `acquired_scopes` additionally requires the original receipt's observation pin and nonempty pinned image inventory. An execution with incomplete native fact bindings consumes its one-shot attempt and cannot become a replacement sample; it leaves `acquisition_complete: false`. Product F/U outcomes do not disqualify an otherwise intact observation packet.

## API and trust boundary

After independently verifying an archive against its external index pin, restore its original bytes and use the frozen publication Resolver:

```python
from native_chain import verify_chain
from resolver import Resolver

reader = Resolver(RESTORED_MAP_ABSOLUTE_PATH,
                  map_sha256=EXTERNAL_MAP_SHA256,
                  index_sha256=EXTERNAL_ARCHIVE_INDEX_SHA256)
result = verify_chain(reader, ORIGINAL_POOLED_FORWARD_ROOT,
                      {"path": ORIGINAL_SNAPSHOT_ABSOLUTE_KEY,
                       "sha256": EXTERNAL_SNAPSHOT_BYTE_SHA256})
```

The reader supplies `read_bytes(original)`, `read_json(original)`, `hash(original)` and `directory(original)`. The verifier uses original absolute keys throughout; every byte read goes through `read_bytes`, every final byte check through `hash`, and filesystem Paths returned by `directory` are used only to enumerate verified restored namespaces. It never opens an original path as a fallback. Original JSON is parsed strictly without rewriting embedded paths or bytes. Duplicate keys and nonfinite JSON fail. Forbidden mapping, grade and worker-content references are rejected before byte access.

The caller must independently authenticate the external snapshot/map/index pins and keep the restore read-only throughout replay. A self-selected pin, populated restore or recorded reviewer identity is not proof of historical absence, a person's identity, or the impossibility of bypassing the original collection procedure. The verifier rechecks accessed files and enumerated namespaces before returning. The Resolver is a verified read API, not an adversarial same-user filesystem sandbox.

## Snapshot contract

A separately pinned JSON snapshot has:

- `version: 1`, `kind: "recorded-native-chain-snapshot-v1"`, and the exact `original_root`.
- `anchors`: exact `{path, sha256}` references under that original root for every name in `native_chain.ANCHORS`: manifest, original initial cohort, cohort seal, hidden authorization, canonical preparation seal, acquisition order, continuation authority, v3 entry permit and remaining plan.
- `terminal_scopes` and `pending_scopes`: lists whose concatenation is the exact frozen 30-scope schedule. Terminal scopes must be a prefix. Excluded scopes are pending **in that snapshot**; this is not an inference about a newer live collector.
- `terminal_records`: exactly one row for each declared terminal scope, with pinned `claim`, `outcome` and positive owned `closure` references. A terminal failure may point to its recorded explicit cleanup closure; it is not upgraded to acquisition.
- `episodes`: pinned terminal episode records, including all 15 original episodes and the later continuation/remaining segments that register the selected effective outcomes. Original failures and subsequent failures are separate records.
- `collection_controls`: pinned original collection entry/start/end, v2 entry/start/failed, v3 entry/start, and a final v3 end or failed record in whole-study mode.
- `complete_record_namespace`: `false` for a prefix, `true` only for the fully terminal cohort. Whole-study mode enumerates the complete independent-evaluation namespace and requires the exact 30 original claims, 28 continuation claims and 59 licensed original/continuation/resumption native record directories. Later claims and replacement native records cannot be silently omitted from a whole-study pass.

Additional descriptive fields are allowed in the snapshot. They confer no authority. Missing required restored evidence fails; it is never relabeled pending by consulting current originals. The snapshot may live outside `original_root`, but its exact original key and external byte pin must be supplied.

## Checks

The verifier checks the original event SHA chain and unique source-lock/self-seal/cohort/hidden-authorization order, terminal public request registration, complete initial/source cohort, canonical initial bytes against original paired capsules, exact capsule byte counts and SHA domains, and recorded source-root order/identity. It reads seal bytes but never self-claim contents. The separate frozen publication-audit-v2 verifier remains responsible for full public controller/D0/deadline replay.

It checks the fixed 28-scope continuation permit against its pinned index/review **and independently rechecks** the original claim/outcome, exact ownership-guard error, original request and recovery commands, source before/after, SDK observations, sidecars, positive owned closure and recorded absence assertions. Missing restored files alone never prove zero forwarding. Existing or ambiguous acquired facts cannot receive a continuation sample. The one v3 preclaim entry permit is limited to `T1/B/android`, its exact three failed entry files and distinct resumed namespace. The prior 11 continuation acquisitions and remaining 17-scope order remain pinned.

Effective operations bind version-aware frozen runner/entry, one-shot reservation, config/profile admission and original dependency registry, full source capsule before/after, request/receipt, original cycle/capture pins, execution-contract inputs, copied native runtime bytes, original image membership and hashes, and positive same-owner resource journals. Platform-selective captures retain stable original root indices and distinguish the controller `{sha256, bytes}` file domain from the native path-to-SHA domain. Observation and automatic-result bytes are hashed; their assertions, outcomes and image judgments are not evaluated.

Recorded v3 shared-workflow context proofs bind the same-arm sibling's first native claim/cycle/capture, original service inventory/context/state, owner and recorded checkpoint pins. Historical freshness remains a recorded admission, not a conclusion drawn from today's files or missing restore members. Resource closure checks original positive receipts/journals and monitor closure; they do not inspect or act on current host resources.

Preserve the original checkpoint bytes named by historical context-proof pins. Later review operations can update a shared workflow path. A one-version-per-original-key restore containing only a later file cannot satisfy an earlier exact byte pin; the verifier fails instead of substituting that later state, rewriting the original JSON, or claiming historical freshness from file absence. This prerequisite is separate from the successful pre-v3 prefix application, which does not contain v3 context proofs.

Cross-process ordering uses recorded Unix endpoints with an explicit scope label. V3 shared `CLOCK_MONOTONIC` endpoints are checked where present. Earlier process-local monotonic origins are checked only within their own operation and are never joined across processes. This is not a cost/clock ledger or a metric computation.

## Author applications and controls

Run the self-contained synthetic HOST suite with:

```sh
python3 -B validation/pooled-forward/publication-native-chain/test_native_chain.py
```

Each invocation retains its code/test snapshots, per-control fixture roots, `RUN.log` and `RESULT.json` under `HOST/`. Synthetic tests use invented source/contract/native/image bytes and original keys below `/recorded/native-study`, which does not exist. The frozen Resolver is exercised on both a prefix and a complete synthetic virtual restore with explicit map/index pins. Synthetic images are not native PNGs; these tests earn no native, business, quality or independent-review credit.

`record_prefix.py` is a separate author-only read-only original-artifact recorder. It writes snapshots and application records only inside this publication directory. It never runs SDKs, acquires a collection lock, edits collection files, or rewrites original JSON. For a later fully closed archive application, create a fresh 30-scope snapshot after terminal records exist, authenticate its external pin, archive/restore its dependencies, then invoke the portable API above. A read-only original application is not an archive/restore acceptance.

The author real application is explicitly the **pinned pre-v3 13-acquisition closed prefix/as-of checkpoint**: the two original `T1/I` acquisitions and the 11 registered v2 acquisitions. The remaining 17 scopes are excluded/pending in that snapshot even if the live collector has since progressed. Final root publication must separately apply whole-study mode to all 30 terminal scopes. Native acquisition remains distinct from product F/U/P, quality and delivery.

All development failures are retained and described in `HOST/DEVELOPMENT.json`; they are verifier/test infrastructure findings, never product defects or treatment outcomes. `FREEZE.json` binds exact final code/test/docs/reference and author-result byte pins. No prior product conclusions, anonymous X/Y map, judge grades, image judgments, worker prompts, selfclaims or findings were read for this review.
