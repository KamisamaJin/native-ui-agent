import Foundation
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let bytes = try! JSONSerialization.data(withJSONObject: fixture)
        let decoded = try! JSONDecoder().decode(EquipmentReturnFixture.self, from: bytes)
        return AnyView(EquipmentReturnPanel(fixture: decoded, onEvent: onEvent))
    }
}
