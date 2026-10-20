# ExpeditionPackPanel public API

Implement Swift in `alerttoast/Sources/AlertToast/ExpeditionPackPanel.swift` and Compose in `reply/Reply/app/src/main/java/com/example/reply/ui/components/ExpeditionPackPanel.kt`.

```swift
public struct ExpeditionPackItem: Codable {
    public let id: String
    public let name: String
    public let grams: Int
    public let available: Bool
    public let providesShelter: Bool
    public let note: String
    public init(id: String, name: String, grams: Int, available: Bool, providesShelter: Bool, note: String) {
        self.id = id
        self.name = name
        self.grams = grams
        self.available = available
        self.providesShelter = providesShelter
        self.note = note
    }
}

public struct ExpeditionPackRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let choiceWidth: Double
    public let notes: [String]
    public let baseGrams: Int
    public let maxGrams: Int
    public let requiresShelter: Bool
    public let coverGrams: Int
    public let selectedIDs: [String]
    public let cover: Bool
    public let items: [ExpeditionPackItem]
    public init(id: String, title: String, context: String, choiceWidth: Double, notes: [String], baseGrams: Int, maxGrams: Int, requiresShelter: Bool, coverGrams: Int, selectedIDs: [String], cover: Bool, items: [ExpeditionPackItem]) {
        self.id = id
        self.title = title
        self.context = context
        self.choiceWidth = choiceWidth
        self.notes = notes
        self.baseGrams = baseGrams
        self.maxGrams = maxGrams
        self.requiresShelter = requiresShelter
        self.coverGrams = coverGrams
        self.selectedIDs = selectedIDs
        self.cover = cover
        self.items = items
    }
}

public struct ExpeditionPackPanel: View {
    public init(request: ExpeditionPackRequest, onConfirm: @escaping (String, [String], Bool) -> Void)
    public var body: some View { get }
}
```

Kotlin uses `package com.example.reply.ui.components` and public data classes with identical field names. Swift `Int`→Kotlin `Int`, `Double`→`Double`, `Bool`→`Boolean`, `[String]`→`List<String>`, item arrays→`List<Item>`. Define every model constructor argument in the exact order shown above, with no required extra parameters.

```kotlin
@Composable
fun ExpeditionPackPanel(request: ExpeditionPackRequest, onConfirm: (String, List<String>, Boolean) -> Unit)
```

`onConfirm` receives the current request id, selected item ids sorted lexicographically, and the current optional choice. Call only when enabled. Other controls update local UI state without caller callbacks. Request id replacement resets local selection, optional choice and disclosure on the existing mounted component. Never emit a confirm callback during caller replacement. Models are business inputs only; do not add observation state, expected labels, grading flags or evidence props.
