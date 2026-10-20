# Reproduction

## SDK-free evidence verification

Run from repository root with Python 3.11 and the root Skill's requirements:

```sh
python -m pip install -r native-ui-agent/scripts/requirements.txt
python -B -m unittest discover -s native-ui-agent/tests
python -B validation/state-forward/verify_tools.py
python -B validation/state-forward/verify_generic.py
python -B -m unittest discover -s validation/state-forward/design/private -p 'test_*.py'
python -B validation/state-forward/verify_trial.py
python -B validation/state-forward/verify_evaluation.py
python -B validation/state-forward/metrics.py
python -B validation/state-forward/costs.py
python -B validation/state-forward/build_tables.py
python -B validation/state-forward/failure_index.py
python -B validation/state-forward/artifacts.py
```

The repository workflow also runs historical verification against immutable
publication aliases. Its old trial hashes and literal scores remain unchanged.
Grader controls are synthetic checks of the evaluator, not natural defect
findings. Archived native inputs, source fingerprints, PNGs and original output
are the evidence; recomputing arithmetic is not a new simulator run.

## Native collection

Actual command arrays, command times and exits are retained in each corpus and
per-case `*-command.json`; original native manifests attest actual observer,
bridge, production sources and inputs. `portable-sha256.json` inventories the
portable files. `portable-scope.json` describes omitted build caches and system
diagnostic videos. All collected assertion PNGs and native failure logs remain.

The trial used the pinned Reply and AlertToast revisions recorded in
`common-host/equal-hosts.json`, JBR 21, the local Android SDK, Xcode 27.1 and iOS
26.5 iPhone 17 Pro simulators. Own arms have separate derived checkouts and
simulators. A new environment can create fresh derived checkouts using
`validation/dispatch-forward/bootstrap.py`; never restore experiment capsules
into an unrelated working checkout.

`experiment.py capsule` records source hashes and copies upstream licenses.
`experiment.py restore` accepts only a workspace under this trial's ignored
`cache/` directory. `experiment.py collect` runs one real iOS and one real
Android worker, preserves nonzero exits, and checks source immutability after
every case. Local runtime paths are explicit constants at its top; adjust a
copy for another machine and preserve that new operator's provenance.

`prepare_inputs.py` translates the independent frozen inputs into native
stimulus/navigation routes. Builders sealed their own additional observation
plans before feedback. Own FINAL runs retain those exact original plans and
actions. Common acceptance uses a separate deterministic target selection;
`prepare_grading.py` creates additive actual-step pointer mappings without
rewriting any sealed native inputs.

This archive permits replaying actual captured facts. Re-running a coding
agent, simulator navigation or screenshot review is a new experiment and may
produce different output. The independent design/acceptance, source capsules,
original reviews, all successful and unsuccessful captures, stage seals and
assignment release establish this run's chronology rather than promising
deterministic model behavior.
