# Native control and per-state observation tools

Use these when a component needs native interaction, long-content location or visual
checks across caller updates. The adapters invoke the caller's production bridge;
they supply no business UI or expected answer. Run generic capability probes first.

## Capture

The iOS App/XCUITest entry point remains `scripts/ios_observe.py run` (see the
[full bridge contract](../assets/ios-observer/CONTRACT.md)). `state_capture` defaults
to true. Its caller JSON has `initial`, optional `updates`, width320/390, theme,
Dynamic Type category, direction, and optional `observation_targets` selectors.

The Android entry point requires an existing Paparazzi test project, its JVM/SDK
configuration and a caller bridge in package `org.nativeobserver`:

```kotlin
object ObserverBridge {
  @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
    // Decode input, apply the project's real theme, call the production component.
    // Echo controlled actions in the caller bridge and notify onEvent.
  }
}
```

```sh
python3 scripts/android_observe.py run --project /absolute/project \
  --bridge /absolute/ObserverBridge.kt --fixtures /absolute/fixtures.json \
  --actions /absolute/actions.json --output /absolute/fresh-output \
  --java-home /absolute/jdk --android-sdk /absolute/sdk
```

The Android config uses width, theme, fontScale, direction, initial and updates.
The adapter adds a newly created reserved test folder, removes only its own files
in `finally`, and retains exact sources, inputs, JUnit, images and hashes in output.
It does not install Gradle plugins or claim Activity/physical-touch coverage.

Both action formats support:

```json
[
  {"type":"tap","target":{"identifier":"actual.choice"},"reveal":true,
   "allow_disabled":true,"state_id":"selected"},
  {"type":"apply_next_fixture","state_id":"replaced"},
  {"type":"tap","target":{"label":"Exact visible action","role":"button"},
   "reveal":true,"state_id":"after-action"},
  {"type":"sweep","state_id":"expanded"}
]
```

After a tap, the observer keeps the immediate result and, by default, reveals the
same target again if layout moved it outside the viewport. `after_target` can name
another exact selector; `observe_after:false` explicitly disables that extra
observation. No second activation occurs. Post-observation stores target geometry,
snapshot and input/event binding; offscreen/missing/ambiguous targets or binding
drift never become a visual pass. A fitting target is fully revealed; an oversized
target's center is measured separately from full visibility.

For multiple locations use `after_targets:[selector,...]` on a tap, caller update
or checkpoint. Native observers reuse already valid frames and collect remaining
targets without another activation. `observation_max_scrolls` (0–40, default24)
bounds the entire target set, not each target. Missing/ambiguous targets retain
their individual unavailable result; a zero search budget still permits actual
immediate-frame facts. `observation_set` binds original snapshot indices, input,
process and event revision, plus native target results and geometry traces.
Callback receipts and event_end remain those of the immediate action frame.
Read [state evidence planning](state-evidence.md) for matrix compilation and
machine findings; `coverage:"targets"` evaluates all bound frames while retaining
`complete:false`. It also gives legacy single-frame evidence its actual credit.

iOS exports hierarchy/attributes from one public XCUIElementSnapshot per capture.
Native hit testing is queried at actual dispatch targets; other exported nodes
have `hittable_measured:false`, not guessed hit values. A native epoch/geometry
change across hierarchy and image makes that capture unassessed. Reveal navigation
keeps native geometry traces; `trace_reveal_images:true` also keeps every search
image. Full-content sweeps still retain all required overlapping images.

For repeated fixtures on unchanged source, iOS `run --build-cache /absolute/cache`
can reuse a content-addressed compiled host. The key covers source/bridge/templates,
toolchain, SDK and compile options; artifact hashes are checked before reuse. Each
capture gets a fresh runtime test plan, inputs, App process, callbacks and images.
Changed code/toolchain is a miss; changed/tampered artifacts fail closed. The manifest
separates cache validation/build, native test and export time. Android retains one
attached ComposeView and stops only when its native capture state machine completes;
it does not shorten content or omit planned states to meet the frame budget.

Selectors are exact identifier or exact label with an optional native role. Natural
language target selection remains the caller agent's job. Duplicate semantic
matches or multiple native actionable descendants are unavailable, never first-match
clicks. iOS uses actual descendant queries; Android uses actual semantic parent IDs.
The semantic container retains coherent label/selected traits, while enabled state
and activation use the unique actual Button/Switch/OnClick. Independently activatable
parents and children remain separate candidates; a narrower selector is required.
Only native Switch wrapper/leaf duplication is collapsed. A container's `enabled=true`
or an ordinary Button's `selected=false` alone is not a component defect.

