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
