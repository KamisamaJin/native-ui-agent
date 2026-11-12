# Recruiting candidate disposition: public production contract

This is an additive reusable component. All types below are public production API.
No implementation exists in this design bundle. Swift declarations show signatures,
not compilable bodies. Kotlin models use immutable `val` fields; Swift uses `let`.

Every fixture `Int` must also satisfy fixture.schema.json. The shared transport
domain is signed 32-bit: -2147483648 through 2147483647. Existing field-specific
positive/nonnegative minima and portfolioScore's maximum100 narrow that domain.
In particular, revision is 0 through 2147483647 and accountBalanceCents is the full
signed 32-bit domain. Swift accepts this common domain and Kotlin serialization's
jsonPrimitive.int decodes it as Int. Out-of-schema values are outside this API contract.

Revision is an opaque comparison key supplied by the caller, never incremented
by this component. The published decisions use comparisons, key equality, and
string formatting; they require no sums or products. The finite frozen fixtures
do not establish arbitrary implementation arithmetic or universal overflow safety.

Swift file: `Sources/AlertToast/Business/CandidateDispositionReview.swift`, exported by existing product `AlertToast`.
Minimum deployment remains the stock package's iOS 14. Do not replace the package API.

```swift
public struct CandidateDispositionInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let portfolioScore: Int
    public let reviewerCapacity: Int
    public let technicalSlots: Int
    public let recruiterSlots: Int
    public let legalHold: Bool
    public let assessmentCount: Int
    public let openRoleCount: Int
    public init(entityID: String, revision: Int, title: String, context: String, notes: [String], portfolioScore: Int, reviewerCapacity: Int, technicalSlots: Int, recruiterSlots: Int, legalHold: Bool, assessmentCount: Int, openRoleCount: Int)
}
public struct CandidateDispositionReview: View {
    public init(input: CandidateDispositionInput, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

Kotlin file: `app/src/main/java/com/example/reply/ui/components/business/CandidateDispositionReview.kt`.

```kotlin
package com.example.reply.ui.components.business

data class CandidateDispositionInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val portfolioScore: Int,
    val reviewerCapacity: Int,
    val technicalSlots: Int,
    val recruiterSlots: Int,
    val legalHold: Boolean,
    val assessmentCount: Int,
    val openRoleCount: Int
)
@Composable
fun CandidateDispositionReview(input: CandidateDispositionInput, onEvent: (String) -> Unit)
```

The exact supplied bridges decode the immutable fixture and pass the same `onEvent`
directly. Android's `org.nativeobserver.ObserverBridge` object applies the stock
`ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false)`, matching the
fixed light/non-dynamic environment. Its fixture parameter is exactly the frozen
host's `kotlinx.serialization.json.JsonObject`; required primitives use
`jsonPrimitive.content` / `.int` / `.boolean`, and lists use `jsonArray.map`.
iOS's factory returns `AnyView` of the production view.
No bridge-owned UI, state, business decisions, fixture-index lookup, `.id`/key reset,
callback transformation, effects, tasks, timers, loading, network, or asynchronous work.
The production component owns all transient selection and receipt state.
