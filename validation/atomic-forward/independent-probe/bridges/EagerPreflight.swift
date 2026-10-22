import SwiftUI

// Independent simple capability probe. It contains no component-under-test design.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(VStack(alignment: .leading, spacing: 16) {
            Text(fixture["title"] as! String).font(.title).accessibilityIdentifier("probe.title")
            Button("Probe action") { onEvent("probe.primary") }
                .frame(maxWidth: .infinity, minHeight: 48).accessibilityIdentifier("probe.primary")
            ForEach(0..<12) { index in
                Text("Capability row \(index + 1)").frame(maxWidth: .infinity, minHeight: 64, alignment: .leading)
            }
            Button("Last native action") { onEvent("probe.last") }
                .frame(maxWidth: .infinity, minHeight: 48).accessibilityIdentifier("probe.last")
            Text(fixture["detail"] as! String).accessibilityIdentifier("probe.detail")
        })
    }
}
