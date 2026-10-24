import SwiftUI
import AlertToast
// Source-API probe only. Never launched or used as a business component.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let _ = AlertToast(type: .regular, title: "Source API probe")
        return AnyView(Text(fixture["title"] as? String ?? "Source API probe"))
    }
}
