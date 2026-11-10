import SwiftUI
import AlertToast
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let seed = fixture["seed"] as? Int ?? 0
        return AnyView(NeutralCounter(seed: seed, onEvent: onEvent).id(seed))
    }
}
