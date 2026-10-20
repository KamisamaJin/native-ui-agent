# Fixed native API and observer contract

Exact production files, relative to the pinned repositories:

- Reply: `app/src/main/java/com/example/reply/ui/printbatch/PrintBatchApprovalCard.kt`; Kotlin package `com.example.reply.ui.printbatch`.
- AlertToast: `Sources/AlertToast/PrintBatchApprovalCard.swift`; Swift module `AlertToast`.

These files are the production implementations. Bridges call these components directly. Do not duplicate a product implementation inside a bridge.

## Kotlin public declarations

```kotlin
data class PrintBatchJob(val id: String, val title: String, val pages: Int, val copies: Int, val isColor: Boolean, val selected: Boolean, val locked: Boolean)
data class PrintBatchModel(val modelID: String, val budgetCredits: Int, val allowPriority: Boolean, val initialPaperMode: String, val initialPriority: Boolean, val initialExpanded: Boolean, val jobs: List<PrintBatchJob>)
data class PrintBatchPresentation(val isDark: Boolean, val textScale: Double, val isRTL: Boolean)
@Composable
fun PrintBatchApprovalCard(
    model: PrintBatchModel,
    presentation: PrintBatchPresentation,
    onEvent: (String, Map<String, Any>) -> Unit,
    modifier: Modifier = Modifier
)
```

## Swift public declarations

All fields and initializers are public. Models may conform to Equatable/Hashable as helpful.

```swift
public struct PrintBatchJob {
    public let id: String; public let title: String
    public let pages: Int; public let copies: Int
    public let isColor: Bool; public let selected: Bool; public let locked: Bool
    public init(id: String, title: String, pages: Int, copies: Int, isColor: Bool, selected: Bool, locked: Bool)
}
public struct PrintBatchModel {
    public let modelID: String; public let budgetCredits: Int
    public let allowPriority: Bool; public let initialPaperMode: String
    public let initialPriority: Bool; public let initialExpanded: Bool
    public let jobs: [PrintBatchJob]
    public init(modelID: String, budgetCredits: Int, allowPriority: Bool, initialPaperMode: String, initialPriority: Bool, initialExpanded: Bool, jobs: [PrintBatchJob])
}
public struct PrintBatchPresentation {
    public let isDark: Bool; public let textScale: Double; public let isRTL: Bool
    public init(isDark: Bool, textScale: Double, isRTL: Bool)
}
public struct PrintBatchApprovalCard: View {
    public init(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: @escaping (String, [String: Any]) -> Void)
    public var body: some View { get }
}
```

`initialPaperMode` accepts only `single` or `duplex`. The callback name and payload are separate parameters. Payload is a JSON-compatible dictionary. The observer adapter serializes it as one JSON object `{"name":name,"payload":payload}`. Integer values remain integers. Job IDs in callbacks are in current model order, with no duplicates.

## Callbacks

- `selectionChanged`: `{"jobIDs":[all currently selected job IDs]}`.
- `paperModeChanged`: `{"paperMode":"single"|"duplex"}`.
- `priorityChanged`: `{"priority":true|false}`.
- `breakdownChanged`: `{"expanded":true|false}`.
- `approve`: `{"modelID":current modelID,"jobIDs":[selected IDs],"paperMode":"single"|"duplex","priority":current persisted boolean,"totalCredits":total,"printedPages":printedPages,"sheets":sheets}`.

Each changing enabled activation produces exactly one event of its corresponding name and payload; approval produces exactly one approve event without changing state. Already-selected mode produces zero events. Disabled activation and caller replacement produce zero component events. Programmatic reset does not emit selection/mode/priority/breakdown events.

## Exact native identifiers

SwiftUI uses accessibilityIdentifier; Compose uses testTag, with those tags exposed as native resource identifiers for the observer. Keep identifiers unique and do not place the same identifier on a parent and child. Every named text value has a separate observable native text node. Identifiers are stable across model replacement. The semantic root may contain children; do not merge all contents into one inaccessible label.

| Identifier | Native meaning / accessibility name |
| --- | --- |
| printbatch.card | Scrollable component root |
| printbatch.title | `Print budget check` |
| printbatch.status | Current badge text |
| printbatch.charge.caption | `Estimated charge` |
| printbatch.charge.value | `{total} cr` |
| printbatch.summary | Exact current summary |
| printbatch.job.ID.toggle | Checkbox/selection action; `Select TITLE` / `Deselect TITLE`, native checked/selected and enabled state |
| printbatch.job.ID.title | Model title |
| printbatch.job.ID.subtitle | Exact subtitle |
| printbatch.job.ID.price | Current per-job price |
| printbatch.mode.title | `Paper mode` |
| printbatch.mode.single | Button `Single-sided`, selected state |
| printbatch.mode.duplex | Button `Duplex`, selected state |
| printbatch.priority | Switch/toggle `Priority handling`, native checked/on and enabled state |
| printbatch.priority.helper | Exact helper text |
| printbatch.breakdown.toggle | Button with exact Show/Hide label and native expanded state or accessibility value `Expanded` / `Collapsed` |
| printbatch.breakdown.ink.label | `Ink` (expanded only) |
| printbatch.breakdown.ink.value | `{ink} cr` (expanded only) |
| printbatch.breakdown.paper.label | `Paper` (expanded only) |
| printbatch.breakdown.paper.value | `{sheets} cr` (expanded only) |
| printbatch.breakdown.priority.label | `Priority` (expanded only) |
| printbatch.breakdown.priority.value | `{surcharge} cr` (expanded only) |
| printbatch.breakdown.total.label | `Total` (expanded only) |
| printbatch.breakdown.total.value | `{total} cr` (expanded only) |
| printbatch.balance | Exact current balance/shortfall text |
| printbatch.approve | Button with exact current approval label and native enabled state |

`ID` is replaced literally by the current job ID. Controls expose one unambiguous exact native activation target. Use native checkbox/switch/button roles and value/selected attributes, or an exact native accessibilityValue `Selected` / `Not selected`, `On` / `Off`, `Expanded` / `Collapsed` where a framework lacks the matching standard attribute. Absence checks require completed bounded content coverage and cannot be inferred from a single viewport.

## Fixture and action wire format

The JSON Schema is input.schema.json. cases.json contains only host configuration, model inputs, initial checkpoint and action inputs. Bridge.swift and ObserverBridge.kt are adapter examples, not implementations. A bridge accepts `{"host":host,"model":activeModel}`; for convenience it also accepts a whole case with `models` and optional `activeModelIndex` (default 0). Caller replacement must preserve the production component's position/identity while supplying the new model, so replacement handling is exercised in production code. The host applies 16 external horizontal units, height 600, and supplies native screenshot/semantic collection; the component owns its scroll container.

The observation normalization contract and the evaluator's capability policy are frozen privately before implementation. No runtime result is inferred from a product source declaration. Public AX does not provide arbitrary SwiftUI font, padding, color or physical hit-region inspection.
