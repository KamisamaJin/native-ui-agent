# Native iOS observation adapter

`scripts/ios_observe.py run` generates a thin app and XCUITest target. The caller's
bridge instantiates the actual production component. The adapter supplies no
business component, labels, action behavior, or design expectations.

## Caller bridge

Supply a Swift file with this signature, importing the production package:

```swift
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any],
                     onEvent: @escaping (String) -> Void) -> AnyView {
        // Return the real production component, mapping its real callbacks to onEvent.
        // UIKit components can be wrapped in UIViewRepresentable here.
    }
}
```

The factory receives the current fixture each time SwiftUI evaluates it. An explicit
host button applies the next fixture without relaunching the app. The host does not
force a new view identity; bridge state/update semantics remain the caller's concern.
The bridge must expose stable unique accessibility identifiers on the actual targets
that the test should operate. Callback names and callback routing are caller-owned.
Use `__observer.*` only for the observer's host controls.

The host offers width 320 or 390 points and a 600-point native vertical ScrollView,
with horizontal padding 16 and top padding 24 inside that parent. Thus actual child
content width is offered width minus 32. A bottom sentinel follows the component.
Fixture update, runtime metadata and callback receipt controls sit outside that region.
The app supplies preferred light/dark scheme, SwiftUI Dynamic Type, and layout direction.
Package font registration/resources and app-specific environment objects belong in the
bridge when needed. This shell is component integration evidence; use the real app's
E2E route for navigation, safe-area, keyboard, or lifecycle claims about that app.

## Inputs and execution

```json
{
  "initial": {"arbitrary": "caller values"},
  "updates": [{"arbitrary": "new caller values"}],
  "width": 390,
  "theme": "dark",
  "dynamic_type": "large",
  "direction": "ltr",
  "canvas_color": "#FFFFFF",
  "required_identifiers": ["actual.primary", "actual.last"],
  "max_scrolls": 18
}
```

Dynamic Type accepts `xSmall`, `small`, `medium`, `large`, `xLarge`, `xxLarge`,
`xxxLarge`, `accessibility1` through `accessibility5`. Direction accepts `ltr` or `rtl`.
Actions are a JSON array, at most 40 actions:

```json
[
  {"type": "tap", "identifier": "actual.primary", "reveal": true, "expect_callback": "primary"},
  {"type": "apply_next_fixture"},
  {"type": "capture", "name": "updated"},
  {"type": "scroll", "direction": "down", "until_identifier": "actual.last", "max_steps": 12},
  {"type": "tap", "identifier": "actual.last"}
]
```

`scroll` without `until_identifier` takes one step by default. Each step drags within
the native parent by roughly half its viewport, preserving overlap. The runner
captures top, before/after every action, each scroll step, and bottom. It then attempts
bounded bottom coverage even if actions did not request scrolling. The required
identifier list should include relevant lower content. Absent required identifiers
or an unreached sentinel fail coverage; they cannot become a pass. Identifiers must
select exactly one existing XCUI node before a tap. The target must be enabled and
hittable. For native Switch containers, the runner resolves a unique native Switch leaf and
records both `semantic_target` and `activation_target`, including roles, frames and
selection paths, before activating the leaf. Ambiguous, disabled or inaccessible
activation targets stop the action. Other targets retain native `.tap()`.
An event is recorded only when the bridge's real callback invokes onEvent.
An optional `expect_callback` requires the named callback in that action's real delta.
Without it, an empty callback delta does not itself fail a tap; the caller must check
expected callback semantics from `steps[*].callback_delta`.

An optional `canvas_color` (`#RRGGBB`) paints the parent ScrollView and outer canvas,
leaving the production component's own surfaces intact. When omitted, the host uses
native system background. `runtime.actual_environment` and manifest
`actual_environment` record the native child SwiftUI environment's scheme, Dynamic
Type category, layout direction and display scale, separately from requested fields.

