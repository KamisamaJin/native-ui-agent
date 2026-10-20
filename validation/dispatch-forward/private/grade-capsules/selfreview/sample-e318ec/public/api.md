# Public native API and local selector contract

The feature name is WaterRound. Swift source belongs to the existing AlertToast public library; Android source belongs to com.example.reply.ui.waterround in Reply. These are public production types, not bridge-only mirror types.

## Shared model

Swift: public struct WaterRoundModel with public immutable stored properties and one public initializer taking every member below without default values. Kotlin: public data class WaterRoundModel with val properties and the same required constructor members. Swift Int and Kotlin Int are sufficient for the constrained domain. All JSON members are required; the bridge must not replace absent or invalid members with defaults.

| Member | Shared type | Valid domain |
| --- | --- | --- |
| roundId | String | nonempty ASCII letters, digits, underscore, or hyphen only |
| title | String | nonempty arbitrary Unicode |
| description | String | nonempty arbitrary Unicode |
| notice | String | arbitrary Unicode; empty means absent |
| bedCount | Int | 1…200 |
| dripLitresPerBed | Int | 1…500 |
| soakLitresPerBed | Int | 1…500 |
| dripPrimeLitres | Int | 0…2000 |
| tankLitres | Int | 0…200000 |
| reserveLitres | Int | 0…tankLitres |
| soakAllowed | Bool / Boolean | required |
| selectedMethod | WateringMethod | drip or soak; must be drip if soakAllowed is false |
| reserveAcknowledged | Bool / Boolean | required; ignored when consent is absent |
| isEnabled | Bool / Boolean | required |
| isSubmitting | Bool / Boolean | required |

WateringMethod is a public String-backed Swift enum and public Kotlin enum with exactly the values drip and soak. JSON enum values use these same lower-case strings. The semantic public model, method values, action alternatives, and payload members are identical across languages.

## Typed actions

Swift public enum WaterRoundAction uses the following associated-value cases. Kotlin public sealed interface WaterRoundAction uses public nested data classes with these same lower-case alternative names and the same members (lower-case class names are intentional here). All payloads are immutable and integer payloads use Int.

~~~swift
case methodRequested(roundId: String, method: WateringMethod)
case reserveAcknowledgementRequested(roundId: String, acknowledged: Bool)
case releaseRequested(
    roundId: String,
    method: WateringMethod,
    bedCount: Int,
    requestedLitres: Int,
    remainingLitres: Int,
    reserveUsedLitres: Int
)
~~~

Kotlin substitutes Boolean for Bool. No other action alternative or hidden UI-originated event is part of this API. reserveUsedLitres is reserveNeededLitres at the instant of an eligible release; requestedLitres is requiredLitres. The other payloads use exactly the current supplied model and current derived summary. On submitting, a request is never emitted merely because the replacement model says submitting.

Swift production entry:
~~~swift
public struct WaterRoundReleaseView: View
public init(model: WaterRoundModel, onAction: @escaping (WaterRoundAction) -> Void)
~~~

Kotlin production entry:
~~~kotlin
@Composable
fun WaterRoundRelease(
    model: WaterRoundModel,
    onAction: (WaterRoundAction) -> Unit,
    modifier: Modifier = Modifier
)
~~~

Swift's modifier remains the normal SwiftUI view modifier chain; Android must honor the optional supplied Modifier. New public Swift API must compile for iOS 14 and macOS 11. Guard later-platform APIs if used internally. Do not place this production view, its model, or its action type in a test host.

## Deterministic callback serialization

The bridge serializes actual typed actions as these exact ordered single-line strings, without whitespace additions or a trailing newline. Preserve event order in an array. Boolean tokens are lower-case true/false. Int tokens are ungrouped base-ten ASCII. roundId's domain makes escaping unnecessary. Never serialize a UI label or synthetic dictionary in place of a typed callback.

~~~text
methodRequested|roundId=ID|method=drip
reserveAcknowledgementRequested|roundId=ID|acknowledged=true
releaseRequested|roundId=ID|method=drip|bedCount=N|requestedLitres=N|remainingLitres=N|reserveUsedLitres=N
~~~

## Exact local selector vocabulary

These identifiers belong only to this component. iOS exposes them as accessibilityIdentifier; Android exposes them as Compose testTag. Do not add whole-application identifiers. A conditional target is absent when its content is absent. The root bounds cover the component's actual owned surface.

| Identifier | Meaning / native text or state |
| --- | --- |
| waterRound.root | owned card surface |
| waterRound.title | supplied title |
| waterRound.description | supplied description |
| waterRound.notice | supplied notice, only when nonempty |
| waterRound.beds | "Beds: N" |
| waterRound.tank | "Tank: N L" |
| waterRound.reserve | "Protected reserve: N L" |
| waterRound.dripPrime | "Drip prime: N L" |
| waterRound.method.drip | native button; accessible label "Drip lines, N L per bed"; selected and enabled state |
| waterRound.method.soak | native button; accessible label "Soak hoses, N L per bed"; selected and enabled state |
| waterRound.required | "Required: N L" |
| waterRound.spendable | "Outside reserve: N L" |
| waterRound.reserveNeeded | "Reserve needed: N L" |
| waterRound.remaining | "Remaining: N L" |
| waterRound.shortfall | "Shortfall: N L", only if positive |
| waterRound.reserveConsent | native checkable control; label "Use N L from the protected reserve"; checked and enabled state; only when consent is required |
| waterRound.status | exact status text defined in brief.md |
| waterRound.submit | native button; label "Release N L"; enabled state |
| waterRound.progress | native progress indicator, only when isEnabled && isSubmitting |

Numeric summary entries may expose the complete combined text via native label/text, even when visually laid out in separate spans. The action buttons must remain native actionable controls. Avoid turning the whole card into one combined accessibility element that hides the local selectors.

Use XCTest/XCUI tap for iOS and the Compose semantic OnClick action for Android. Android semantic activation is not a physical OS touch claim. Native checked/selected/enabled observations may use platform representations normalized to those Boolean concepts, with the original native fields retained. Repeated clicks on the visible consent request the same inverse Boolean until the caller sends a replacement. Repeated release requests use the same supplied model until replacement. A selected method button is enabled in an enabled round, but its successful tap is a no-op.

## Public example

public-example.json is an illustrative caller input, not a private validation case. Its environment is only a host instruction; production APIs receive the model. No expected event trace is published.
