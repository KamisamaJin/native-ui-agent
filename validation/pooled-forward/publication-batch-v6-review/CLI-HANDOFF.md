Use the complete revision-v6 directory together. Batch SHA256 is 6ababef0d4ea03242a03a1a89bfaefc2006253b0b6384d983577e16b39ad1332; EMITTER-SCHEMA-v5.json SHA256 is 7149cb0873e30cfe3690e0b64c1f7d711c916c927a313f0a82e19d1841acbda9. Material-v3 remains 4783735c450d882c7fcf62e5a1192dacafa96352fee899023a8e67a12e2e94ac. APIs, output index schemas and all function bodies are unchanged from v5. Parent independently admits the complete revision uniformly; this reviewer has not run either invocation on actual inputs.

Use a fresh PREPARATION_ID containing ASCII letters/digits/hyphens and preserve prior failures. Set CAUSE_INDEX, CAUSE_SHA, NATIVE_SNAPSHOT, NATIVE_SNAPSHOT_SHA, NATIVE_RESULT and NATIVE_RESULT_SHA to externally recorded original absolute paths and SHA256 pins. Do not repin changed originals or retag old actual selection proofs. The unchanged full cause barrier runs before actual map/event/report/source/image reads; the production mapping pin is unchanged.

The single selection invocation is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward/publication-batch-v6-review/revision-v6/alarm-material-tools-v6/batch.py prepare --root /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward --id "$PREPARATION_ID" --cause-index "$CAUSE_INDEX" --cause-index-sha256 "$CAUSE_SHA" --native-snapshot "$NATIVE_SNAPSHOT" --native-snapshot-sha256 "$NATIVE_SNAPSHOT_SHA" --native-result "$NATIVE_RESULT" --native-result-sha256 "$NATIVE_RESULT_SHA"
```

Capture the returned selection_seal.path and selection_seal.sha256 externally as SELECTION_SEAL and SELECTION_SHA. Fresh SPEC/DERIVATIONS pairs and ALL-SPECS-SEAL.json are written under operators/cohort2/coordination/alarm-material-selections/$PREPARATION_ID; neutral intermediates remain under cache/business/blind-quality/alarm-intermediates/$PREPARATION_ID.

The single all15 packaging invocation is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward/publication-batch-v6-review/revision-v6/alarm-material-tools-v6/batch.py build --root /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward --id "$PREPARATION_ID" --selection-seal "$SELECTION_SEAL" --selection-seal-sha256 "$SELECTION_SHA"
```

Build checks all15 raw/derived/spec/document proofs before writing packets. Record the returned packets_seal externally. Fresh packet root, preflight, ledgers and summary locations are unchanged. Any dispatcher must bind this newly admitted batch/schema pin set and follow the unchanged cause/selection/packet links. These commands never dispatch a reviewer. Unknown report names, protected factual identities and unsupported body schemas still stop; no extra aliases or outcome fields were added.
