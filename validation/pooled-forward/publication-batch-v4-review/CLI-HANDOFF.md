Use the complete revision-v4 directory together: batch.py, exact material-v3, EMITTER-SCHEMA-v3.json and the sibling three-file presentation library. Batch SHA256 is 5f9e7d9e5708dbbb14dad36de73d874f79613add09a052840ce2039efd6b117c; schema SHA256 is 2d8605a83df3f1a6b028e4d989f17b2bd97ec87b0016d0f5172fa5a353dc0af6; material SHA256 is 4783735c450d882c7fcf62e5a1192dacafa96352fee899023a8e67a12e2e94ac. Parent must review/admit this separate frozen revision uniformly. This reviewer has run neither invocation on actual inputs.

Set PREPARATION_ID to a new ASCII letters/digits/hyphens identifier. Retain any failed v3 attempt and use fresh selection, intermediate and packet namespaces. Supply externally recorded original absolute paths and SHA256 pins as CAUSE_INDEX, CAUSE_SHA, NATIVE_SNAPSHOT, NATIVE_SNAPSHOT_SHA, NATIVE_RESULT and NATIVE_RESULT_SHA. Rehashing a changed original does not create authority. The native result must bind that exact snapshot/root, all30 scopes and the original files_read inventory; the unchanged full-cause verifier runs before map, manifest, event, report, source or image reads. The production mapping pin remains unchanged.

The single selection invocation is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward/publication-batch-v4-review/revision-v4/alarm-material-tools-v4/batch.py prepare --root /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward --id "$PREPARATION_ID" --cause-index "$CAUSE_INDEX" --cause-index-sha256 "$CAUSE_SHA" --native-snapshot "$NATIVE_SNAPSHOT" --native-snapshot-sha256 "$NATIVE_SNAPSHOT_SHA" --native-result "$NATIVE_RESULT" --native-result-sha256 "$NATIVE_RESULT_SHA"
```

Record the returned selection_seal.path and selection_seal.sha256 externally as SELECTION_SEAL and SELECTION_SHA. Selection writes fifteen SPEC.json/DERIVATIONS.json pairs and then ALL-SPECS-SEAL.json under operators/cohort2/coordination/alarm-material-selections/$PREPARATION_ID. Neutral intermediates remain under cache/business/blind-quality/alarm-intermediates/$PREPARATION_ID.

The single all15 packaging invocation is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward/publication-batch-v4-review/revision-v4/alarm-material-tools-v4/batch.py build --root /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward --id "$PREPARATION_ID" --selection-seal "$SELECTION_SEAL" --selection-seal-sha256 "$SELECTION_SHA"
```

Build checks every all15 selected original/derived/spec/document byte pin and replays derivations before creating the first packet. ALL15-PREFLIGHT.json precedes packet creation. Packet root is cache/business/blind-quality/alarm-packets/$PREPARATION_ID; operator ledgers are in the selection directory's packaging child. Capture the returned packets_seal externally. The output index schemas/APIs are unchanged from v3: ALL-SPECS binds original_root/current cause/groups/code pins; ALL-PACKETS follows selection_seal and binds group packet/ledger refs. A dispatcher must verify those links and its separately admitted code pins. These commands never dispatch a reviewer.

V4 changes only the source-pinned file classifier. It preserves whole direct-child attachment JSON and factual workflow reports, retains exact provenance controls in the original raw archive, and rejects unrelated unknown JSON. Unknown factual/projection schemas still fail closed; see REVIEW.md. Keep original bytes and original pins recoverable. No SUT, criteria, expected value, quality denominator, business outcome or presentation finding is changed by this candidate.
