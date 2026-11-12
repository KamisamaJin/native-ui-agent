import Foundation
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let bytes = try! JSONSerialization.data(withJSONObject: fixture)
        let decoded = try! JSONDecoder().decode(ShipmentReleaseFixture.self, from: bytes)
        return AnyView(ShipmentReleasePanel(fixture: decoded, onEvent: onEvent))
    }
}
