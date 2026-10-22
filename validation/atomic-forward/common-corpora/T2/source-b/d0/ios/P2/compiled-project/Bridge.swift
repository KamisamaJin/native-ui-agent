import SwiftUI
import AlertToast

// Adapter only: no local business state, styling, semantic IDs, or replacement UI.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        do {
            let data = try JSONSerialization.data(withJSONObject: fixture)
            let model = try JSONDecoder().decode(RiverSensorTriageModel.self, from: data)
            return AnyView(RiverSensorTriageBoard(model: model,
                onSelect: { id in onEvent("river:select:\(id)") },
                onDetailsChange: { expanded in onEvent("river:details:\(expanded ? "open" : "closed")") },
                onAcknowledge: { id in onEvent("river:acknowledge:\(id)") }))
        } catch { fatalError("Invalid approved fixture: \(error)") }
    }
}
