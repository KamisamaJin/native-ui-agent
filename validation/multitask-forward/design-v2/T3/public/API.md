# CollectionConditionReviewPanel public API

Production paths: `alerttoast/Sources/AlertToast/CollectionConditionReviewPanel.swift` and `reply/Reply/app/src/main/java/com/example/reply/ui/components/CollectionConditionReviewPanel.kt`.

```swift
public struct CollectionConditionObject: Codable {
    public let id: String
    public let title: String
    public let material: String
    public let inspectionNote: String
    public let status: String
    public let reason: String?
    public let editable: Bool
    public let required: Bool
    public init(id: String, title: String, material: String, inspectionNote: String, status: String, reason: String?, editable: Bool, required: Bool) {
        self.id = id
        self.title = title
        self.material = material
        self.inspectionNote = inspectionNote
        self.status = status
        self.reason = reason
        self.editable = editable
        self.required = required
    }
}

public struct CollectionConditionReviewRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let focusID: String
    public let queueWidth: Double
    public let notes: [String]
    public let objects: [CollectionConditionObject]
    public init(id: String, title: String, context: String, focusID: String, queueWidth: Double, notes: [String], objects: [CollectionConditionObject]) {
        self.id = id
        self.title = title
        self.context = context
        self.focusID = focusID
        self.queueWidth = queueWidth
        self.notes = notes
        self.objects = objects
    }
}

public struct CollectionConditionAssessment: Codable {
    public let id: String
    public let status: String
    public let reason: String?
    public init(id: String, status: String, reason: String?) {
        self.id = id
        self.status = status
        self.reason = reason
    }
}

public struct CollectionConditionReviewPanel: View {
    public init(request: CollectionConditionReviewRequest, onConfirm: @escaping (String, [CollectionConditionAssessment]) -> Void)
    public var body: some View { get }
}
```

Kotlin package is `com.example.reply.ui.components`. Supply public data classes with the same field names and constructor order. Swift String/Int/Double/Bool map to Kotlin String/Int/Double/Boolean; arrays map to List<T>; String? maps to String?. No required additional parameters.

```kotlin
@Composable
fun CollectionConditionReviewPanel(request: CollectionConditionReviewRequest, onConfirm: (String, List<CollectionConditionAssessment>) -> Unit)
```

Callbacks contain the current request id and actual local business data, sorted by item id. Mixer callback additionally contains the actual mode. Collection callback contains every object's actual id/status/reason, including optional pending objects. Only enabled confirmation emits a callback. Editing controls never emit confirmation. Caller replacement never emits confirmation and resets local state from the new request on the same mounted component. Do not add expected labels, grading flags or observation state to the production API. All UI/eligibility/derivation logic belongs in production; bridges only decode input and format callback receipts.
