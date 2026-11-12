# Fixed production API

These are API declarations, not a production implementation or substitute UI.

```swift
import SwiftUI
// Export from the AlertToast module. All fields are public; supply public field initializers.
public struct EquipmentReturnFixture: Codable, Equatable {
    public var entityId: String
    public var entityTitle: String
    public var description: String
    public var dataBearing: Bool
    public var restockAllowed: Bool
    public var repairAllowed: Bool
    public var recycleAllowed: Bool
    public var restockDetail: String
    public var repairDetail: String
    public var recycleDetail: String
}
public struct EquipmentReturnPanel: View {
    public init(fixture: EquipmentReturnFixture, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

```kotlin
package com.example.reply.ui.components.business
data class EquipmentReturnFixture(
    val entityId: String,
    val entityTitle: String,
    val description: String,
    val dataBearing: Boolean,
    val restockAllowed: Boolean,
    val repairAllowed: Boolean,
    val recycleAllowed: Boolean,
    val restockDetail: String,
    val repairDetail: String,
    val recycleDetail: String,
)
@Composable
fun EquipmentReturnPanel(fixture: EquipmentReturnFixture, onEvent: (String) -> Unit)
```

fixture.schema.json is the transport contract. All fields are nonoptional. IDs/labels are unique within each group and IDs use the delimiter-safe grammar. Allowed empty strings are explicit. Fixtures supply no local selection, approval, summary, eligibility override, or expected callback.

Production owns real business state, decision gating, and same-versus-changed entity replacement. The component is additive, exported by AlertToast on iOS and located in production app/src/main on Android. No internal ScrollView/LazyColumn, modal, popup, overlay, navigation route, timer, network, randomness, async state, or animation is needed. A single eager vertical flow fills the offered child width; the host owns scrolling.
