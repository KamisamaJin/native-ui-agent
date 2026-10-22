# Recompute the atomic-review forward study

Use Python 3.11 for the CI replay and Pillow 11.3.0, the actual image decoder used
in the native study host (Python 3.9; see `operators/python-runtime.json`). The
Skill's supported dependency range remains in `scripts/requirements.txt`;
the publication/CI command additionally pins this study's decoder. SDK-free verification does not launch
a native application or ask a model to replace the sealed judgments:

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt 'Pillow==11.3.0'
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 -B validation/atomic-forward/test_metrics.py
python3 -B validation/atomic-forward/verify_adapters.py
python3 -B validation/atomic-forward/verify_study.py
python3 -B validation/atomic-forward/build_summary.py --check
python3 -B validation/atomic-forward/costs.py --check
python3 -B validation/atomic-forward/grading_costs.py --check
python3 -B validation/atomic-forward/observation_costs.py --check
python3 -B validation/atomic-forward/action_scope.py --check
python3 -B validation/atomic-forward/build_tables.py --check
python3 -B validation/atomic-forward/build_gallery.py --check
python3 -B validation/atomic-forward/failure_index.py --check
python3 -B validation/atomic-forward/disagreements.py --check
python3 -B validation/atomic-forward/artifacts.py
```

`verify_study.py` verifies frozen release bytes, approved original plans, source
capsules, complete cohort prerequisite seals and native launch chronology. It
recomputes shared acceptance from the original raw observations and the two
unchanged anonymous judgment requests, then recomputes the prospective metrics.
`artifacts.py` additionally checks every published file hash and size, including
rejected attempts. A green integrity check does not mean all UI assertions passed.

`action_scope.py` separately audits the original public own/common launch inputs.
The common package uses base routes without the generated plans' four after-target
observation extensions. Both arms share that gap; fixtures and bridges agree.
Missing observations remain unknown, original claim evidence is not replaced, and
own-to-common elapsed time is not a same-route collector-speed comparison. See
`ENGINEERING.md` for the acquisition-scope limitation and prospective follow-up.

The graded publication's assignment disclosure follows the study's `reveal` gate.
The orchestrating root and owner are privileged; only the fresh quality-assessor
contexts are assignment-blind, as detailed in `ENGINEERING.md`. Private
designs and the assignment are included in the published manifest after disclosure;
they must be retained when exporting a clean checkout for verification. The
`baseline-v7` and `candidate-v8` directories are byte inventories of the actual
tested tools. Prior releases remain under their original study paths, with changed
publication dependencies resolved by `validation/publication_history.py`.

Actual acquisition uses the upstream Reply commit
`53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79` and AlertToast commit
`76a1c1793cd3443001c20c6033beb84453b25d9f`, the pinned thin host, Xcode/iOS
Simulator 26.5 and Paparazzi/Compose JVM rendering. The latter performs semantic
actions rather than Android emulator touch. Original command JSONs record device,
tool, source/input hashes, authorization, times and exits. `compile_only.py` does
not render. `experiment.py` authorizes each acquisition against the complete
required cohort before invoking an SDK.

This run's producer and acquisition paths are intentionally write-once. Re-running
SDK commands into these directories would destroy provenance and is refused. A new
development experiment needs a new directory, fresh devices, a new preregistration,
independent design, assignment and model contexts; its numbers must be reported
separately. The original PNGs and native JSON are sufficient for the published
offline review-tool comparison, without any additional screenshot acquisition.

The native evidence captures component behavior in controlled hosts. It does not
establish generic computed SwiftUI styles, arbitrary uninstrumented legacy-app
navigation, physical hit areas, backend behavior or full-brief coverage outside
the selected atomic ledger. Independent AI consensus is preserved evidence, not a
human gold standard.
