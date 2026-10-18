import SwiftUI
import AlertToast

// Caller-owned controlled state. The production View keeps its identity across external updates.
private struct VisitObserverBody: View {
    let seed: String
    let onEvent: (String) -> Void
    @State private var model: VisitRescheduleModel
    init(seed: String, onEvent: @escaping (String) -> Void) {
        self.seed = seed; self.onEvent = onEvent
        _model = State(initialValue: try! JSONDecoder().decode(VisitRescheduleModel.self, from: Data(seed.utf8)))
    }
    private func replace(_ key: String, _ value: Any) {
        var json = try! JSONSerialization.jsonObject(with: JSONEncoder().encode(model)) as! [String: Any]
        json[key] = value
        model = try! JSONDecoder().decode(VisitRescheduleModel.self, from: JSONSerialization.data(withJSONObject: json))
    }
    var body: some View {
        VisitReschedulePanel(model: model) { action in
            switch action {
            case .selectSlot(let id):
                onEvent("select_slot:" + id)
                if model.selectedSlotId != id { replace("feeAccepted", false) }
                replace("selectedSlotId", id)
            case .setFeeAccepted(let value): onEvent("fee_accepted:" + String(value)); replace("feeAccepted", value)
            case .confirm(let id): onEvent("confirm:" + id)
            case .retry: onEvent("retry")
            case .done: onEvent("done")
            }
        }
        .onChange(of: seed) { value in
            model = try! JSONDecoder().decode(VisitRescheduleModel.self, from: Data(value.utf8))
        }
    }
}
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let data = try! JSONSerialization.data(withJSONObject: fixture["model"]!, options: [.sortedKeys])
        return AnyView(VisitObserverBody(seed: String(decoding: data, as: UTF8.self), onEvent: onEvent))
    }
}
