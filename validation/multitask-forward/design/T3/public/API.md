# CafeGroupOrderPanel public API

Implement Swift in `alerttoast/Sources/AlertToast/CafeGroupOrderPanel.swift` and Compose in `reply/Reply/app/src/main/java/com/example/reply/ui/components/CafeGroupOrderPanel.kt`.

```swift
public struct CafeGroupDrink: Codable {
    public let id: String
    public let name: String
    public let cents: Int
    public let available: Bool
    public let supportsReuse: Bool
    public let note: String
    public init(id: String, name: String, cents: Int, available: Bool, supportsReuse: Bool, note: String) {
        self.id = id
        self.name = name
        self.cents = cents
        self.available = available
        self.supportsReuse = supportsReuse
        self.note = note
    }
}

public struct CafeGroupOrderRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let choiceWidth: Double
    public let notes: [String]
    public let maxServings: Int
    public let member: Bool
    public let discountThreshold: Int
    public let discountCents: Int
    public let reuseCreditCents: Int
    public let reuseAllowed: Bool
    public let selectedIDs: [String]
    public let reuse: Bool
    public let drinks: [CafeGroupDrink]
    public init(id: String, title: String, context: String, choiceWidth: Double, notes: [String], maxServings: Int, member: Bool, discountThreshold: Int, discountCents: Int, reuseCreditCents: Int, reuseAllowed: Bool, selectedIDs: [String], reuse: Bool, drinks: [CafeGroupDrink]) {
        self.id = id
        self.title = title
        self.context = context
        self.choiceWidth = choiceWidth
        self.notes = notes
        self.maxServings = maxServings
        self.member = member
        self.discountThreshold = discountThreshold
        self.discountCents = discountCents
        self.reuseCreditCents = reuseCreditCents
        self.reuseAllowed = reuseAllowed
        self.selectedIDs = selectedIDs
        self.reuse = reuse
        self.drinks = drinks
    }
}

public struct CafeGroupOrderPanel: View {
    public init(request: CafeGroupOrderRequest, onConfirm: @escaping (String, [String], Bool) -> Void)
    public var body: some View { get }
}
```

Kotlin uses `package com.example.reply.ui.components` and public data classes with identical field names. Swift `Int`→Kotlin `Int`, `Double`→`Double`, `Bool`→`Boolean`, `[String]`→`List<String>`, item arrays→`List<Item>`. Define every model constructor argument in the exact order shown above, with no required extra parameters.

```kotlin
@Composable
fun CafeGroupOrderPanel(request: CafeGroupOrderRequest, onConfirm: (String, List<String>, Boolean) -> Unit)
```

`onConfirm` receives the current request id, selected item ids sorted lexicographically, and the current optional choice. Call only when enabled. Other controls update local UI state without caller callbacks. Request id replacement resets local selection, optional choice and disclosure on the existing mounted component. Never emit a confirm callback during caller replacement. Models are business inputs only; do not add observation state, expected labels, grading flags or evidence props.
