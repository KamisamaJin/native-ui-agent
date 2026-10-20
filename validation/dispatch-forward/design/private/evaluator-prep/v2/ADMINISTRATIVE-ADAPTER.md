# V2 administrative provenance adapter

The original design seal and initial PREP-SEAL remain unchanged. This adapter was
prepared before any candidate source/evidence was delivered to the evaluator.
It reads only the two additionally authorized frozen producer files for input
serialization format. It does not change expected rows, native activation methods,
callback/stimulus gates, evidence criteria, native field matchers, visual protocol,
business eligibility, or denominators.

## Relocated archives

V1 pinned dependencies with original absolute paths. V2 keeps exact pinned hashes
and resolves the known dependency paths relative to the relocated repository,
derived from this versioned evaluator's fixed directory. It imports the same
shared contract.py, which imports the same native_checks.py. It verifies the two
producer source hashes as serialization-format provenance as well. Absolute JDK
and jar locations in probe-provenance.json document the independent probe command
only; the grader does not open those caches or require their presence.

A cache-free relocation control copied only the sealed design, normalized plans,
pinned shared dependencies and v2 evaluator/profile files to a temporary repository
under this private preparation directory. Both shared imports and both encoding
profiles succeeded there without the original repository paths or JVM caches.

## Actual native input identity

Both producers bind a CURRENT MODEL serialization hash:

- iOS ObserverApp.swift: JSONSerialization.data(withJSONObject: fixtures[index],
  options: [.sortedKeys]), interpreted as UTF-8, then SHA-256.
- Android NativeObserverTest.kt: current.toString().toByteArray() on the parsed
  kotlinx JsonObject, then SHA-256. Parsed property order is preserved.

The captured fixtures.json file SHA remains an immutable artifact identity and is
retained separately. V2 does not compare that whole-file digest to input_sha256.
It decodes the exact model at /initial or /updates/0 from that captured file,
preserving input member order, and matches the sealed model with typed recursive
equality. The producer starts at input index 0 and moves to 1 for that replacement.

Independent synthetic Foundation and JVM kotlinx probes establish byte encodings.
The seven frozen vectors include Unicode/emoji/Arabic, all ASCII control characters,
slashes, quotes, backslashes, newlines, Booleans, integer values, reversed order,
and a caller replacement. The Python profiles match every actual probe byte.
Foundation sorts model members and escapes forward slashes. Kotlin preserves
parsed member order and does not escape forward slashes. Both use compact UTF-8
JSON with the probed control-character escapes. The profiles are restricted to
the established flat ASCII-key String/Bool/32-bit Int model domain; unsupported
primitive types, invalid Unicode, missing/corrupt profiles or unknown platforms
produce native-encoding U rather than a provenance bypass.

For each snapshot and successful requested dispatch, V2 checks the exact current
model digest. A replacement also checks binding_before against the exact initial
model digest and binding_after against the replacement model digest. The common
callback gate still separately requires same instance/process, requested route,
correct input-index movement, event revisions and interval receipts. Source/input
facts can never replace that native dispatch gate.

Reports add only compact input_encoding_provenance and evaluator_adapter metadata.
The former records the file artifact SHA, native model SHA, optional previous-model
SHA, model pointer, profile/probe/source hashes and byte count. It contains no
derived watering amounts or synthetic callback. Runtime capability parsing remains
as initially frozen; this version does not substitute source/native-declaration
facts for unsupported native inspection evidence.

## Controls and immutable parent

All 43 original controls run against V2 via a separate regression copy that changes
only paths/output name. The original control source and report remain sealed.
Additional encoding/provenance controls include successful current-model binding
on each platform, successful replacement before/after binding, and rejection of
whole-file hashes, wrongly sorted Android hashes, unescaped iOS slash hashes,
wrong previous-model hashes, unknown encoding domains, missing profiles, and
absolute-path dependency assumptions. No candidate is involved.

normalization-verification.json checks the original design/preparation commitments,
unchanged normalized plan bytes and every expected value, plus unchanged shared
gate and matcher function syntax. V2-SEAL.json commits all files in this version
directory except its own envelope. Later adaptations require a new version and
cannot alter this seal.
