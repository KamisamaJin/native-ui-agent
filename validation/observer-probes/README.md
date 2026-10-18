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


- `android-animation/`: an unrelated Material RadioButton/Checkbox reproduces a sampling discrepancy after a native callback. The original two-frame sample differs from a fresh render of the same final controlled state; eight-frame samples match the selected/checked glyph crops byte for byte. This only proves the documented standard controls/cadence, not that all animations settle at that cadence. All three business arms were recaptured with the same correction.
- `switch-probe/`: four actual iOS tests distinguish a semantic Switch container from its native activation leaf. Both old direct `.tap()` and new leaf activation succeeded in the minimal standard Switch probe; an explicit center-coordinate tap failed, so this is not evidence that all old `.tap()` calls fail. The revised adapter records semantic and activation frames/roles separately, verifies callback/value changes, and stops a missing-target search at the observed bottom with an unobserved outcome and no invented callback.
- `passed-production-import/`: the bridge imports the upstream module and renders the actual AlertToast View. One native test passes with the common explicit arm64 build configuration, covering the integration condition omitted by the earlier generic probe.
