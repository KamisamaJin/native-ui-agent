# Authored design system

The SVGs are independent structure references, never candidate screenshots or pixel
regression baselines. Numeric tokens are native units in tokens.json. Preserve the
stock package/product and Android theme; the component sets these explicit local
surface/type values inside the theme rather than changing a global theme.

Host: offered 390, vertical viewport 600, LTR, light, 16 horizontal inset and 24 top
inset. iOS Dynamic Type Large; Android fontScale 1.0, native density 2.75, requested
390x600 through paparazzi-float32-screen-config-v1. Requested width is not a rounded
actual viewport assertion. Actual Android screen pixels are1072x1650 at density2.75.

Component: fill offered child width, opaque surface #FFF7F9FC, corner radius12,
16 native units inner padding. Header title24 semibold (600), body/context/notes15
normal (400); all text left aligned with ink #FF15243B, secondary text #FF526174.
Use system/SansSerif fonts, no bundled or custom typeface. Root/detail captions16
semibold, visible content ordered title, context, notes, root caption/options,
detail caption/options, summary, confirmation, status, receipt, primary action.
Every block has12 native units vertical separation. No fixed total content height.
Notes may be empty. All supplied strings retain their full content and wrap.

Choice rows: native Button, minimum48pt/dp semantic control height, full width,
8 corner radius, solid #FFFFFFFF fill when unselected, #FFE5F1FF when selected.
Unselected outline1 #FFB8C5D6; selected outline2 #FF2459A6. Inner content inset16,
label15 normal, left aligned, check indicator at trailing edge16 from the edge
only while selected. Disabled labels/indicators #FF526174; enabled labels ink.
Keep the whole Button's native frame around the styled row. Disabled selected rows
retain the selected fill/check; there is no opacity modifier on the whole control.

Confirmation: same row geometry and selected cues, native button toggling selected.
Primary: full width, minimum48pt/dp native control height, corner8, centered label16
semibold; enabled solid #FF2459A6 with #FFFFFFFF text, disabled solid #FFD9E1EC
with #FF526174 text. Lock after recording through native disabled semantics.
Summary is16 semibold ink; status and receipt15 normal muted. No shadows, icons
other than selection checks, gradients, translucent fills, or animations.

Surface gutter pixel sampling: normalized x.02–.035, y.20–.80 within the actual
component surface semantic box. Inner padding keeps children outside the gutter.
Use visible-fragment scope for an oversized surface. Row/button gutter sampling:
x.02–.035, y.25–.75 in the actual control box, outside text/check ink and rounded
corners. Expect opaque dominant sRGB with zero channel tolerance, at least12pixels,
minimum support0.90. These are rendered samples, not computed style/color claims.

Geometry assertions measure the actual native semantic/control accessibility box,
not effective padding or physical touch area. Full-content states have wrapping,
overlap, horizontal clipping and type-hierarchy visual atoms. Intermediate states
have explicit target sets and local fill/check/control facts, without claiming a
whole-state scan. No extra decorative measurement nodes are introduced.
