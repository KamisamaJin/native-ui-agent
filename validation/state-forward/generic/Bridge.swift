import SwiftUI

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(Panel(rows: fixture["rows"] as? Int ?? 8,
                      token: fixture["token"] as? String ?? "A", onEvent: onEvent))
    }
}
private struct Panel: View {
    let rows: Int
    let token: String
    let onEvent: (String) -> Void
    @State private var expanded = false
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Panel \(token)").accessibilityIdentifier("probe.header")
            Button(expanded ? "Hide sections" : "Show sections") {
                expanded.toggle(); onEvent("expanded")
            }.accessibilityIdentifier("probe.disclosure")
            Button("Unavailable") { onEvent("disabled") }.disabled(true)
                .accessibilityIdentifier("probe.disabled")
            ForEach(0..<rows, id: \.self) { n in
                Text("Section \(n)").frame(minHeight: 48)
                    .accessibilityIdentifier("probe.row.\(n)")
            }
            if expanded {
                Text(String(repeating: "Neutral section details. ", count: 24))
                    .accessibilityIdentifier("probe.detail")
            }
            Text("End \(token)").accessibilityIdentifier("probe.footer")
            Button("Continue \(token)") { onEvent("secondary") }
                .accessibilityIdentifier("probe.secondary")
        }
    }
}
