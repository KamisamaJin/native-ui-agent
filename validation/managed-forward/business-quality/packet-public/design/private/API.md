# Fixed production API

Only the two production component files named in README may be added. Their public types are below. They must not import an observer/test package. All DTO fields are required and non-null. Money is integer USD cents. IDs match `[a-zA-Z0-9_-]+`, revision is positive, servings and option bounds are positive, minimum is at most maximum, prices/prepaid/credit are nonnegative, option IDs are unique. The initial requested count is positive; later choices clamp it. Option order and note order are caller order. Fixtures are valid; no malformed-input UI is requested.

Swift types, exported by `AlertToast`:

```swift
public struct MenuReplacementOption: Codable, Equatable {
    public let id: String
    public let title: String
    public let detail: String
    public let pricePerServingCents: Int
    public let minimumServings: Int
    public let maximumServings: Int
    public let available: Bool
    public init(id: String, title: String, detail: String,
                pricePerServingCents: Int, minimumServings: Int,
                maximumServings: Int, available: Bool)
}
public struct MenuChangeModel: Codable, Equatable {
    public let requestID: String
    public let revision: Int
    public let orderReference: String
    public let venue: String
    public let occasion: String
    public let originalDish: String
    public let respondBy: String
    public let requestedServings: Int
    public let prepaidTotalCents: Int
    public let trayReturnCreditCents: Int
    public let notice: String
    public let options: [MenuReplacementOption]
    public let kitchenNotes: [String]
    public init(requestID: String, revision: Int, orderReference: String,
                venue: String, occasion: String, originalDish: String,
                respondBy: String, requestedServings: Int,
                prepaidTotalCents: Int, trayReturnCreditCents: Int,
                notice: String, options: [MenuReplacementOption],
                kitchenNotes: [String])
}
public struct MenuChangeSubmission: Equatable {
    public let requestID: String
    public let revision: Int
    public let optionID: String
    public let servings: Int
    public let useTrayCredit: Bool
    public let balanceCents: Int
    public var wireValue: String { get }
}
public struct MenuChangeReviewPanel: View {
    public init(model: MenuChangeModel,
                onSubmit: @escaping (MenuChangeSubmission) -> Void)
}
```

Each Swift DTO initializer has the exact fields shown; its implementation assigns them. `MenuChangeSubmission` may have a public memberwise initializer with those six fields. Use only iOS-14-compatible production APIs. These signatures describe interfaces, not implementation code to copy wholesale.

Kotlin public types in `com.example.reply.ui.components`:

```kotlin
data class MenuReplacementOption(
    val id: String, val title: String, val detail: String,
    val pricePerServingCents: Int, val minimumServings: Int,
    val maximumServings: Int, val available: Boolean
)
data class MenuChangeModel(
    val requestID: String, val revision: Int, val orderReference: String,
    val venue: String, val occasion: String, val originalDish: String,
    val respondBy: String, val requestedServings: Int,
    val prepaidTotalCents: Int, val trayReturnCreditCents: Int,
    val notice: String, val options: List<MenuReplacementOption>,
    val kitchenNotes: List<String>
)
data class MenuChangeSubmission(
    val requestID: String, val revision: Int, val optionID: String,
    val servings: Int, val useTrayCredit: Boolean, val balanceCents: Int
) { val wireValue: String get() = /* exact format below */ }
@Composable
fun MenuChangeReviewPanel(
    model: MenuChangeModel,
    onSubmit: (MenuChangeSubmission) -> Unit
)
```

The only product event is a valid send. `wireValue` is exactly:

```text
menu.submit|request=<requestID>|revision=<revision>|option=<optionID>|servings=<servings>|trayCredit=<true-or-false>|balanceCents=<signed-integer>
```

Example: `menu.submit|request=cedar-104|revision=1|option=roast|servings=13|trayCredit=true|balanceCents=1400`. The component constructs this typed submission. The thin bridges call `onEvent(submission.wireValue)`; they do not calculate money, manage local selection or reconcile revisions.

Native accessibility identifiers / Compose test tags belong on actual production targets:

| Identifier | Meaning / native semantics |
|---|---|
| `menu.canvas` | Component container, contains children without merging them into one leaf. |
| `menu.title`, `menu.context`, `menu.original`, `menu.notice` | Occasion; `Order <orderReference> · <venue> · revision <revision>`; `Replacing: <originalDish> · <requestedServings> servings`; notice. |
| `menu.option.<id>` | One native button per option, accessible label exactly option title, selected trait/state reflects current selection; unavailable and sent are disabled. Price, range and unavailable explanation remain visibly readable and can be in its hint. |
| `menu.servings` | Text `<desired servings> servings`. |
| `menu.decrease`, `menu.increase` | Native buttons labeled `Decrease servings` and `Increase servings`; visible minus / plus is acceptable with these accessible labels. |
| `menu.credit` | Actual native switch labeled `Use tray return credit`; exposes native on/off value. Visible supporting copy includes the currently offered credit amount. |
| `menu.ack` | Actual native switch with the full acceptance sentence in README; exposes native on/off value. |
| `menu.summary` | Solid balance-card container, contains child text without replacing/merging it. |
| `menu.selection` | Selected title, otherwise `No replacement selected`. |
| `menu.replacementTotal` | `Replacement total $N.NN`, otherwise `Replacement total —`. |
| `menu.prepaid` | `Already paid $N.NN`. |
| `menu.creditApplied` | `Tray credit applied $N.NN`; zero when credit not on, even with no choice. |
| `menu.balance` | Signed balance display from README, otherwise `Select a dish to calculate the balance`. |
| `menu.status` | Current status sentence. |
| `menu.submit` | Native button `Send replacement request`, or `Request sent` after sending. |
| `menu.notes.last` | The complete final kitchen-note paragraph. Other paragraphs need no test-only IDs. |

Do not put a second clickable descendant inside an option button or a switch semantic target. Support real native accessibility behavior; these IDs are limited to this component and do not require application-wide instrumentation. No testing-only style readback or hidden copy of rendered UI is allowed.

The supplied `Bridge.swift` signature is `ObserverBridge.make(fixture:onEvent:) -> AnyView`. The supplied Android bridge is `org.nativeobserver.ObserverBridge.Content(JsonObject, (String) -> Unit)`. They decode one immutable DTO from the current fixture and directly instantiate the production API. Their source bytes are fixed and launch-bound for both scopes. Fixture updates pass a new model through the same call site and keep component identity.
