import Foundation
import SwiftUI

// Qualification capability fixture only. This is not a production UI substitute.
enum ObserverBridge {
    static func make(
        fixture: [String: Any],
        onEvent: @escaping (String) -> Void
    ) -> AnyView {
        guard let marker = fixture["marker"] as? String,
              let detail = fixture["detail"] as? String else {
            preconditionFailure("Qualification fixture requires marker and detail")
        }
        return AnyView(QualificationProbe(marker: marker, detail: detail, onEvent: onEvent))
    }
}

private struct QualificationProbe: View {
    let marker: String
    let detail: String
    let onEvent: (String) -> Void

    @State private var instanceID = UUID().uuidString
    @State private var taps = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Native capability qualification")
                .font(.title2)
                .accessibilityIdentifier("probe.title")
            Text(marker)
                .accessibilityIdentifier("probe.marker")
            Text("Instance")
                .accessibilityValue(instanceID)
                .accessibilityIdentifier("probe.instance")
            Text("Tap count: \(taps)")
                .accessibilityIdentifier("probe.count")

            Button("Primary native action") {
                taps += 1
                onEvent("probe.primary")
            }
            .frame(maxWidth: .infinity)
            .frame(height: 48)
            .contentShape(Rectangle())
            .accessibilityIdentifier("probe.primary")

            Button("Disabled native action") {
                onEvent("probe.disabled")
            }
            .frame(maxWidth: .infinity)
            .frame(height: 48)
            .contentShape(Rectangle())
            .disabled(true)
            .accessibilityIdentifier("probe.disabled")

            LazyVStack(alignment: .leading, spacing: 16) {
                ForEach(0..<18) { index in
                    Text("Native content row \(index + 1)")
                        .frame(maxWidth: .infinity, minHeight: 64, alignment: .leading)
                        .accessibilityIdentifier("probe.row.\(index)")
                }
                Button("Last native action") {
                    onEvent("probe.last")
                }
                .frame(maxWidth: .infinity)
                .frame(height: 48)
                .contentShape(Rectangle())
                .accessibilityIdentifier("probe.last")
                Text(detail)
                    .accessibilityIdentifier("probe.detail")
            }
        }
    }
}
