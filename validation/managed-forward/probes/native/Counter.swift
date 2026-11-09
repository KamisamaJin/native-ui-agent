import SwiftUI

public struct NeutralCounter: View {
    let seed: Int
    let onEvent: (String) -> Void
    @State private var count: Int
    public init(seed: Int, onEvent: @escaping (String) -> Void) {
        self.seed = seed; self.onEvent = onEvent; _count = State(initialValue: seed)
    }
    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Tally: \(count)").accessibilityIdentifier("counter.tally")
            Button("Count") { count += 1; onEvent("increment") }
                .frame(height: 48).accessibilityIdentifier("counter.increment")
            Button("Unavailable by design") { onEvent("disabled") }
                .disabled(true).frame(height: 48).accessibilityIdentifier("counter.disabled")
            HStack {
                Button("Left") { onEvent("left") }
                Button("Right") { onEvent("right") }
            }.accessibilityElement(children: .contain).accessibilityIdentifier("counter.pair")
            Button("Continue") { onEvent("continue") }
                .disabled(count == 0).frame(height: 48).accessibilityIdentifier("counter.continue")
        }
    }
}
