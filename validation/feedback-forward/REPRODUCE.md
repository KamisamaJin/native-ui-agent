# Reproduce the evidence and inspect the methods

The SDK-free replay checks original data; it does not re-render components or turn
retained UI failures into passing examples. Python/Pillow are required:

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 -B validation/feedback-forward/test_metrics.py
python3 -B validation/feedback-forward/test_delivery_metrics.py
python3 -B validation/feedback-forward/test_final_outcome_metrics.py
python3 -B validation/feedback-forward/test_implementation_audit.py
python3 -B validation/feedback-forward/test_source_outcomes.py
python3 -B validation/feedback-forward/benchmark_summary.py --check
python3 -B validation/feedback-forward/verify.py
python3 -B validation/feedback-forward/build_summary.py --check
python3 -B validation/feedback-forward/build_failure_index.py --check
python3 -B validation/feedback-forward/artifacts.py
```

`PREREGISTRATION.md`, `METHODS-PRE-DESIGN.json`, the retained first engineering
revision, `METHODS-RELEASE.json` and `gates/` show when methods, source and findings
closed. `baseline-v8` is the exact previous Skill; `candidate-v9` is the released
increment. This is an incremental v8/v9 repair comparison. Both arms share the
optimized native execution/final-check services. Shared backend speed cannot be
credited as an exclusive repair-policy advantage.

`neutral/` fixes source and coverage before launch. `neutral-captures/` retains all
eight full paired runs, and `benchmark-summary.json` retains order/cache/stages,
coverage and supported-status comparisons. `neutral-targeted*` are explicitly
partial feedback runs, not equal-full-coverage speed comparisons. Independent
review folders and failed engineering/operator attempts are preserved separately.

For a new SDK replication use an owned simulator and new output directory, keeping
all published original evidence unchanged. Install the pinned upstream hosts using
local tools appropriate to your machine, restore the selected source capsule's
production files byte-exact, and use the generic Skill CLI with that case's approved
plan/lock/fixtures/bridge and externally approved canonical digests. For example:

```sh
python3 native-ui-agent/scripts/execution_plan.py --run \
  --plan <case/platform/plan.json> --design-lock <design-lock.json> \
  --design-sha256 <approved-lock-digest> --fixtures <approved-fixtures.json> \
  --bridge <original-bridge> --launch-source reference \
  --launch-pointer /launch/P1/ios --source-root <actual-production-source-root> \
  --environment <approved-environment.json> --environment-sha256 <approved-digest> \
  --policy <policy.json> --policy-sha256 <approved-policy-digest> \
  --package <actual-AlertToast-package> --simulator <owned-UDID> \
  --developer-dir <installed-Xcode-Developer-directory> --output <fresh-output>
```

Android uses `--project`, `--java-home` and `--android-sdk`; it runs Paparazzi/JVM,
not a physical device. The source-root set defines the measured scope; include all
changed production roots. Toolchain/source/fixture/dispatch/image records remain
available in every original run. A different SDK/device/renderer is a new replication,
not permission to replace frozen data or expected values. The study operators record
this machine's paths; portable generic tools accept your own explicit paths.

Public final independent grading uses the SAME full source-bound final bytes as the
consumer's own final check, never a separate common re-render. Hidden caller inputs
are exercised only after every final source/public/self-check endpoint closes.
Unknowns, disagreements, failed captures and budget overruns remain in the reports.
The complete self-check endpoint includes the shared source-only review and a
fresh check of the actual Swift module/caller at the declared minimum source API.
Source judgments are reported separately from runtime/visual truth. The compiler
check does not claim an older-OS link, archive or runtime execution.
The combined workspace also needs the upstream-relative source namespaces
`Sources -> alerttoast/Sources` and `app -> reply/Reply/app`. Original source-gate
failures exposed this shared setup omission. `source_views.py` installs explicit
internal directory links and proves production hashes unchanged; original
definitions, expectations, catalog bytes and native evidence stay fixed. Portable
capsules retain those relative links and the publication inventory checks their
literal Git paths and targets. This recovery and its actual latency are shared
infrastructure evidence, not an exclusive v9 repair result.
A green repository CI means integrity/recomputation checks passed, not that every
experimental component passed its business/visual acceptance criteria.
