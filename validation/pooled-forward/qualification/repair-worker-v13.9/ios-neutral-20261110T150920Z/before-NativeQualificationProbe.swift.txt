import Foundation
import SwiftUI

// Neutral qualification component. Not a production business UI substitute.
@available(iOS 14.0, macOS 11.0, tvOS 14.0, watchOS 7.0, *)
public struct NativeQualificationProbe: View {
    private let marker: String
    private let detail: String
    private let onEvent: (String) -> Void

    @State private var instanceID = UUID().uuidString
    @State private var taps = 0

    public init(marker: String, detail: String, onEvent: @escaping (String) -> Void) {
        self.marker = marker
        self.detail = detail
        self.onEvent = onEvent
    }

    public var body: some View {
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
                taps += 2
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
