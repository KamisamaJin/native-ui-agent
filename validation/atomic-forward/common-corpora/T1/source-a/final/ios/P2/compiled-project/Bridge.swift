import SwiftUI
import AlertToast

// Adapter only: no local business state, styling, semantic IDs, or replacement UI.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        do {
            let data = try JSONSerialization.data(withJSONObject: fixture)
            let model = try JSONDecoder().decode(WorkshopSlotPlannerModel.self, from: data)
            return AnyView(WorkshopSlotPlanner(model: model,
                onSelect: { id in onEvent("workshop:select:\(id)") },
                onDetailsChange: { expanded in onEvent("workshop:details:\(expanded ? "open" : "closed")") },
                onReserve: { id in onEvent("workshop:reserve:\(id)") }))
        } catch { fatalError("Invalid approved fixture: \(error)") }
    }
}
