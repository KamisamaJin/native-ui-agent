# Independent three-task design cohort

This directory contains three unrelated native component tasks authored without production source, native SDK execution, prior trials, probes, reported bugs or implementation screenshots. All numeric/style/behavior expectations, public inputs and hidden input combinations were fixed before implementation.

- T1 ExpeditionPackPanel: expedition equipment, shared weight capacity and required shelter.
- T2 PublicationRightsPanel: publication channels, conditional exclusive rights and quote totals.
- T3 CafeGroupOrderPanel: group drinks, serving limits, member savings and reusable cups.

Each task has 22 rule families, 6 selected states, 3 cases and both native platforms: 792 complete denominator cells. P1 is light at width390, normal type; P2 is dark at width320, xxxLarge/1.6 text; H1 is a different ordinary seed/input combination and caller replacement. Two original full sweeps and five non-sweep actions per case. Five non-sweep actions include same-mounted-component caller replacement. Explicit disabled attempts retain unknown callback behavior if no successful dispatch occurred.

Builders receive only their task's public directory and must not read public/compiled. They must compile plans themselves with the frozen design_contract.py and the approved digest in approval.json. Common observation/grading uses only the sealed compiled artifacts. Every compiled case root has fixtures.json and actions.ios.json/actions.android.json, alongside ios/android subdirectories.

The SDK-free oracle entry is `<Tn>/private/grader.py:grade`; controls run with `python3 -B <Tn>/private/test_grader.py`. All 18 final controls pass for each task. An original synthetic-test aliasing error is preserved before correction; no production mutations were introduced. The full source and test logic are sealed through each task SEAL.json. Native tools are pinned through TOOL-PINS.json. COHORT-SEAL.json commits to all three task seals and shared design files.

Do not modify sealed design, acceptance, grader, references, inputs, precision or controls after implementation starts. Fixing a later independently discovered design error requires a new separately approved cohort revision, never a changed expectation to fit implementation output.
