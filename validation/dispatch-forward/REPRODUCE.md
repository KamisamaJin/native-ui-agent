# Reproduce and audit

This experiment compares **common-v3** (v3 plus the shared successful-dispatch
correction) and **candidate-v4** (the same correction plus observation optimizations).
Both arms use the Skill. It is not a new no-Skill comparison.

## Audit the published evidence without native SDKs

From a clean checkout, Python 3.11+:

```sh
python -m pip install -r native-ui-agent/scripts/requirements.txt
python -B -m unittest discover -s native-ui-agent/tests -v
python -B validation/dispatch-forward/verify_generic.py
python -B validation/dispatch-forward/run_evaluator_controls.py
python -B validation/dispatch-forward/verify_trial.py
python -B validation/dispatch-forward/verify_blind_stages.py
python -B validation/dispatch-forward/verify_evaluation.py
python -B validation/dispatch-forward/metrics.py
python -B validation/dispatch-forward/observation_facts.py
python -B validation/dispatch-forward/costs.py
python -B validation/dispatch-forward/build_tables.py
python -B validation/dispatch-forward/build_failure_index.py
python -B validation/dispatch-forward/verify_artifacts.py
```

The checks validate original source/input/image identities, the shared dispatch
gate, independently recomputed overlapping scroll intervals, frozen expectations,
phase order and published arithmetic. They do **not** rerender native UI or turn a
manual image judgment into a deterministic universal style inspector. The
timestamped original synthetic-control reports are restored byte for byte after
each fresh control replay.

`original-v3/`, `common-v3/`, and `candidate-v4/` are immutable tool copies. The
published `native-ui-agent/` files equal the candidate freeze. Design, evaluator
preparation versions and all previous failed attempts remain separate artifacts.

## Rerender an archived production component

Use a Mac with Xcode and an installed iOS simulator runtime for iOS; Android uses
JDK 21, the Android SDK and the pinned Reply Gradle project with Paparazzi/Layoutlib.
This experiment used Xcode 27.1, iOS 26.5 and iPhone 17 Pro. Different runtimes,
fonts and toolchains may produce different native results. SDKs, simulator
runtimes, upstream checkouts and compiler caches are not distributed here.

Create a fresh host using `bootstrap.py --help`, supplying your own absolute JDK
and Android SDK paths. The helper checks out the pinned upstream revisions and
installs the common test dependencies. `install_capsule.py` then installs an exact
sealed D0 or FINAL source into that dedicated host:

```sh
python validation/dispatch-forward/bootstrap.py --help
python validation/dispatch-forward/install_capsule.py \
  validation/dispatch-forward/private/submissions/SUBMISSION/final \
  /absolute/path/to/fresh-host
```

Run the collector CLI directly so all machine paths are explicit. Replace the
uppercase placeholders and choose a published case such as C01. Output directories
must be fresh. iOS uses the archived production Swift package and public bridge:

```sh
python validation/dispatch-forward/candidate-v4/scripts/ios_observe.py run \
  --package /absolute/path/to/fresh-host/alerttoast --product AlertToast \
  --bridge validation/dispatch-forward/bridges/Bridge.swift \
  --fixtures validation/dispatch-forward/private/inputs/final/C01/fixtures.json \
  --actions validation/dispatch-forward/private/inputs/final/C01/actions.json \
  --simulator YOUR_SIMULATOR_UUID \
  --developer-dir /Applications/Xcode.app/Contents/Developer \
  --build-cache /absolute/path/to/new-build-cache \
  --output /absolute/path/to/new-ios-evidence
```

Android calls the production Compose component through the archived bridge:

```sh
python validation/dispatch-forward/candidate-v4/scripts/android_observe.py run \
  --project /absolute/path/to/fresh-host/reply/Reply \
  --bridge validation/dispatch-forward/bridges/ObserverBridge.kt \
  --fixtures validation/dispatch-forward/private/inputs/final/C01/fixtures.json \
  --actions validation/dispatch-forward/private/inputs/final/C01/actions.json \
  --java-home YOUR_JDK_21 --android-sdk YOUR_ANDROID_SDK \
  --output /absolute/path/to/new-android-evidence
```

For the old collector substitute `common-v3` and omit `--build-cache`. Native
captures start fresh processes/inputs and receipts; a valid build-cache hit never
reuses an old screenshot. `trial_operator.py` contains this experiment's recorded
machine paths, so direct collector commands are preferable on another machine.

The original component identifiers are a local contract for this newly implemented
feature. The experiment does not prove automatic localization of arbitrary legacy
pages from vague prose. Both bridges decode inputs and forward callbacks; the
business UI and calculations live in the real production modules. This test scope
does not include the original app's navigation, backend or real network behavior.

Android activation here is **Compose semantic OnClick in Layoutlib**, not an OS
touch on an emulator or device. iOS uses XCUI taps in a simulator. Neither semantic
bounds nor screenshots prove a physical hit region, universal effective font
attributes or internal padding. Those unsupported aspects remain U.

## Original versus portable records

`evidence/` retains native PNGs, raw observations, exact inputs, native summaries,
command logs and compiled host sources. `portable-sha256.json` binds every retained
file. DerivedData and xcresult build caches are excluded; any omitted automatic
system diagnostic video has its hash and reason in `portable-scope.json`. All
assertion screenshots are retained. Historical absolute paths are provenance,
not dependencies on the original workstation.

`private/` is published only after all blind phases seal and assignment is
released. Its bounded source capsules, original reviews, compile failures and
phase ledger are included; unbounded local native build directories are excluded.
Anonymous grading capsules duplicate original native bytes so their relative
locators remain self-contained. Review projections change only identity/path
strings and corresponding derived-file hashes; original claim values and native
image bytes remain unchanged, and original reviews are also published.
