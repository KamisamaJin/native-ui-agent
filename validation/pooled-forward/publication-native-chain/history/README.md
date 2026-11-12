# Explicit shared-workflow history

This extension preserves raw historical shared-workflow bytes referenced by `fresh-platform-context.json` before later source/image/finish binding can update the live workflow files. It does not modify the frozen parent `native_chain.py` or `FREEZE.json`, live workflows, source, contracts, measurements, grades or mappings. It runs no SDK/device commands and acquires no locks, including on the recorded `ios.lock` file.

`checkpoint.py` is an author preservation tool; `history_view.py` is the pure archive reader. Their roles are deliberately separate. Original JSON and checkpoint bytes are copied unchanged. Metadata in the new ledger records their original absolute paths, required SHA256 values, claim/proof pins, Unix observation times and stable device/inode/size/mode/mtime/ctime identities. Read-only copies use fresh, content-addressed directories and mode `0444`. External hashes provide integrity; filesystem permissions are not an adversarial same-user immutability guarantee.

## Final checkpoint before binding

After all native scope records close, root should verify this extension's freeze and run a **fresh** checkpoint before any later binding:

```sh
python3 -B /ABS/pooled-forward/publication-native-chain/history/checkpoint.py \
  --root /ABS/pooled-forward \
  --output /ABS/pooled-forward/publication-native-chain/history/HOST/final-pre-binding-UNIQUE
```

The tool inspects the exact five potentially shared sibling-proof slots `T1/B/android` through `T5/B/android`. It first validates each native continuation claim and registered record namespace, then reads only its context-proof sidecar and the four explicitly pinned sibling files: `owner.json`, `ios.lock`, `ios.json` and `ios-backup.json` under that task's registered `B/hidden-workflow`. The special `T1/B/android` resumed record is supported. Source/contract/native-result/model/grade data is neither read nor copied by the preservation tool. The frozen native-chain verifier separately checks the full admission/continuation/native provenance.

Every copied original is read twice without following symlinks, and byte SHA and file identity must stay equal. Required historical SHA mismatches, missing old bytes, unexpected paths, changed proofs and ambiguous versions become explicit failures. No changed final value can substitute. Missing registry/proof slots remain explicit pending snapshot slots. Previously captured checkpoints are never overwritten or silently extended.

`LEDGER.json` reports `complete`, `partial` or `failed`. Here, complete means that all five history-proof slots are represented and all their required versions were preserved. It does **not** assert native collection completion, historical empty directories, current freshness, product quality or delivery. Root's terminal native collection and final checkpoint remain separate prerequisites.

The initial independent checkpoint is `HOST/actual-checkpoint-initial/LEDGER.json`: 16 preserved versions for T1–T4, with `T5/B/android` explicitly pending at capture time and zero failures. The companion validation record checks those copies through the history reader without reading mutable original workflow bytes. A later live claim does not retroactively complete this immutable checkpoint.

## Archive replay API

Archive and externally pin the ledger, raw copies and unchanged original claim/proof records. Independently validate the archive/index and create the ordinary frozen Resolver mapping **final current** originals and the historical copy files by their own original absolute keys. Then create a separate history view:

```python
from history_view import HistoryReader
from native_chain import verify_chain

# base is the frozen Resolver constructed with external map/index pins.
history = HistoryReader(base,
                        {"path": ORIGINAL_HISTORY_LEDGER_KEY,
                         "sha256": EXTERNAL_HISTORY_LEDGER_SHA256})
result = verify_chain(history, ORIGINAL_STUDY_ROOT,
                      {"path": ORIGINAL_NATIVE_CHAIN_SNAPSHOT_KEY,
                       "sha256": EXTERNAL_NATIVE_CHAIN_SNAPSHOT_SHA256})
```

The frozen verifier's `read_bytes/read_json/hash/directory` API supports this wrapper unchanged. Every history/copy/proof byte is read through the supplied base reader; the adapter opens no original or copied file directly. Embedded original paths and JSON bytes are retained. The ledger and copy pins are rechecked during reads.

Only the exact whitelisted original sibling paths named by the externally pinned ledger can return archived historical bytes. Any workflow path not selected by that view fails, even if a final file is present. Missing/changed copies fail without fallback to current originals. Sources, contracts, native measurements and other files retain ordinary base-reader behavior and original pins. Final workflow replay must use `base` separately; do not apply the historical view to a final-state/delivery check.

`HistoryReader(..., require_complete=False)` permits an explicitly partial historical selection for a scoped author check. The default requires all five history-proof slots and zero failures. This flag does not authorize whole-study native completeness or fill missing historical versions.

Directory access rejects any workflow subtree **or ancestor** that would mix final current files with selected historical versions. Ordinary disjoint namespaces pass through unchanged. The frozen native-chain verifier enumerates its evidence/capsule namespaces, which are disjoint from these workflow roots.

The path-only reader API cannot choose between multiple historical SHA values for the same original key. A ledger can preserve the raw versions, but this adapter refuses an ambiguous view rather than selecting a latest/first/current version. Such a conflict must remain unresolved or use independently scoped views; one frozen whole-chain replay cannot pretend a single original key simultaneously contains two versions. No such conflict was found in the initial 16-file checkpoint.

## HOST controls and limits

Run `python3 -B .../history/test_history.py`. Each author attempt retains code snapshots, fixture roots, logs and results. Controls cover missing/changed copies with no fallback, changed final originals, forbidden source/contract/native overrides, unregistered proof paths, malformed provenance, duplicate JSON/versions, multiple-version ambiguity, mixed directories, pending scopes and registration changes during copying.

Tests include a real frozen Resolver restore with absent original paths, plus the frozen parent native-chain verifier on a complete **synthetic** cohort after its current workflow bytes have changed. The ordinary final view fails the earlier pins; the history view verifies the same chain with zero mutable original workflow reads. These tests contain invented native/source/image bytes and earn no native acquisition or product credit. The unchanged frozen verifier and synthetic generator are vendored with exact pins; the test producer configures its workflow root to the actual registered `hidden-workflow` namespace before generating synthetic files.

The first integration attempt exposed a synthetic fixture namespace mismatch (`workflow` versus the registered `hidden-workflow`). The whitelist correctly rejected it; the failed test/code/fixture/log remain retained. The fixture producer was corrected before writing test files. The frozen verifier and history whitelist were unchanged.

Checkpoint timestamps and inode values attest what this read-only preservation run observed. They do not prove the file existed unchanged at every earlier time or establish independent human identity. Keep the archive and restored view read-only, authenticate all external pins, and retain failed/ambiguous checkpoints. No actual product conclusions, grade/result/model content or X/Y mapping were accessed for this extension.
