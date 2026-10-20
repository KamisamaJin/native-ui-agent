# V3 original native PNG geometry clarification

V1, V2, their seals, every design expectation, shared native callback gate, native
matcher, pixel tolerance, and initial manual protocol remain preserved. V3 corrects
only the coordinate calibration used by the pixel-geometry administrative adapter.
No candidate source, candidate PNG, candidate observation, outcome, or generic
evidence file was opened. The example metadata was supplied directly in the
authorized preparation request. All controls use generated original synthetic PNGs.

## iOS image and frame coordinate spaces

The frozen iOS producer's app.screenshot() covers the full App. Its PNG does not
cover only the narrower 320/390-point component viewport. Use the original
snapshot.app_frame and the original PNG dimensions:

- scale_x = original_png_width / app_frame.width.
- scale_y = original_png_height / app_frame.height.
- Require finite positive dimensions and agreement between these two scales.
- If original runtime.screen_scale is present, cross-check both computed scales
  against it.
- If original screenshot_pixels metadata is present, its integer width and height
  must equal the dimensions in the original PNG header.
- Never substitute PNG.width / viewport.width for a full-App PNG.

Native iOS frames are absolute app screen coordinates. Project a point by
((native_x - app_frame.x) * scale_x,
 (native_y - app_frame.y) * scale_y). Project a rectangle's origin with that
translation and scale its width/height. The component viewport's location and
width may differ from the App frame. Nonzero and negative App origins are valid;
they must be subtracted rather than silently assumed zero.

For the authorized metadata shape App 402×874, PNG 1206×2622, viewport 390×600
at (6,62), both scales equal 3. The viewport projects to [18,186,1188,1986].
A 320-point viewport inside the same App retains scale 3. This is a coordinate
example, not candidate evidence or a component style assertion.

The original manual protocol's generic sentence describing scale through viewport
width applies only when that viewport is the complete captured surface. For iOS
full-App captures, this clarification supplies the actual producer format.

## Android attached-view coordinate space

The frozen Android producer's PNG covers the complete attached Compose view.
Its original snapshot.logical_viewport_dp contains that view's width and height.
Use PNG.width / logical_viewport_dp.width and
PNG.height / logical_viewport_dp.height, checking their agreement. Native
bounds_dp are already relative to that attached view, so the projection origin is
(0,0). Do not infer the missing logical width from a requested environment width,
a source literal, a component viewport, or a screenshot guess.

## Measurement and unavailable evidence

Use the same 0.01 native scale-agreement tolerance already used by the initial
format validator. This is a metadata agreement check, not a change to any sealed
component/pixel tolerance. Geometry segments remain original native pixel
coordinates. Their reported scale must agree with the calibrated full captured
surface. Segment length divided by that validated scale is compared by the
unchanged frozen numeric matcher.

Missing App frame, conflicting original PNG dimensions, width/height scale
disagreement, or conflicting reported screen scale leaves calibration U. A
manual measurement that declares the known-wrong viewport/crop scale is rejected.
Missing Android attached-view dp dimensions leaves U. There is no viewport-ratio,
source-declaration, visual-size guess, or default-scale fallback.

The calibration helper exposes project_rect for preparing annotations in original
PNG coordinates. Color-patch interpretation and native bounds/typography/padding/
hit-region matching are unchanged. Projection establishes coordinate conversion
only; it never establishes a source-derived native styling fact.

## Versioning and controls

V3 reuses the byte-identical V2 input encoding profiles and pinned shared
dependencies. The 43 original controls and 40 encoding/provenance controls run
against V3 unchanged except copying the additional geometry helper into the
synthetic relocated archive. Twenty-nine new controls cover original PNG/frame
calibration, both offered host widths inside a 402-point App, origin translation,
viewport-derived scale rejection, crop/metadata conflicts, missing App frame,
Android's actual attached-view fields, and integrated synthetic geometry
measurement. No business grades are generated.

normalization-verification.json verifies all earlier sealed files, unchanged
normalized plan bytes and expected values, and unchanged gate/matcher syntax.
V3-SEAL.json is a separate immutable preparation commitment.
