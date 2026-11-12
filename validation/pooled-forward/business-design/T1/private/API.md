# Fixed production API

These are API declarations, not a production implementation or substitute UI.

```swift
import SwiftUI
// Export from the AlertToast module. All fields are public; supply public field initializers.
public struct ReleaseLot: Codable, Equatable {
    public var id: String
    public var label: String
    public var detail: String
    public var units: Int
    public var available: Bool
    public var holdReason: String
}
public struct ShipmentReleaseFixture: Codable, Equatable {
    public var entityId: String
    public var entityTitle: String
    public var description: String
    public var lots: [ReleaseLot]
}
public struct ShipmentReleasePanel: View {
    public init(fixture: ShipmentReleaseFixture, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

```kotlin
package com.example.reply.ui.components.business
data class ReleaseLot(
    val id: String,
    val label: String,
    val detail: String,
    val units: Int,
    val available: Boolean,
    val holdReason: String,
)
data class ShipmentReleaseFixture(
    val entityId: String,
    val entityTitle: String,
    val description: String,
    val lots: List<ReleaseLot>,
)
@Composable
fun ShipmentReleasePanel(fixture: ShipmentReleaseFixture, onEvent: (String) -> Unit)
```

fixture.schema.json is the transport contract. All fields are nonoptional. IDs/labels are unique within each group and IDs use the delimiter-safe grammar. Allowed empty strings are explicit. Fixtures supply no local selection, approval, summary, eligibility override, or expected callback.

Production owns real business state, decision gating, and same-versus-changed entity replacement. The component is additive, exported by AlertToast on iOS and located in production app/src/main on Android. No internal ScrollView/LazyColumn, modal, popup, overlay, navigation route, timer, network, randomness, async state, or animation is needed. A single eager vertical flow fills the offered child width; the host owns scrolling.
