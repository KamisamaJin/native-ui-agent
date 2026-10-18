# Native observation capability evidence

These are unrelated, simple capability probes, not the new business task's outcome tests. They establish what the observation host actually executed before product assertions are judged. They do not establish generic SwiftUI style properties or real-app navigation/lifecycle correctness.

- `passed-390-dark/`: actual App+XCUITest, native AX/frames,390×600 viewport,3× display scale, callbacks, explicit same-process caller replacement, bidirectional reveal, disabled blocking and full bottom/required-target coverage.
- `passed-320-light-accessibility3-rtl/`: same assertions at320 width, accessibility3 and RTL. The two final preflight runs executed2 native UI tests and76 snapshots. Requested and actual environment are separate in the evidence.
- `failed-initial-offscreen-tap/`: earlier unsuccessful attempt retained; initially offscreen tap produced no invented callback. Subsequent adapter support reveals bounded targets through recorded ordinary scrolls.
- `android/`: continuous-frame experiment establishes native semantics callback and external replacement in one attached ComposeView. A failed detached-snapshot attempt is also retained.
- `android-final/`: corrected unclipped geometry supports bottom-to-top reveal, callback, external replacement and actual bottom sampling. Clip-aware frames and raw placement have distinct meanings. Android semantics actions/programmatic ScrollState do not prove physical OS touch or Activity behavior.

`verify_preflight.py` rechecks archived native counts, hashes, process identity, event deltas and coverage. It does not run Xcode/Gradle or repeat an image judgment. Original xcresult and DerivedData remain in ignored local cache, with portable exact images/JSON/logs/source fingerprints retained here.

## Later integration correction

The initial iOS preflight linked the upstream package but its generic bridge did not `import` or render the package's View. Consequently it did not expose the x86_64 host/arm64 package mismatch that the new real component bridges encountered. This is a preflight coverage limitation, not a product bug. Common explicit architecture settings are documented in `../fresh-blind/host-amendments.json`; all affected iOS captures are rerun before grading. The original Skill and probe evidence are preserved. A follow-up package-importing native probe additionally instantiates the real upstream AlertToast View before product runtime results are graded.
