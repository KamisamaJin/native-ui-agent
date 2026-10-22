import SwiftUI
import AlertToast

// Adapter only: no local business state, styling, semantic IDs, or replacement UI.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        do {
            let data = try JSONSerialization.data(withJSONObject: fixture)
            let model = try JSONDecoder().decode(BicycleServiceIntakeModel.self, from: data)
            return AnyView(BicycleServiceIntake(model: model,
                onToggle: { id, selected in onEvent("bicycle:toggle:\(id):\(selected ? "true" : "false")") },
                onDetailsChange: { expanded in onEvent("bicycle:details:\(expanded ? "open" : "closed")") },
                onSubmit: { ids in onEvent("bicycle:submit:\(ids.sorted().joined(separator: ","))") }))
        } catch { fatalError("Invalid approved fixture: \(error)") }
    }
}
