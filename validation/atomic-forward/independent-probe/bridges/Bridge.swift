import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        func color(_ key: String) -> Color {
            let value = UInt32(fixture[key] as! String, radix: 16)!
            return Color(red: Double((value >> 16) & 255)/255, green: Double((value >> 8) & 255)/255, blue: Double(value & 255)/255)
        }
        return AnyView(QuietMomentCard(title: fixture["title"] as! String, detail: fixture["body"] as! String, canvas: color("canvas"), band: color("band"), onAcknowledge: {onEvent("acknowledged")}))
    }
}
