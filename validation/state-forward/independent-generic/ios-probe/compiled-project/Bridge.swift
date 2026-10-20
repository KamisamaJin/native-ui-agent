import SwiftUI

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(VStack(alignment: .leading, spacing: 16) {
            Text(fixture["title"] as? String ?? "").accessibilityIdentifier("probe.title")
            Button("Activate probe") { onEvent("probe.activated") }
                .frame(maxWidth: .infinity, minHeight: 48).accessibilityIdentifier("probe.action")
            ForEach(0..<8, id: \.self) { i in
                Text("Probe row \(i + 1)").frame(maxWidth: .infinity, minHeight: 80, alignment: .leading)
            }
            Text(fixture["footer"] as? String ?? "").accessibilityIdentifier("probe.footer")
        })
    }
}
