# Current-host runtime admission v2

Use this CI entry point with Linux, Python 3.11 and Pillow 11.3.0 already installed:

```sh
bash validation/pooled-forward/publication-runtime-admission/ci-python311-v2.sh
```

It creates a fresh owned `HOST/ci-python311.*/admission` artifact containing a new current-host runtime/code inventory, full installed wheel/dist-info license texts and metadata, exact source snapshots, fixed-evidence comparisons, logs, all 23 unchanged generic replay controls and seven mechanism controls. Required checks have no skip option. It uses current-host native libraries, never Darwin libraries on Linux.

The direct invocation is:

```sh
python3.11 -B validation/pooled-forward/publication-runtime-admission/admit_runtime_v2.py \
  --target linux-py311 \
  --output validation/pooled-forward/publication-runtime-admission/HOST/UNIQUE-CI-RUN
```

`README.md`, `FREEZE.json`, the first sources and all first results are retained unchanged. Pre-handoff review found that the historical fixture transport copied `PIL/` but not separately pinned sibling wheel libraries. That would fail the required real-Resolver control on manylinux wheels carrying `pillow.libs/`. V2 adds exactly those declared support bytes to the **new synthetic restore**, with a dedicated roundtrip control. `CURRENT-HOST-FIXTURE-TRANSPORT-DIFF.patch` records this narrow change; the historical helper remains intact. No historical JSON or expected evidence is rewritten.

The current-host driver still differs from historical replay only by explicit support-library inventory/layout verification. The frozen worker, both A/B backends, fixed golden JSON/PNG bytes, and all 23 generic test bodies remain unchanged. The existing actual-data barrier and unsupported source-domain/source-responsibility/delivery boundaries remain in force.

The fixed golden expected catalog/manual/report comes from the separately frozen historical generic author run. Both backends must match it exactly, so the new runtime does not create its own expected answer or self-approve arbitrary data. Package and distribution versions must both be exactly Pillow 11.3.0. Every wheel-owned package/support byte and full dist-info license text is preserved and pinned in the **new** inventory. Historical runtime/inventory and its 66,498-byte full license remain separately pinned and untouched.

Author validation of v2 passed seven mechanism controls, both A/B golden comparisons and 23/23 generic replay/corruption/U controls on **Darwin arm64 / CPython 3.9.6 / Pillow 11.3.0**. The Linux target was also invoked on Darwin and correctly failed; it was not skipped or reported as Linux success. Linux/Python 3.11 execution remains for root's CI preflight. Its fresh result will state the actual host, interpreter, wheel bytes and license pins. Admission is limited to this fixed generic replay scope, not actual study data or unsupported source/domain behavior.

`RUNTIME-ADMISSION-v2-FREEZE.json` is the current extension freeze. `FREEZE.json` remains the preserved first revision. See `README.md` for the common runtime/license limits; v2 supersedes its six-control count and first CI command only.
