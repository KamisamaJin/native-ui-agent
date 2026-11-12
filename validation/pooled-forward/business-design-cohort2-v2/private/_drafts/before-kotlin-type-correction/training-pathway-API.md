# Training pathway enrollment: public production contract

This is an additive reusable component. All types below are public production API.
No implementation exists in this design bundle. Swift declarations show signatures,
not compilable bodies. Kotlin models use immutable `val` fields; Swift uses `let`.

Every fixture `Int` must also satisfy fixture.schema.json. The shared transport
domain is signed32-bit: -2147483648 through2147483647. Existing field-specific
positive/nonnegative minima and portfolioScore's maximum100 narrow that domain.
In particular, revision is0 through2147483647 and accountBalanceCents is the full
signed32-bit domain. Swift accepts this common domain and Kotlin/Gson decodes it
without numeric narrowing. Out-of-schema values are outside this API contract.

Revision is an opaque comparison key supplied by the caller, never incremented
by this component. The published decisions use comparisons, key equality, and
string formatting; they require no sums or products. The finite frozen fixtures
do not establish arbitrary implementation arithmetic or universal overflow safety.

Swift file: `Sources/AlertToast/Business/TrainingPathwayEnrollment.swift`, exported by existing product `AlertToast`.
Minimum deployment remains the stock package's iOS 14. Do not replace the package API.

```swift
public struct TrainingPathwayInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let completedHours: Int
    public let completedModules: [String]
    public let cohortSeats: Int
    public let deviceCredits: Int
    public let assessmentSlots: Int
    public let practiceSeats: Int
    public init(entityID: String, revision: Int, title: String, context: String, notes: [String], completedHours: Int, completedModules: [String], cohortSeats: Int, deviceCredits: Int, assessmentSlots: Int, practiceSeats: Int)
}
public struct TrainingPathwayEnrollment: View {
    public init(input: TrainingPathwayInput, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

Kotlin file: `app/src/main/java/com/example/reply/ui/components/business/TrainingPathwayEnrollment.kt`.

```kotlin
package com.example.reply.ui.components.business

data class TrainingPathwayInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val completedHours: Int,
    val completedModules: List<String>,
    val cohortSeats: Int,
    val deviceCredits: Int,
    val assessmentSlots: Int,
    val practiceSeats: Int
)
@Composable
fun TrainingPathwayEnrollment(input: TrainingPathwayInput, onEvent: (String) -> Unit)
```

The exact supplied bridges decode the immutable fixture and pass the same `onEvent`
directly. Android's `org.nativeobserver.ObserverBridge` object applies the stock
`ContrastAwareReplyTheme`. iOS's factory returns `AnyView` of the production view.
No bridge-owned UI, state, business decisions, fixture-index lookup, `.id`/key reset,
callback transformation, effects, tasks, timers, loading, network, or asynchronous work.
The production component owns all transient selection and receipt state.
