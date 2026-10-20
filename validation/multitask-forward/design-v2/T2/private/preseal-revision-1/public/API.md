# BroadcastCueMixerPanel public API

Production paths: `alerttoast/Sources/AlertToast/BroadcastCueMixerPanel.swift` and `reply/Reply/app/src/main/java/com/example/reply/ui/components/BroadcastCueMixerPanel.kt`.

```swift
public struct BroadcastMixChannel: Codable {
    public let id: String
    public let name: String
    public let caption: String
    public let level: Int
    public let muted: Bool
    public let locked: Bool
    public init(id: String, name: String, caption: String, level: Int, muted: Bool, locked: Bool) {
        self.id = id
        self.name = name
        self.caption = caption
        self.level = level
        self.muted = muted
        self.locked = locked
    }
}

public struct BroadcastCueMixerRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let maxLiveUnits: Int
    public let maxLevel: Int
    public let mode: String
    public let stepperWidth: Double
    public let notes: [String]
    public let channels: [BroadcastMixChannel]
    public init(id: String, title: String, context: String, maxLiveUnits: Int, maxLevel: Int, mode: String, stepperWidth: Double, notes: [String], channels: [BroadcastMixChannel]) {
        self.id = id
        self.title = title
        self.context = context
        self.maxLiveUnits = maxLiveUnits
        self.maxLevel = maxLevel
        self.mode = mode
        self.stepperWidth = stepperWidth
        self.notes = notes
        self.channels = channels
    }
}

public struct BroadcastCueMixerPanel: View {
    public init(request: BroadcastCueMixerRequest, onConfirm: @escaping (String, String, [BroadcastMixChannel]) -> Void)
    public var body: some View { get }
}
```

Kotlin package is `com.example.reply.ui.components`. Supply public data classes with the same field names and constructor order. Swift String/Int/Double/Bool map to Kotlin String/Int/Double/Boolean; arrays map to List<T>; String? maps to String?. No required additional parameters.

```kotlin
@Composable
fun BroadcastCueMixerPanel(request: BroadcastCueMixerRequest, onConfirm: (String, String, List<BroadcastMixChannel>) -> Unit)
```

Callbacks contain the current request id and actual local business data, sorted by item id. Mixer callback additionally contains the actual mode. Collection callback contains every object's actual id/status/reason, including optional pending objects. Only enabled confirmation emits a callback. Editing controls never emit confirmation. Caller replacement never emits confirmation and resets local state from the new request on the same mounted component. Do not add expected labels, grading flags or observation state to the production API. All UI/eligibility/derivation logic belongs in production; bridges only decode input and format callback receipts.
