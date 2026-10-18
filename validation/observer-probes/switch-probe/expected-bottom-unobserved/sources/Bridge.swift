import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let supplied = fixture["on"] as? Bool ?? false
        return AnyView(VStack(alignment: .leading, spacing: 18) {
            AlertToast(type: .regular, title: "Upstream native package probe")
                .accessibilityIdentifier("probe.upstream")
            Toggle("Generic controlled switch", isOn: Binding(get: { supplied }, set: { onEvent("probe.switch:\($0)") }))
                .accessibilityIdentifier("probe.switch")
            Text("Caller value: \(supplied ? "on" : "off")").accessibilityIdentifier("probe.state")
            Button("Native ordinary button") { onEvent("probe.button") }
                .accessibilityIdentifier("probe.button")
        })
    }
}
