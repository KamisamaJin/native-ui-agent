# Visitor access preclearance: public production contract

This is an additive reusable component. All types below are public production API.
No implementation exists in this design bundle. Swift declarations show signatures,
not compilable bodies. Kotlin models use immutable `val` fields; Swift uses `let`.

Swift file: `Sources/AlertToast/Business/VisitorAccessPreclearance.swift`, exported by existing product `AlertToast`.
Minimum deployment remains the stock package's iOS 14. Do not replace the package API.

```swift
public struct VisitorAccessInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let guestCount: Int
    public let sponsorActive: Bool
    public let badgeTrainingComplete: Bool
    public let researchCapacity: Int
    public let officeCapacity: Int
    public let verifiedIDs: Int
    public let labInductions: Int
    public let escortCount: Int
    public init(entityID: String, revision: Int, title: String, context: String, notes: [String], guestCount: Int, sponsorActive: Bool, badgeTrainingComplete: Bool, researchCapacity: Int, officeCapacity: Int, verifiedIDs: Int, labInductions: Int, escortCount: Int)
}
public struct VisitorAccessPreclearance: View {
    public init(input: VisitorAccessInput, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

Kotlin file: `app/src/main/java/com/example/reply/ui/components/business/VisitorAccessPreclearance.kt`.

```kotlin
package com.example.reply.ui.components.business

data class VisitorAccessInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val guestCount: Int,
    val sponsorActive: Bool,
    val badgeTrainingComplete: Bool,
    val researchCapacity: Int,
    val officeCapacity: Int,
    val verifiedIDs: Int,
    val labInductions: Int,
    val escortCount: Int
)
@Composable
fun VisitorAccessPreclearance(input: VisitorAccessInput, onEvent: (String) -> Unit)
```

The exact supplied bridges decode the immutable fixture and pass the same `onEvent`
directly. Android's `org.nativeobserver.ObserverBridge` object applies the stock
`ContrastAwareReplyTheme`. iOS's factory returns `AnyView` of the production view.
No bridge-owned UI, state, business decisions, fixture-index lookup, `.id`/key reset,
callback transformation, effects, tasks, timers, loading, network, or asynchronous work.
The production component owns all transient selection and receipt state.
