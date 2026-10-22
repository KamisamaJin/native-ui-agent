# Original-byte publication completion

The first v8 commit `f9ce51a4` and its [failed CI](https://github.com/KamisamaJin/native-ui-agent/actions/runs/39738733296)
remain unchanged. The full decoded job log is preserved in `first-ci-failure.log`.
All historical regressions and the 115 tool / 9 metric tests passed; the new study
guard then rejected a missing original Xcode result dependency before any regrading.

The portable inventory excluded `.xcresult`, but the preimplementation neutral
probe's complete stage seal still referenced 274 original result files (41,576,227
bytes). Local files masked that publishing omission. These are original test
results, not SDKs or new acquisitions. Every added payload must match the original
preimplementation seal SHA. Another gate refers to `design-v2/SEAL.json`, while Git
published `design-v2/seal.json`; the local case-insensitive filesystem masked that
case-only reference. Preparation materializes the missing spelling from the unique
Git-published file only after verifying the exact original bytes. No duplicate-case
Git filenames or modified gate hashes are required.

`publication_closure.py` is a generic publication guard, validated by seven unrelated
SDK-free controls. It compares every sealed literal path with the actual Git index,
rejects omissions, changed bytes, ambiguous case matches and unsafe paths, and never
overwrites a different alias. This is shared publication infrastructure, not a v8
quality or speed gain and not business-case tuning.

No frozen Skill, evaluator, nine shared adapters, design, product source, stage seal,
expectation, original finding, grade or metric changes. `COMPLETION.json` adds an
explicit immutable inventory for this publication correction. The original v8
`ARTIFACTS.json` remains byte-exact. Only the current README and CI workflow change;
their first-publication bytes are retained under `original-mutable/` and verified
against the original manifest in an isolated historical publication view.

Run from repository root after a clean checkout:

```sh
python3 -B validation/publications/atomic-v8-completion/test_publication_closure.py
python3 -B validation/publications/atomic-v8-completion/verify_completion.py --prepare
python3 -B validation/atomic-forward/verify_adapters.py
python3 -B validation/atomic-forward/verify_study.py
# Run the original derived --check commands in atomic-forward/REPRODUCE.md.
python3 -B validation/publications/atomic-v8-completion/verify_completion.py
```

The last command replaces a direct current-root `atomic-forward/artifacts.py` call:
it runs that unchanged checker against its exact original publication scope and
also verifies all completion bytes. The full-workspace frozen study checker verifies
the restored original gate dependencies and unchanged numerical/qualitative results.
The first failed publication is not relabeled successful or silently overwritten.