Long-content location uses current native frames and bounded feedback. iOS reduces
scroll size on direction reversals and records missing/stationary/limit outcomes.
Normal-sized iOS controls are revealed completely. A scroll-to-text target does not
require a control role. An oversized native control may be activated at its measured visible intersection;
that is recorded separately from full-element visibility, with real callback delta.
Android invokes the native semantic action and moves native ScrollState; this is
not OS physical touch. Missing callbacks after an unexecuted action stay unassessed.

## State coverage

Capture automatically sweeps initial, before caller replacement, and final. Give
relevant post-action checkpoints unique `state_id` values to sweep those states too.
`initial`/`final` are reserved. Explicit sweep `max_steps` can bound one sweep; the
result remains incomplete if that bound cannot cover the content.

Each `state_captures` item binds input index/hash, process/session identity, event
revision, action checkpoint and exact snapshot indices. Native content geometry
and viewport intervals establish top-to-bottom overlap for THAT state. A later
fixture's footer cannot fill an earlier fixture's gap. No global observed-ID union
is substituted for per-state coverage. Dynamic content/height/binding problems stay
visible. Complete pixel coverage is not style correctness.

XCUI sometimes returns non-finite geometry. JSON transport retains those coordinates
as null and lists their native values/paths in `serialization_diagnostics`; their
pixel projection is unavailable. It never substitutes zero coordinates or drops all
other native observations because one frame cannot be represented in JSON.

## Typed assertions

`native_checks.py` consumes a frozen atomic plan and actual observation. Keep a
requirement's independently unmeasured aspects separate. The independent required-ID
set can detect omitted plan cells; code cannot prove that natural-language intent
has been completely translated into the plan.

```json
{
 "version":1,
 "states":[{"id":"selected","input_index":0,"after_action":0}],
 "required_assertion_ids":["choice-enabled","selected-state"],
 "assertions":[
  {"id":"choice-enabled","state":"selected","kind":"control",
   "target":{"identifier":"actual.choice"},"property":"enabled","expected":true},
  {"id":"selected-state","state":"selected","kind":"control",
   "target":{"identifier":"actual.choice"},"property":"selected","expected":true}
 ]
}
```

```sh
python3 scripts/native_checks.py --plan /absolute/plan.json \
  --observation /absolute/capture/observation.json --platform ios \
  --output /absolute/fresh-checks.json
```

For an action-only checkpoint, a state can set `coverage:"target"` and
`after_action:N`. The checker verifies the exact native post-action snapshot and
binding, without a full sweep. Its `complete:false` explicitly means no full-content
claim. It can establish callback/native-control assertions, while a full-content
visual pass remains withheld. Use this to avoid expensive unnecessary whole-body
sweeps after every simple interaction.

Control properties include present, unique, enabled, selected, value, label,
control_role, ax_width/ax_height. `touch_width/touch_height` use Android native touch
bounds only; iOS AX frames do not establish physical hit regions. `event` assertions
name the action index and exact expected callback delta. They default to activation
and the platform's real route (`xcui_tap` or `compose_onclick`). Optional
`required_method` must match the demonstrated method. The exported
`native_checks.callback_verdict` is also the evaluator entry point: successful
attempt, unique enabled native control, same input/process and exact event interval
are hard preconditions. Observer-blocked/unavailable/observed intervals remain U
even when expected callbacks are empty. A demonstrated delivery with missing/wrong
callbacks is F. For callback quietness after caller replacement, explicitly set
`stimulus:"caller_update"`; the native input index must demonstrably advance by one.
Literal interval facts are retained separately and are not behavior verdicts.
`text_layout` uses exported
native text-layout fields such as font_sp, color_argb, lines, ellipsized or overflow;
unsupported fields remain unassessed, not guessed from source.

A `manual` visual/pixel assertion requires a review with `observation_sha256` and
`decisions` entries containing id, method, status, reason, snapshot_indices and
SHA-bound evidence including the actual state screenshots. A visual pass requiring
`coverage:full_content` is withheld if interval coverage is incomplete. A visible
failure may be established from a smaller observed region. Manual judgment remains
fallible; typed runtime facts cannot be replaced with manual/source assertions.

Exit0 means supplied atomic assertions passed,1 confirmed assertion failures,
3 unassessed assertions,2 invalid inputs/evidence. This is not proof of every business
requirement absent an independently checked complete contract. Always retain the
assertion denominator and unassessed counts.