`tap` supports `reveal: true` and bounded `max_steps` (default 18, maximum 24). It
uses the unique target's measured frame to choose up/down native parent scrolling,
retaining every overlapping scroll screenshot. If a lazy target is absent, it searches
downward by default; `direction: "up"` is an explicit search hint for an absent upper
target. It records `reveal_diagnostics` when the bound expires or a missing target search
reaches the fully visible native bottom sentinel. This is bounded observer evidence,
not proof that the production target is absent. An unexecuted action cannot pass a
business assertion. `scroll` with `direction: "auto"`
and `until_identifier` uses the same helper. An element larger than the viewport
cannot pass full-containment coverage.

`tap` with `allow_disabled: true` can observe a fully visible, unique native disabled
target without issuing a tap. Its step has `outcome: "blocked_disabled"`, native
`target.enabled: false`, and zero callback delta. Any unexpected callback fails.
An enabled target is still actually tapped. The adapter never writes selection or
enabled state; those are caller fixture/production component responsibilities.

```sh
python3 native-ui-agent/scripts/ios_observe.py run \
  --bridge /absolute/Bridge.swift \
  --package /absolute/production-package --product AlertToast \
  --fixtures /absolute/fixtures.json --actions /absolute/actions.json \
  --simulator SIMULATOR_UDID --output /absolute/fresh-evidence
```

Omit `--package` for a self-contained bridge/probe. For an app outside a Swift package,
use the project's existing test host instead, or expose its production component as a
local package; this adapter does not copy app source into a substitute implementation.
The current build command targets an Apple Silicon simulator (`ARCHS=arm64`,
`ONLY_ACTIVE_ARCH=YES`), including the real imported package. Intel simulator builds
are outside this tested adapter configuration. Xcode is selected only per
child-process `DEVELOPER_DIR`; no global settings change.
`--developer-dir` and explicit `--sdk iphonesimulator` are supported.

## Evidence and limits

Each run requires a fresh directory. `manifest.json` records build/test commands and
exit codes, actual native test count from xcresult, SHA-256 source and image hashes,
coverage, native summary and final observer status. `observation.json` contains native
AX snapshots, actual screen-point frames, screenshot pixel dimensions, mapped image
frames, host process PID/instance identity, fixture index, callback deltas, screenshots,
and issues. Original xcresult bundles, logs and exported XCTest attachments are retained.
Fixture transport is base64 JSON injected into test-runner environment in `.xctestrun`,
then into app launchEnvironment. No generated test silently substitutes a missing fixture.

AX role, identifier, label, value, enabled, selected and hittable are read from
XCUIElement. Value is a string representation of XCUI's returned value or null.
`intersects_viewport` means a nonempty native frame intersects the measured ScrollView;
it is geometric evidence, not proof of lack of occlusion. The viewport is measured by
a native GeometryReader in global points; the raw AX ScrollView frame is retained
separately because SwiftUI can extend it into safe areas. The complete node list also
contains offscreen nodes. `coverage.observed_identifiers` requires a complete native
frame inside the viewport and native hittability (or an actually disabled target).
The bottom sentinel must be fully contained and hittable.
`fully_within_viewport` records that geometric check, with 0.5-point tolerance.
A tap or a `scroll` target also requires complete containment. A target taller than the
viewport therefore remains incomplete and requires a caller-specific inspection.
Before/after snapshots permit
independent checks of text changes and the same process identity for fixture updates.

The adapter does **not** extract generic SwiftUI font, padding, foreground/background
color, or style-tree attributes. A 48-point frame proves that measured AX boundary,
not its font or internal padding. Native geometry and screen density may support image
crops; they do not establish design correctness. Observer status `passed` means this
observation session completed with coverage, not that business/visual requirements pass.

`ProbeBridge.swift` is a separate generic capability preflight with native text, a
48-point button, tall content and a last action. It is never used as a production UI
substitute. Forward-test it with actual native builds, taps, callback receipt, scroll
coverage and explicit caller update before relying on new adapter capabilities.
