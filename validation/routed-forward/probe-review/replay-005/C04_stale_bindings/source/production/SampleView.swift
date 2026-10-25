// Neutral source capsule for forward probes; synthetic transport does not run it.
import SwiftUI

struct PaperSampleView: View {
    let reverse: Bool
    var body: some View {
        VStack(spacing: 12) {
            Text(reverse ? "Reverse" : "Front")
                .accessibilityIdentifier("paper.caption")
            Rectangle()
                .fill(reverse ? Color.orange : Color.blue)
                .frame(width: 66, height: 44)
                .accessibilityElement()
                .accessibilityIdentifier("paper.sample")
        }
    }
}
// changed source
