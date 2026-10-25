# Independent after-check of the revised scope guard

The revised implementation closes the ordinary external-XCUI application path:
an ordinary source proof without `calibration_reference` now returns
`outside_calibrated_scope`. Exact probe-record membership also blocks the negative
origin, x=500, and width=1 extrapolation controls from the first review. The raw
strict failed status, threshold, original report, and original plan remain unchanged.

This is a separate assessment. The original `ASSESSMENT-1-SEAL.json` and top-level
review `SEAL.json` remain valid and unchanged. This after-check reviews frozen
`ax_calibration.py` SHA-256
`528eefb12ef9e081e5af0a6b0ece40ffa392bb2bf496f49e5e4de4226103e1b7`.
No production/probe edits or new native SDK runs were performed by the reviewer.

## Controls that pass

- Missing reference, wrong extraction digest, wrong reference identifier, or even a
  one-ULP frame mismatch returns `outside_calibrated_scope`.
- With a matching digest/identifier/frame, the exact recorded probe sample can be
  diagnosed. This checks record membership; it does not infer a new target's type.
- Fit now rejects views with inconsistent runtime OS, reference identity, false
  local-transform flags, or false ancestor-transform flags, even when the extraction's
  eligibility boolean remains true. An unrelated supplied context no longer fits.
- The same actual native records reproduce factor 1 with 87 fit and 62 held-out
  fully visible rows. The profile scope now explicitly states that zero observed
  residual does not validate positive residual behavior.
- Ordinary external measurement annotation adds only the outside-scope diagnostic.
  The exact Fraction comparison still fails against the unchanged neutral threshold.

## What these checks do not prove

The new `scope_proven` predicate in lines 78–81 is an equality lookup on
caller-supplied extraction-digest/identifier fields and the source frame. It does
not authenticate a target's runtime identity, snapshot, process/session, or native
class. A review-only dictionary can copy a genuine probe reference and frame while
naming an unrelated target, false transform identity, a different process, and an
unrelated snapshot; the function still returns `definite_within_profile`.

That synthetic control is not a new native observation and is not runtime scope
proof. The ordinary integrated producer currently emits no such reference, so its
external sources safely remain outside. Keep that producer boundary explicit;
adding this metadata to a business source must never be presented as equivalent to
the probe's measured in-process geometry.

Fit similarly still trusts provenance strings and the consistency of its input
dictionary. Correct context plus non-digest provenance is accepted. Contradicting a
native transform matrix while leaving the identity booleans true also fits. The
sealed extractor derives those flags from measured affine values, so these synthetic
dictionary controls do not allege a contradiction in the actual native records.
They show that fit's added checks validate metadata consistency, rather than
independently authenticating the native capture or extraction.

A matching reference with `source.unit:"px"` is also accepted directly. Normal
integrated iOS proofs are `pt`, as enforced upstream; future producers must preserve
that boundary or the classifier should reject contradictory units itself.

All actual residuals remain exactly zero. No positive residual envelope, factor cap,
future numerical guarantee, universal SwiftUI layout property, screenshot edge, or
touch region was established by these controls. The original limitations about
method predeclaration and repeated observations remain in force. No known failing
case, new probe dimension, model tuning, or changed P/F tolerance was introduced.

## Reproduce

Run `python3 validation/routed-forward/calibration-review/after-check/reproduce_after_check.py`
from the repository, or invoke the script's absolute path. It checks the original
review seal and native input hashes, imports this after-check's frozen source, and
writes deterministic `CONTROLS.json` and `reproduced-profile.json`.

Disposition: the ordinary-source fail-closed guard and the new fit metadata checks
work as described. Exact recorded-probe membership is useful for replay diagnostics;
it must not be described as independently verified runtime scope for a different
target. Leave generic external XCUI sources outside, and retain all raw strict
outcomes and the zero-residual model limitation.
