import SwiftUI
import Foundation
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let data = try! JSONSerialization.data(withJSONObject: fixture)
        let request = try! JSONDecoder().decode(CollectionConditionReviewRequest.self, from: data)
        return AnyView(CollectionConditionReviewPanel(request: request, onConfirm: { id, decisions in
            let payload = decisions.sorted { $0.id < $1.id }.map { "\($0.id)=\($0.status)/\($0.reason ?? "-")" }.joined(separator: ",")
            onEvent("condition:\(id):\(payload)")
        }))
    }
}
