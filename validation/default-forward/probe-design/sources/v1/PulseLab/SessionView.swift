import SwiftUI

// Production view for the neutral Pulse Lab fixture app.
struct SessionView: View {
    enum Phase: String { case idle = "Idle", running = "Running", paused = "Paused" }
    @State private var phase: Phase = .idle
    @State private var count = 0
    @State private var previewPaused = false

    var body: some View {
        VStack(spacing: 24) {
            Text("Pulse Lab").font(.largeTitle)
            VStack(spacing: 16) {
                Text(phase.rawValue).accessibilityIdentifier("session.phase")
                Text("Count \(count)").font(.title).accessibilityIdentifier("session.count")
                Button(phase == .idle ? "Start" : phase == .running ? "Pause" : "Resume") {
                    switch phase {
                    case .idle: count = 0; phase = .running
                    case .running: phase = .paused
                    case .paused: phase = .running
                    }
                }
                .accessibilityIdentifier("session.primary")
                if phase == .running {
                    Button("Step") { count += 1 }
                }
                if phase != .idle {
                    Button("Reset") { count = 0; phase = .idle }
                        .accessibilityIdentifier("session.reset")
                }
            }
            .padding(24)
            .accessibilityElement(children: .contain)
            .accessibilityIdentifier("session.group")
            Divider()
            VStack(spacing: 12) {
                Text("Preview")
                Text(previewPaused ? "Still" : "Moving")
                    .accessibilityIdentifier("preview.phase")
                Button(previewPaused ? "Resume" : "Pause") { previewPaused.toggle() }
                    .accessibilityIdentifier("session.primary")
            }
            .accessibilityElement(children: .contain)
            .accessibilityIdentifier("preview.group")
        }
        .padding(24)
        .buttonStyle(.borderedProminent)
    }
}
