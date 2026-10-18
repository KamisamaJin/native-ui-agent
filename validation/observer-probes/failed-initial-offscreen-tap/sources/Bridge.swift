import SwiftUI

// Independent adapter preflight only. Business observations supply their own Bridge.swift.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(ProbeView(fixture: fixture, onEvent: onEvent))
    }
}

private struct ProbeView: View {
    let fixture: [String: Any]
    let onEvent: (String) -> Void
    @Environment(\.colorScheme) private var scheme
    @Environment(\.dynamicTypeSize) private var type
    @Environment(\.layoutDirection) private var direction
    var body: some View {
        LazyVStack(alignment: .leading, spacing: 16) {
            Text(fixture["title"] as? String ?? "Native observer probe").font(.title).accessibilityIdentifier("probe.title")
            Text("Native environment: \(scheme == .dark ? "dark" : "light"), \(String(describing: type)), \(direction == .rightToLeft ? "rtl" : "ltr")")
                .font(.caption2).accessibilityIdentifier("probe.environment")
            Text("Native body text: theme, text sizing and writing direction are supplied by the caller.").font(.body).accessibilityIdentifier("probe.body")
            Button("Probe 48 point action") { onEvent("probe.primary") }
                .frame(maxWidth: .infinity).frame(height: 48).contentShape(Rectangle())
                .accessibilityIdentifier("probe.primary")
            ForEach(0..<18) { index in
                Text("Native tall content row \(index + 1)").frame(maxWidth: .infinity, minHeight: 64, alignment: .leading)
                    .accessibilityIdentifier("probe.row.\(index)")
            }
            Button("Last native action") { onEvent("probe.last") }
                .frame(maxWidth: .infinity).frame(height: 48).contentShape(Rectangle())
                .accessibilityIdentifier("probe.last")
            Text(fixture["detail"] as? String ?? "Initial detail").accessibilityIdentifier("probe.detail")
        }
    }
}
