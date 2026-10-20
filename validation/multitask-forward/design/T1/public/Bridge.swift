import SwiftUI
import Foundation
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let data = try! JSONSerialization.data(withJSONObject: fixture)
        let request = try! JSONDecoder().decode(ExpeditionPackRequest.self, from: data)
        return AnyView(ExpeditionPackPanel(request: request) { id, ids, option in
            onEvent("packed:\(id):\(ids.sorted().joined(separator: ",")):\(option ? "true" : "false")")
        })
    }
}
