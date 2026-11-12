# Fixed production API

These are API declarations, not a production implementation or substitute UI.

```swift
import SwiftUI
// Export from the AlertToast module. All fields are public; supply public field initializers.
public struct NoticeAudience: Codable, Equatable {
    public var id: String
    public var label: String
    public var detail: String
    public var recipients: Int
    public var allowed: Bool
    public var blockedReason: String
}
public struct OutageNoticeFixture: Codable, Equatable {
    public var entityId: String
    public var entityTitle: String
    public var description: String
    public var subject: String
    public var message: String
    public var workaround: String
    public var audiences: [NoticeAudience]
}
public struct OutageNoticePanel: View {
    public init(fixture: OutageNoticeFixture, onEvent: @escaping (String) -> Void)
    public var body: some View { get }
}
```

```kotlin
package com.example.reply.ui.components.business
data class NoticeAudience(
    val id: String,
    val label: String,
    val detail: String,
    val recipients: Int,
    val allowed: Boolean,
    val blockedReason: String,
)
data class OutageNoticeFixture(
    val entityId: String,
    val entityTitle: String,
    val description: String,
    val subject: String,
    val message: String,
    val workaround: String,
    val audiences: List<NoticeAudience>,
)
@Composable
fun OutageNoticePanel(fixture: OutageNoticeFixture, onEvent: (String) -> Unit)
```

fixture.schema.json is the transport contract. All fields are nonoptional. IDs/labels are unique within each group and IDs use the delimiter-safe grammar. Allowed empty strings are explicit. Fixtures supply no local selection, approval, summary, eligibility override, or expected callback.

Production owns real business state, decision gating, and same-versus-changed entity replacement. The component is additive, exported by AlertToast on iOS and located in production app/src/main on Android. No internal ScrollView/LazyColumn, modal, popup, overlay, navigation route, timer, network, randomness, async state, or animation is needed. A single eager vertical flow fills the offered child width; the host owns scrolling.
