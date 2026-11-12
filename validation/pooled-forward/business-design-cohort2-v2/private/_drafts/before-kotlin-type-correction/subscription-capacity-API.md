# Subscription capacity change: public production contract

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

Swift file: `Sources/AlertToast/Business/SubscriptionCapacityChange.swift`, exported by existing product `AlertToast`.
Minimum deployment remains the stock package's iOS 14. Do not replace the package API.

```swift
public struct SubscriptionCapacityInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let seatCount: Int
    public let teamQuota: Int
    public let scaleQuota: Int
    public let prepaidMonths: Int
    public let accountBalanceCents: Int
    public init(entityID: String, revision: Int, title: String, context: String, notes: [String], seatCount: Int, teamQuota: Int, scaleQuota: Int, prepaidMonths: Int, accountBalanceCents: Int)
}
public struct SubscriptionCapacityChange: View {
    public init(input: SubscriptionCapacityInput, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

Kotlin file: `app/src/main/java/com/example/reply/ui/components/business/SubscriptionCapacityChange.kt`.

```kotlin
package com.example.reply.ui.components.business

data class SubscriptionCapacityInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val seatCount: Int,
    val teamQuota: Int,
    val scaleQuota: Int,
    val prepaidMonths: Int,
    val accountBalanceCents: Int
)
@Composable
fun SubscriptionCapacityChange(input: SubscriptionCapacityInput, onEvent: (String) -> Unit)
```

The exact supplied bridges decode the immutable fixture and pass the same `onEvent`
directly. Android's `org.nativeobserver.ObserverBridge` object applies the stock
`ContrastAwareReplyTheme`. iOS's factory returns `AnyView` of the production view.
No bridge-owned UI, state, business decisions, fixture-index lookup, `.id`/key reset,
callback transformation, effects, tasks, timers, loading, network, or asynchronous work.
The production component owns all transient selection and receipt state.
