# Neutral native capability fixture interface

This addendum was prepared after the qualification protocol seal, without reading
candidate implementation code or previous validation material. Its source is
unbuilt. Nothing in this directory is evidence of SDK availability or successful
native behavior. Preserve the original protocol seal; bind this addendum using
`FIXTURE-SEAL.json` before either benchmark arm runs.

`ObserverBridge.swift` supplies the documented self-contained iOS bridge ABI and
imports only Foundation/SwiftUI. The documented observer can build a thin native
App/XCUITest host without a production package. `ObserverBridge.kt` supplies the
documented Android `org.nativeobserver.ObserverBridge.Content(JsonObject,
onEvent)` ABI. It needs an admitted existing Paparazzi/Compose test module with
Material3 and kotlinx.serialization. No historical project, product code or
previous qualification scaffold has been copied.

An independent operator still must supply the Android module/Gradle wrapper and
confirmed dependency/toolchain versions, the installed iOS runtime/device type,
approved environment/design/launch/coverage/route locks, and default-service
project configs. The ABI alone cannot choose those project-specific facts.
This is therefore a source fixture plus minimum integration interface, not a
claimed runnable two-platform SDK package. No SDK/build/device command has run.

Both bridges display a fixture marker, a callback-updated counter, eighteen tall
rows, a last action and a detail. They expose a stable-per-mounted-view instance
token through native accessibility/semantics while rendering constant visible
text `Instance`. A caller update changes marker/detail without intentionally
replacing view identity. The actual native instance token, not the source code,
must establish whether identity was preserved. A new capture must have a fresh
native app/session identity; the token is additional evidence and cannot replace
the adapter's process/input/event bindings.

No bridge supplies scrolling: the documented observer parent owns the viewport
and scroll sampling. Actual button leaf/semantic grouping, AX frame, touch bounds,
font, text layout, Dynamic Type and screenshot coverage require real observation.
The declared 48-unit outer button height is not proof of a native control's
physical hit region or effective font. The two platforms need not have identical
pixel layouts or typography. Native constraints/tolerances must be independently
fixed before collecting, without learning values from the first screenshots.

## Frozen scalar inputs

The JSON files contain only deterministic markers/details and observer environment
requests. iOS `ios-cold.json` and `ios-warm.json` are the two approved payloads for
the C0 and W1/F2 epochs. Android always uses `android.json` in the unchanged-source
speed episode. Each contains an initial value and one replacement. The value
suffix changes after caller replacement. iOS's required identifier list includes
lower content. Both platforms' independent coverage oracle includes the lower
content so a top image cannot satisfy coverage. Apply AMENDMENT-1's distinction
between ordinary eligible-packet finalization and explicit fresh collection.

`actions.json` is a documented observer-action sequence for the ordinary capability
path. It supplies explicit independent branches and callback predicates; the
operator must bind this exact route into the independently approved design plan
and let the default compiler generate execution scope. Do not pass an unrelated
parallel action file in place of that source of truth. State indices are zero
based. There are no disabled-target actions in the speed route. Use
`negative-actions.json` only for the separate blocked-dispatch qualification.

The public default execution API should materialize this route, with all normal
source/responsibility/environment gates. This addendum does not replace it with a
test-only collector. If a public configuration cannot represent the route or
dependencies, record that incompatibility; do not quietly change the route.

## Minimum independent oracle

The operator binds each row below to the actual generated assertion and source
expectation before A/B. State IDs and after-action indices come from the sealed
actions. Preserve state-local full-content maps and native command/result files.

| State / action | Mandatory fact and independent expectation |
| --- | --- |
| `start` / 0 | input 0; exact initial marker/detail; unique enabled primary; full overlapping content reaches the native bottom sentinel and includes the lower detail/last target; actual requested environment verified |
| `after-primary` / 1 | real unique enabled primary native activation using the platform's actual documented route; exact callback delta `["probe.primary"]`; immediate result retained; counter `Tap count: 1`; no second activation from locating evidence |
| `after-replacement` / 2 | actual input index advances 0 to 1 in the same capture process/app session; original instance token remains; marker/detail now equal the exact update payload; counter stays `Tap count: 1`; caller-update callback interval is empty after successful real caller update |
| `replacement-full` / 3 | full overlapping content coverage for input 1 in that same capture; exact updated marker/detail and lower native last target observed; input 0 bottom frames cannot fill this state |
| `after-last` / 4 | lower native last target is actually located and uniquely activated; exact callback delta `["probe.last"]`; immediate and post-location evidence retain input 1/process/event identity; partial target visibility cannot certify full content |

The ordinary capability route is intended to produce P for observable facts,
without inventing unsupported style claims. This expectation is conditional on
actual native capability qualification; any unmet fact remains U or a demonstrated
F according to raw evidence. Do not set P because the bridge source looks correct.

The independent negative protocol controls are outside speed measurement:

* Use `negative-actions.json` to observe the native disabled primary counterpart.
  `probe.disabled.enabled == false` can be P. A callback-behavior assertion with
  an unexecuted disabled activation is U even for expected empty callbacks.
  Unexpected real callback receipt is separately F. An independent subsequent
  primary branch still must establish its own real activation and callback.
* Re-evaluate an intact start-state packet against a separately sealed deliberate
  wrong marker expectation. A demonstrated actual different label is F. Keep
  this evaluator-control plan separate from the ordinary delivery plan; it is
  neither a business defect nor a reason to repair correct source.
* Handoff repair requires its own authentic mismatching native harness variant,
  independently frozen before collecting. Give its worker only the emitted task
  and cited evidence. Neither an expectation mismatch control nor a fabricated
  process/dispatch receipt can stand in for a repairable source defect.

Do not add unsupported SwiftUI computed styles, physical Android touch, physical
iOS hit-size claims, a complete app lifecycle or undeclared business requirements
to this interface. Do not shrink rows or change widths/fonts to accelerate it.
