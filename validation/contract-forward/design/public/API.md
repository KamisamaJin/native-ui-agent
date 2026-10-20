# Production API

Swift file: `Sources/AlertToast/WorkshopEnrollmentCard.swift` (inside the pinned AlertToast package). Public SwiftUI entry point and value types:

```swift
public struct WorkshopCourse: Codable, Equatable {
    public var id: String
    public var title: String
    public var detail: String
    public var seatPriceCents: Int
    public var capacity: Int
    public var onsiteAvailable: Bool
    public var workbookAvailable: Bool
}
public struct WorkshopCatalog: Codable, Equatable {
    public var title: String
    public var detail: String
    public var courses: [WorkshopCourse]
    public var remoteDiscountCents: Int
    public var onsiteFeeCents: Int
    public var workbookCents: Int
}
public enum WorkshopAttendance: String, Codable { case remote, onsite }
public struct WorkshopReservation: Equatable {
    public var courseID: String
    public var mode: WorkshopAttendance
    public var seats: Int
    public var workbook: Bool
}
public struct WorkshopEnrollmentCard: View {
    public init(catalog: WorkshopCatalog, onReserve: @escaping (WorkshopReservation) -> Void)
    public var body: some View { get }
}
```

Provide public memberwise initializers for the value structs, so production callers can construct them; Codable must decode fixtures with the property spelling shown. Add API without changing existing host components. The input catalog must remain a live value property; never use input-derived `.id(...)` to recreate the entire card on caller replacement.

Kotlin file: `app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt`, package `com.example.reply.ui.components`:

```kotlin
data class WorkshopCourse(val id: String, val title: String, val detail: String,
    val seatPriceCents: Int, val capacity: Int,
    val onsiteAvailable: Boolean, val workbookAvailable: Boolean)
data class WorkshopCatalog(val title: String, val detail: String,
    val courses: List<WorkshopCourse>, val remoteDiscountCents: Int,
    val onsiteFeeCents: Int, val workbookCents: Int)
enum class WorkshopAttendance { REMOTE, ONSITE }
data class WorkshopReservation(val courseID: String, val mode: WorkshopAttendance,
    val seats: Int, val workbook: Boolean)
@Composable
fun WorkshopEnrollmentCard(catalog: WorkshopCatalog,
    onReserve: (WorkshopReservation) -> Unit, modifier: Modifier = Modifier)
```

Callers own the outer scroll and theme. The card reads native text size and direction. Input equivalence must not trigger spurious callbacks or lose selections. The bridge calls this API directly. Callback wire event is `reserve:<courseID>:remote|onsite:<seats>:true|false`; event transport is solely the bridge's serialization of the production reservation callback. No callbacks for changes, Edit or caller replacement.

Observer input layout: each `cases/<id>/fixtures.json` is an object containing `initial` (catalog), `updates` (ordered catalog replacements), width, theme, dynamic_type, fontScale, direction, viewportHeight, state_capture:false, max_scrolls and observation_targets. Separate literal actions are in `actions.ios.json` / `actions.android.json`; the compiler emits enriched action files. Both platforms follow the same route. Apply-next-fixture advances exactly one input on the same UI instance. Compose observation establishes semantic OnClick, not physical Android touch. P1 selects 5 states; P2 selects 6 states. All indices are zero-based original action indices.
