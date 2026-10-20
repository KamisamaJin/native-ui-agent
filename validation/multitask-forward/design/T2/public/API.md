# PublicationRightsPanel public API

Implement Swift in `alerttoast/Sources/AlertToast/PublicationRightsPanel.swift` and Compose in `reply/Reply/app/src/main/java/com/example/reply/ui/components/PublicationRightsPanel.kt`.

```swift
public struct PublicationRightsChannel: Codable {
    public let id: String
    public let name: String
    public let cents: Int
    public let available: Bool
    public let note: String
    public init(id: String, name: String, cents: Int, available: Bool, note: String) {
        self.id = id
        self.name = name
        self.cents = cents
        self.available = available
        self.note = note
    }
}

public struct PublicationRightsRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let choiceWidth: Double
    public let notes: [String]
    public let baseCents: Int
    public let exclusiveCents: Int
    public let exclusiveAllowed: Bool
    public let selectedIDs: [String]
    public let exclusive: Bool
    public let channels: [PublicationRightsChannel]
    public init(id: String, title: String, context: String, choiceWidth: Double, notes: [String], baseCents: Int, exclusiveCents: Int, exclusiveAllowed: Bool, selectedIDs: [String], exclusive: Bool, channels: [PublicationRightsChannel]) {
        self.id = id
        self.title = title
        self.context = context
        self.choiceWidth = choiceWidth
        self.notes = notes
        self.baseCents = baseCents
        self.exclusiveCents = exclusiveCents
        self.exclusiveAllowed = exclusiveAllowed
        self.selectedIDs = selectedIDs
        self.exclusive = exclusive
        self.channels = channels
    }
}

public struct PublicationRightsPanel: View {
    public init(request: PublicationRightsRequest, onConfirm: @escaping (String, [String], Bool) -> Void)
    public var body: some View { get }
}
```

Kotlin uses `package com.example.reply.ui.components` and public data classes with identical field names. Swift `Int`→Kotlin `Int`, `Double`→`Double`, `Bool`→`Boolean`, `[String]`→`List<String>`, item arrays→`List<Item>`. Define every model constructor argument in the exact order shown above, with no required extra parameters.

```kotlin
@Composable
fun PublicationRightsPanel(request: PublicationRightsRequest, onConfirm: (String, List<String>, Boolean) -> Unit)
```

`onConfirm` receives the current request id, selected item ids sorted lexicographically, and the current optional choice. Call only when enabled. Other controls update local UI state without caller callbacks. Request id replacement resets local selection, optional choice and disclosure on the existing mounted component. Never emit a confirm callback during caller replacement. Models are business inputs only; do not add observation state, expected labels, grading flags or evidence props.
