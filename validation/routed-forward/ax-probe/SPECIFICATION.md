# Sealed native numerical calibration probe, transport v2

This self-contained fixture measures 18 actual accessible UIKit `UIView` leaves
inside `UIViewRepresentable`, returned by the public `ObserverBridge.make` interface.
It contains no business UI, business-specific sizes, callbacks, or layout fixes.
`fixtures.json` fixes the 328 × 2280.375 point canvas and each leaf's declared bounds
and placement. The bridge has matching intrinsic, `sizeThatFits`, and SwiftUI frame
sizes, so the existing host has finite full-content geometry to sweep.

The dimensions and positions were authored before any native execution. Twelve views
are the fit set; six are held out by identifier. Every held-out width, height, x
placement, and y placement is absent from the corresponding fit dimension. This is
an identifier-level split: repeated observations after scrolling are correlated and
must not be counted as independent new views. `samples.json` is the machine-readable
split and predeclared reference table. `SEAL.json` records exact source/input hashes.
Do not retune the split or reference table after native results.

The first sealed version's native capture completed with full coverage, but its
runtime JSON values were truncated by public XCUI transport at exactly 512
characters. The extractor rejected those incomplete values; no profile fit was
performed from them. The complete original source/specification seal is preserved
in the sibling `ax-probe-v1` directory. This v2 revision changes only transport,
extraction, and supporting specification. Fixture geometry, split, tolerances,
and actions retain their original file hashes. Its seal links the original seal.

## Native runtime truth

Each leaf is independently accessible under its unique `axprobe.pNN` identifier.
Its `accessibilityValue` getter samples public UIKit geometry synchronously and emits
compact JSON with wire version `v:2`. The JSON reports the actual `UIView.bounds`,
public `UIView.accessibilityFrame`, `convert(bounds, to: window)`, local transform,
ancestor transform identity, attached screen scale, actual OS version, instance UUID,
and `ObjectIdentifier(self)`. Declared bounds alone are not runtime evidence. Before
using declared sizes as calibration truth, verify actual runtime bounds against the
sealed reference table.

The value getter detects ancestor scrolling through freshly converted geometry.
It changes its cached value and geometry revision only when that measured geometry
or attachment changes. It never invokes `onEvent`, so layout observations cannot
advance the observer's callback revision. There is no timer, display link, private
UIKit API, screenshot parsing, or override of `accessibilityFrame` in the fixture.
The default public accessibility frame is therefore a separate in-process oracle
for the existing observer's public XCUI snapshot frame. Instance identity should stay
stable through scrolling and full sweeps in the same process.

The compact wire keys are `b` (bounds), `a` (public accessibility frame), `w`
(window-converted bounds), `t` (actual affine components a/b/c/d/tx/ty), `p`
(ancestor transform identity), `s` (screen scale), `os` (OS version), `m` (attached
measurement), `i` (reference identifier), `u` (all 128 instance UUID bits as 32 hex
characters), `o` (actual object identity as hexadecimal), and `r` (geometry revision).
Each rectangle array is x/y/width/height. The extractor restores descriptive semantic
field names and rectangle objects without rounding or correction. Split membership
comes from the unchanged sealed sample table, rather than consuming wire space.

The getter emits complete native metrics only when the ASCII JSON is below 480
bytes, leaving margin below the observed 512-character XCUI truncation boundary.
Otherwise it emits a short explicit unavailable marker with the attempted length;
the extractor rejects that marker. Non-finite geometry similarly remains unavailable.
No value is shortened by changing its numeric precision. `--preflight-transport`
checks representative worst-case serialization before native execution: long signed
fractional coordinates beyond this canvas's range, full-length identity fields,
large geometry revision, and a long OS version. `TRANSPORT-PREFLIGHT.json` retains
those synthetic byte counts. This is a serialization check, not native evidence.

## Checkpoints and native invocation

Use the existing `native-ui-agent/scripts/ios_observe.py run`, omitting `--package`
because this is a self-contained probe. Supply `AXProbeBridge.swift`, `fixtures.json`,
and `actions.json`, a chosen native simulator, and a fresh output directory. Native
SDK execution of v2 is deferred until after the revised source/specification seal.

With the existing `state_capture:true` protocol, `initial` is a complete overlapping
sweep. The actions then scroll upward twice, capture `after-two-generic-up-scrolls`,
and request the complete `reswept` checkpoint. The fixture remains unchanged; this
creates a second generic scroll/sweep checkpoint under the same input and callback
revision. Automatic `final` may also be retained by the observer. The tall matrix
places some offscreen views at large positive screen coordinates initially and
negative coordinates after scrolling. Retain all observed values; do not clamp them
to the viewport or replace offscreen coordinates with zero. If native AX omits an
offscreen leaf, record it unavailable rather than inferring its frame.

After native observation:

```sh
python3 /absolute/path/ax-probe/extract_calibration.py \
  --observation /absolute/fresh-native-output/observation.json \
  --output /absolute/fresh-native-output/calibration-rows.json
```

The extractor imports no candidate geometry code. It preserves runtime and XCUI
frames, numeric residuals, view identities, sample split, state/binding fields,
and visibility. Its independent image projection uses the in-process public UIKit
accessibility frame plus measured app frame and screenshot dimensions; it does not
derive its expected frame from the candidate's reported XCUI frame. This separates
native AX transport error from later image-coordinate projection error. Native
screen scale is reported, never hard-coded to the current simulator's scale.

## Precision and semantic limits

Inputs are binary-exact integers and multiples of one eighth or one quarter point.
The predeclared tolerance for confirming the runtime reference bounds is 0.000001
point. All AX and projection residuals remain unrounded; no post hoc tolerance or
correction is built into this fixture. Only consistent captures with matching
runtime bounds and identity local/ancestor transforms are eligible for the intended
numerical comparison. Report separate held-out errors after any fit is fixed.

Local `UIView.bounds`, a screen-space accessibility frame, and screenshot pixels
have different meanings. A transformed, combined, clipped, custom-accessibility,
SwiftUI, or text view can expose an AX boundary that differs from its local layout
bounds. This probe calibrates numerical transport and projection for the observed
identity-transform UIKit leaves and current environment. It cannot establish a
universal conversion from AX width/height into a component's layout size, touch
region, internal padding, text metrics, or visual design correctness. The public
in-process AX frame is also not an independent screenshot-edge detector.
