import SwiftUI
import Foundation
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let data = try! JSONSerialization.data(withJSONObject: fixture)
        let request = try! JSONDecoder().decode(BroadcastCueMixerRequest.self, from: data)
        return AnyView(BroadcastCueMixerPanel(request: request, onConfirm: { id, mode, channels in
            let payload = channels.sorted { $0.id < $1.id }.map { "\($0.id)=\($0.level)/\($0.muted ? "true" : "false")" }.joined(separator: ",")
            onEvent("mix:\(id):\(mode):\(payload)")
        }))
    }
}
