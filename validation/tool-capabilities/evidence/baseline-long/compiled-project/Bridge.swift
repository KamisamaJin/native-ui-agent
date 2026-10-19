import SwiftUI

// Generic native capability probe. No business component or outcomes are represented here.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(CapabilityProbe(fixture: fixture, onEvent: onEvent))
    }
}

private struct CapabilityProbe: View {
    let fixture: [String: Any]
    let onEvent: (String) -> Void
    @State private var toggled = false
    @State private var expanded = false
    private var generation: String { fixture["generation"] as? String ?? "initial" }
    private var mode: String { fixture["mode"] as? String ?? "semantic" }
    private var disabled: Bool { fixture["disabled"] as? Bool ?? true }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Capability \(generation)").accessibilityIdentifier("cap.title")
            if mode == "semantic" { semanticContent }
            else { longContent }
        }
    }

    private var semanticContent: some View {
        VStack(alignment: .leading, spacing: 10) {
            VStack {
                Button("Actual button leaf") { onEvent("cap.button") }
                    .frame(maxWidth: .infinity).frame(height: 48)
                    .accessibilityIdentifier("cap.button.leaf")
                    .disabled(disabled)
            }
            .accessibilityElement(children: .contain)
            .accessibilityLabel("Selected semantic button group")
            .accessibilityAddTraits(.isSelected)
            .accessibilityIdentifier("cap.button.semantic")

            VStack {
                Toggle("Actual switch leaf", isOn: Binding(get: { toggled }, set: {
                    toggled = $0; onEvent("cap.switch.\($0 ? "on" : "off")")
                }))
                .accessibilityIdentifier("cap.switch.leaf")
                .disabled(disabled)
            }
            .accessibilityElement(children: .contain)
            .accessibilityLabel("Selected semantic switch group")
            .accessibilityAddTraits(.isSelected)
            .accessibilityIdentifier("cap.switch.semantic")

            VStack {
                Button("Left actual leaf") { onEvent("cap.ambiguous.left") }
                    .frame(maxWidth: .infinity).frame(height: 44)
                    .accessibilityIdentifier("cap.ambiguous.left")
                Button("Right actual leaf") { onEvent("cap.ambiguous.right") }
                    .frame(maxWidth: .infinity).frame(height: 44)
                    .accessibilityIdentifier("cap.ambiguous.right")
            }
            .accessibilityElement(children: .contain)
            .accessibilityLabel("Ambiguous semantic group")
            .accessibilityIdentifier("cap.ambiguous.semantic")

            HStack {
                Button("Duplicate one") { onEvent("cap.duplicate.one") }
                    .accessibilityIdentifier("cap.duplicate")
                Button("Duplicate two") { onEvent("cap.duplicate.two") }
                    .accessibilityIdentifier("cap.duplicate")
            }.frame(height: 44)
            Button("Label only native action") { onEvent("cap.label") }
                .frame(maxWidth: .infinity).frame(height: 44)
            Text("Semantic generation \(generation)").accessibilityIdentifier("cap.detail")
        }
    }

    private var longContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button("Top native action") { onEvent("cap.top") }
                .frame(maxWidth: .infinity).frame(height: 48)
                .accessibilityIdentifier("cap.top")
            ForEach(0..<6) { n in
                Text("Upper \(generation) row \(n)")
                    .frame(maxWidth: .infinity, minHeight: 88, alignment: .leading)
                    .accessibilityIdentifier("cap.upper.\(n)")
            }
            VStack(alignment: .leading) {
                Text("Tall row start \(generation)").accessibilityIdentifier("cap.tall.start")
                Spacer(minLength: 0)
                Text("Tall row middle \(generation)").accessibilityIdentifier("cap.tall.middle")
                Spacer(minLength: 0)
                Text("Tall row end \(generation)").accessibilityIdentifier("cap.tall.end")
            }
            .frame(maxWidth: .infinity).frame(height: 940)
            .background(Color.gray.opacity(0.1))
            .accessibilityElement(children: .contain)
            .accessibilityLabel("Tall semantic row \(generation)")
            .accessibilityIdentifier("cap.tall")
            ForEach(0..<10) { n in
                Text("Lower \(generation) row \(n)")
                    .frame(maxWidth: .infinity, minHeight: 88, alignment: .leading)
                    .accessibilityIdentifier("cap.lower.\(n)")
            }
            Button("Distant native action") { onEvent("cap.distant") }
                .frame(maxWidth: .infinity).frame(height: 48)
                .accessibilityIdentifier("cap.distant")
            Button("Expand native content") { expanded = true; onEvent("cap.expand") }
                .frame(maxWidth: .infinity).frame(height: 48)
                .accessibilityIdentifier("cap.expand")
            if expanded {
                Text("Expanded state \(generation)").accessibilityIdentifier("cap.expanded.marker")
                ForEach(0..<8) { n in
                    Text("Expanded \(generation) row \(n)")
                        .frame(maxWidth: .infinity, minHeight: 88, alignment: .leading)
                        .accessibilityIdentifier("cap.expanded.\(n)")
                }
            }
            Button("Label only distant action") { onEvent("cap.label.distant") }
                .frame(maxWidth: .infinity).frame(height: 48)
            Text("End \(generation) expanded=\(expanded)").accessibilityIdentifier("cap.end")
        }
    }
}
