# Independent review of the current AX calibration model

The native probe evidence is sound for its measured UIKit identity-transform scope.
The current classifier applies that scope more broadly than the evidence establishes.
Accept the transport/runtime observations, preserve the raw strict outcomes, and
withhold within-profile certainty when target semantics cannot be verified.

This review froze the current generic implementation before recommending guards.
`ASSESSMENT-1-SEAL.json` seals the source snapshot, raw context, reproducible checks,
and results. The reviewed `ax_calibration.py` SHA-256 is
`999aca80300904992087a4181b87f5f0c84db455aebe681b6a0014474544c8bd`.
It includes the axis-specific maximum extent guard. Later live edits are outside
this assessment. No probe, production, threshold, expectation, tolerance, or native
record was changed. No business study or known business-case value was inspected.

## What the native records establish

- V1 produced 612 target value strings, every one truncated to 512 characters and
  invalid JSON. The observer's session status was `passed`, which did not establish
  complete custom runtime values. V1 supplied no usable JSON geometry truth.
- V2 produced 612 complete values across 34 consistent snapshots, 210–272 ASCII
  bytes each. All 18 target identifiers were unique in every snapshot. Native
  UUID identity remained stable per view. Input hash, process/instance, fixture
  index, and event revision stayed bound; no callback metrics were introduced.
- Source and input hashes match the v2 probe seal. `initial`, `reswept`, and `final`
  report complete native sweeps with stable binding and content height.
- Actual UIKit bounds equal the sealed reference bounds exactly. Public in-process
  UIKit AX rectangles and exported XCUI rectangles agree exactly, including negative
  scroll coordinates. The independent runtime-based image projection and observer
  image frames also agree exactly. This last result verifies arithmetic agreement;
  it does not independently detect screenshot edges or visual touch boundaries.
- There are 18 independent view units: 12 fit and 6 held out, observed repeatedly
  in one process/context. The 612 rows are correlated observations, not 612
  independent views or environments.

The actual runtime records identify OS 26.5, screen/display scale 3, a 402 × 874
point app frame, and 1206 × 2622 screenshot pixels. These are observed values.
They must not become universal constants.

## Findings

### P1: Target scope is described but not verified by the classifier

`source-snapshot/ax_calibration.py:59–74` accepts profile status/provider, OS/scale
context, finite frame values, and coarse domain bounds. It does not require measured
evidence that the target is an identity-transform UIKit leaf with the same AX
semantics as the probe. A normal `native_geometry.py` proof contains a public AX
frame/provider/unit and explicitly says it is not full layout allocation; it does
not supply the missing target semantics.

The direct reproducible call using an actual probe frame and no target-scope proof
returns `definite_within_profile`. Adding explicit synthetic metadata naming a
custom SwiftUI AX target with `local_transform_identity:false` returns the same
classification: that metadata is ignored. No claim is made that such a target was
captured natively; this is a demonstration of the function's missing guard.

This matters even though raw F remains F. `requirement_routes.py` sends
`boundary_overlap` and `outside_calibrated_scope` to measurement review; a
`definite_within_profile` annotation can instead leave a failure on the product
diagnosis route. A scope disclaimer in prose does not prevent that routing certainty.
Ordinary external XCUI frames usually cannot prove these target semantics and must
therefore remain `outside_calibrated_scope`.

### P2: No positive error envelope was tested by this dataset

The fitter uses 149 fully visible rows: 87 fit and 62 held out. Every width/height
residual is exactly zero. Its factor of 1 is imposed by the lower bound in line 41;
it is not an estimate supported by a nonzero observed residual. The held-out records
also have zero residual, so they establish consistency on the held-out views but do
not test any positive error boundary, factor cap, coverage probability, or future
error bound. There is no statistical confidence or worst-case numerical proof here.

The sealed probe specification predates native execution, fixes the split and
reference-bounds tolerance, and forbids tuning tolerances from outcomes. It does
not predeclare this ULP formula, factor floor/cap, or 8-ULP position-coherence gate.
The code comment calling the model “predeclared” is not established by that seal.
Treat this as an exploratory empirical model until its method is separately fixed.
Do not add known failing values to the probe or widen the original P/F thresholds.

All complete raw records also show zero residual; the fully-visible filter did not
hide a positive residual in this run. Negative/large scroll translations exist in
the raw data but are excluded from the fitter's fully-visible set.

### P2: The accepted domain is broader than the sampled domain

The current axis-specific maximum extent check works: a height above the observed
height maximum is rejected, even when below the maximum width. However, the
coordinate guard combines x and y into one absolute maximum and has no lower size
bounds. Fully visible fitting rows have x 48.25–224.75, y 63.5–587.75, width
57.5–137.25, and height 23.5–76.25. Held-out visible rows extend y to 596.875.

Review-only calls with negative origins, x=500, or width=1 are all accepted as
`definite_within_profile`, despite lying outside the corresponding fitting ranges.
These are domain extrapolations. The held-out set also participates in constructing
the profile domain, although it does not participate in calculating the factor.
Matching even a precise bounding box would still not prove the envelope for every
unobserved point or semantic target inside it.

### P2: Context/provenance and unit checks rely on upstream trust

The actual run's hashes and runtime context verify successfully in this review.
However, `fit()` accepts caller-supplied context/provenance without checking them
against native rows or the raw observation. A synthetic unrelated OS/scale and a
non-digest provenance string still yield profile status `validated`. Pinning that
profile's bytes later does not itself prove its calibration origin.

`classify()` also ignores `source.unit`: a direct source marked `px` receives the
same point-based interval as one marked `pt`. The normal integrated producer emits
`pt`, and `design_contract.py` requires iOS geometry expectations in `pt`, so this
is not evidence of an actual mixed-unit native result. It is an unchecked API
invariant that must remain enforced at the calibration boundary if other producers
can call it. The same boundary should verify snapshot/source identity, rather than
trusting independent context and measurement dictionaries as a complete binding.

## Working invariants

The wrong-OS check returns `outside_calibrated_scope`. The current per-axis maximum
height check does so as well. The review's exact Fraction comparison remains F for
the neutral synthetic threshold; annotation preserves the original report, plan,
threshold, and status and only adds a diagnostic field. No epsilon, snapping,
correction, or tolerance change is introduced by the reviewed annotation function.

## Reproduction and artifacts

Run `python3 validation/routed-forward/calibration-review/reproduce_review.py` from
the repository, or use that script's absolute path from any working directory.
It imports the frozen generic source snapshot, verifies the probe seals and raw
record hashes, checks both transport runs, reproduces the fit, and exercises the
scope/domain/unit/binding boundaries without another native run. Its outputs are
deterministic `RAW-CONTEXT.json`, `RESULTS.json`, and `reproduced-profile.json`.

`SCOPE-GUARD-RECOMMENDATION.md` describes the minimum evidence guard. It is advice
written after the initial assessment was sealed, not a production change or a
retroactive adjustment to the fixture or model.
