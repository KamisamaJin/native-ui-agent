import SwiftUI

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(Surface(rows: fixture["rows"] as? Int ?? 1, onEvent: onEvent))
    }
}
private struct Surface: View {
    let rows: Int
    let onEvent: (String) -> Void
    @State private var expanded = false
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Generic observation surface").accessibilityIdentifier("gen.title")
            Button("Deliver correct event") { onEvent("delivered") }
                .accessibilityIdentifier("gen.correct")
            Button("Disabled event") { onEvent("disabled") }.disabled(true)
                .accessibilityIdentifier("gen.disabled")
            Button("Silent action") {}.accessibilityIdentifier("gen.silent")
            Button("Wrong event") { onEvent("different") }.accessibilityIdentifier("gen.wrong")
            ForEach(0..<rows, id: \.self) { n in
                Text("Native generic row \(n)").frame(minHeight: 36)
                    .accessibilityIdentifier("gen.row.\(n)")
            }
            if expanded {
                Text(String(repeating: "Expanded neutral measurement text. ", count: 24))
                    .accessibilityIdentifier("gen.expanded")
            }
            Button(expanded ? "Collapse measured detail" : "Expand measured detail") {
                expanded.toggle(); onEvent("expanded")
            }.frame(maxWidth: .infinity, minHeight: 48).accessibilityIdentifier("gen.disclosure")
            Text("Generic final label").accessibilityIdentifier("gen.tail")
        }
    }
}
