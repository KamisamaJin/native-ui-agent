# Native geometry precision and cohort barriers

Android observation retains each matched SemanticsNode's actual integer pixel
size, Float position promoted without another Float operation, and native density
promoted to Double. `native_geometry` contains version1, provider
`compose_semantics_int_size`, coordinate_unit px, density, position_px, size_px.
The observer keeps the original rounded bounds as well; neither replaces the other.

`native_geometry.py` computes dimensions directly from integer extents/native
density. Same-frame gaps/insets use recorded native positions and extents with
exact rational operations. iOS reads CGRect width/height directly, avoiding
x+width-x cancellation. Reports retain actual values, exact numerator/denominator,
provider, source samples, selectors and snapshot indices. The approved expectation
and its separately sourced design tolerance are unchanged. There is no global
epsilon, pixel snapping, nearest accepted size or implicit physical-pixel tolerance.
Actual layout quantization remains observable; a design allowing it must state an
independent tolerance before implementation.

The upstream public AX provider can itself report near-boundary floating values
or transient dimensions while scrolling or settling. Direct CGRect evidence does
not certify that provider accuracy. Preserve such failures/conflicts and separate
them from confirmed product defects; do not silently round them into passes.

This repairs export/subtraction precision; it does not recover unknown SwiftUI
computed styles, unobserved boxes, layout allocation, glyph ink or OS touch regions.
Two unique fully visible boxes must share a coherent native frame for a relation.
Real conflicting geometry within a state stays unassessed. Unknown/malformed native
packets never fall back to a reassuring rounded result. Legacy observations without
these samples keep the original strict calculation, explicitly labeled legacy;
reacquire native evidence before claiming precision improvement. Historical grades
and screenshots must not be overwritten.

For a multi-candidate validation, `cohort_gate.py` seals all configured members
at once and checks exact prerequisites and artifact hashes before launch. Fix a
version1 config with artifact_root and stage graph (`members`, `requires`) before
work. `seal(registry, stage, member_to_file_list)` rejects missing members,
unsealed upstream stages, changed artifacts, path escapes and duplicate seals.
`authorize(registry, stage)` returns a timestamped digest-bound receipt only when
the whole upstream cohort is complete. CLI equivalents accept --registry, --stage,
--artifact-root for relocated archives, and --members for a JSON mapping.

The caller still checks actual workspace source against its sealed capsule and
records the authorization receipt before invoking the SDK. A barrier is a process
guard, not a secure sandbox against direct SDK invocation or a declaration that
maliciously omits cohort members. Pin cohort membership before design, preserve
rejected early-launch controls and audit actual command times against seals.

## Empirical AX calibration

`ax_calibration.py` fits a separately sealed neutral UIKit probe: public runtime
bounds/window conversion and raw XCUI dimensions, with disjoint fit/held-out native
identities. It uses binary64 ULP propagation, predeclared factor cap, fully visible
identity transforms, exact reference dimensions and matching runtime/density.
A failed holdout or out-of-domain input supplies no calibrated conclusion.
Configure a pinned `calibration: {path, sha256}` in the default service.

Calibration annotates a failed geometry row as `boundary_overlap`,
`definite_within_profile` or `outside_calibrated_scope`; it never edits raw status,
expectation, tolerance or acceptance. Boundary overlap routes to measurement review
without repeated SDK capture of unchanged code. This empirical UIKit model is not
a universal error bound for SwiftUI, glyphs, padding, touch regions or other OSes.
An uncertain strict failure remains a delivery blocker until independently supported
measurement resolves it; a small difference alone cannot become a pass. Preserve
raw records and the calibration context so a probe transport failure is distinguishable
from a product defect.

An OS/scale/domain match alone never proves the target is an identity UIKit leaf.
This implementation admits only an exact pinned probe-reference identity and raw
frame present in the profile; ordinary external AX packets lack that proof and
remain `outside_calibrated_scope`. The observed zero residuals validate agreement
of the collected records, not a universal positive-error bound. This deliberately
limits automatic calibration benefit rather than weakening thresholds.
