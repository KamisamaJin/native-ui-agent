# Independent neutral forward probe

The small iOS/Android QuietMomentCard component met its frozen contract on the first implementation. Both platforms were rendered at normal and narrow/large-text configurations. Every final run has 14 passed, 0 failed, 0 unassessed applicable assertions; each 16-cell matrix also contains 2 explicit N/A stimulus cells. No defect was seeded and no component fix was required.

| Final run | Original frames | Bound assertions | Environment |
| --- | ---: | --- | --- |
| android-normal-v2 | 7 | 14/14 passed; 2 N/A | P |
| android-narrow-large-v2 | 7 | 14/14 passed; 2 N/A | P |
| ios-normal | 11 | 14/14 passed; 2 N/A | P |
| ios-narrow-large | 16 | 14/14 passed; 2 N/A | P |

The design freezes component-owned canvas/accent fills, separate wrapping/overlap propositions, exact native 64-unit band height, both caller titles, activation callback and callback silence after replacement. Zero RGB channel tolerance is used. Pixel results concern the approved sample regions, not every canvas pixel. One review context read the original images; two independent visual judges and panel acceptance are not established.

Design canonical SHA256: `43fa75fc638806d1102453f0fd079406c896a184840297e6e7ea37897793f07d`.
Policy canonical SHA256: `bcfcecff2744eea4d6a6d8f1ff33248307a843d1cd450c94dda6bead4bf1c3fc`.

The iOS normal native viewport is 390×600pt and narrow is 260×600pt; actual Dynamic Type is large/accessibility3, light, ltr. The iPhone 17 simulator uses iOS 26.5; Xcode 27.1 compiles the arm64 host against SDK 27.1. The requested 390 Android viewport is actually 389.81818dp at 2.75 density because the pinned provider uses integer 1072px; narrow is 260dp/715px. Original exact-unit environment checks F/P remain in original-environment-checks.json. After root updated the shared metadata interface, fresh v2 acquisitions use the separately recorded explicit provider encoding with unchanged 390/260 requests and pass P/P. This is a prefreeze tool revision, not a retroactive change to original evidence.

The original bundled iOS LazyVStack capability probe executed 1 test but failed all 6 full-content sweeps because native content height changed by 58–59pt as lower content materialized. Native callbacks and same-process quiet replacement succeeded. Its original failed images, xcresult, logs and unassessed coverage remain intact. A separate original eager-stack generic probe passed all 6 overlapping sweeps; it does not convert the lazy result into a pass.

All component actions dispatched successfully (xcui_tap / compose_onclick), delivered acknowledged, then caller replacement advanced input with no callback in the same PID/session. The iOS narrow states require 2 overlapping frames each, with stable state-bound content heights 798.3333/802.3333pt. Large text and action hyphenate naturally and remain readable.

Native execution wall times (seconds):

| Invocation | Seconds | Result |
| --- | ---: | --- |
| android-narrow-large | 3.297 | captured_not_graded |
| android-narrow-large-v2 | 13.316 | captured_not_graded |
| android-normal | 4.293 | captured_not_graded |
| android-normal-v2 | 4.565 | captured_not_graded |
| ios-narrow-large | 34.980 | passed |
| ios-normal | 18.502 | passed |
| preflight-android | 27.889 | captured_not_graded |
| preflight-ios | 140.764 | failed |
| preflight-ios-eager | 85.816 | passed |

The exact commands, exit codes, UTC starts, wall durations and stdout/log hashes are in commands.jsonl. Phase-times.json retains native build/test/export timing and JUnit timing. Parallel intervals overlap; no fictitious independent authoring/reading stopwatch is claimed. The first observed clock is 00:48:11 UTC and final report time is2026-10-22T00:59:28.624338+00:00.

No real application page/navigation, Android physical touch, keyboard, lifecycle, screen reader journey, all text styles, whole-canvas color coverage or physical hit area was tested. Generic public iOS AX cannot establish computed SwiftUI font/color/padding. No business study SDK run, subagent, commit, push or Skill write was made by this context. One own reporting-helper syntax error is retained alongside its fix; it is not a tool failure.

Created simulator: A23C7E6D-E267-4C1D-85E0-1A480EFC0BAF. It was shut down after the final capture. The final seal covers all non-cache evidence artifacts and the source snapshots; cached dependencies/build artifacts have their own native manifest hashes.
