import SwiftUI

/// Caller-owned facts and display content for a training enrollment request.
public struct TrainingPathwayInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let completedHours: Int
    public let completedModules: [String]
    public let cohortSeats: Int
    public let deviceCredits: Int
    public let assessmentSlots: Int
    public let practiceSeats: Int

    public init(
        entityID: String,
        revision: Int,
        title: String,
        context: String,
        notes: [String],
        completedHours: Int,
        completedModules: [String],
        cohortSeats: Int,
        deviceCredits: Int,
        assessmentSlots: Int,
        practiceSeats: Int
    ) {
        self.entityID = entityID
        self.revision = revision
        self.title = title
        self.context = context
        self.notes = notes
        self.completedHours = completedHours
        self.completedModules = completedModules
        self.cohortSeats = cohortSeats
        self.deviceCredits = deviceCredits
        self.assessmentSlots = assessmentSlots
        self.practiceSeats = practiceSeats
    }
}

private enum TrainingPathway: String, CaseIterable {
    case guided
    case independent

    var label: String {
        switch self {
        case .guided: return "Guided cohort"
        case .independent: return "Independent lab"
        }
    }

    func isEligible(for input: TrainingPathwayInput) -> Bool {
        guard input.completedModules.contains("foundation") else { return false }
        switch self {
        case .guided:
            return input.completedHours >= 8 && input.cohortSeats >= 1
        case .independent:
            return input.completedHours >= 4 && input.deviceCredits >= 2
        }
    }
}

private enum TrainingParticipationMode: String, CaseIterable {
    case certificate
    case practice

    var label: String {
        switch self {
        case .certificate: return "Certificate assessment"
        case .practice: return "Practice only"
        }
    }

    func isEligible(for input: TrainingPathwayInput, pathway: TrainingPathway?) -> Bool {
        guard let pathway = pathway, pathway.isEligible(for: input) else { return false }
        switch self {
        case .certificate:
            return pathway == .guided && input.completedHours >= 12 && input.assessmentSlots >= 1
        case .practice:
            return input.practiceSeats >= 1
        }
    }
}

private struct TrainingEnrollmentState {
    let entityID: String
    let revision: Int
    var pathway: TrainingPathway?
    var mode: TrainingParticipationMode?
    var confirmed = false
    var recorded = false

    init(input: TrainingPathwayInput) {
        entityID = input.entityID
        revision = input.revision
    }

    /// Identity is reconciled first, followed by the parent and then its dependent choice.
    func reconciled(with input: TrainingPathwayInput) -> TrainingEnrollmentState {
        guard entityID == input.entityID && revision == input.revision else {
            return TrainingEnrollmentState(input: input)
        }
        var next = self
        if let pathway = next.pathway, !pathway.isEligible(for: input) {
            next.pathway = nil
            next.mode = nil
            next.confirmed = false
            next.recorded = false
        } else if let mode = next.mode, !mode.isEligible(for: input, pathway: next.pathway) {
            next.mode = nil
            next.confirmed = false
            next.recorded = false
        }
        return next
    }

    func hasValidChoices(for input: TrainingPathwayInput) -> Bool {
        guard let pathway = pathway, let mode = mode else { return false }
        return pathway.isEligible(for: input) && mode.isEligible(for: input, pathway: pathway)
    }

    func canRecord(for input: TrainingPathwayInput) -> Bool {
        return !recorded && confirmed && hasValidChoices(for: input)
    }

    func summary(for input: TrainingPathwayInput) -> String {
        return "Pathway: \(pathway?.label ?? "Not chosen"). Mode: \(mode?.label ?? "Not chosen"). \(input.completedHours) completed hours."
    }

    func status(for input: TrainingPathwayInput) -> String {
        if recorded { return "Recorded. Selections are locked for this request." }
        if !TrainingPathway.allCases.contains(where: { $0.isEligible(for: input) }) {
            return "No pathway is eligible for these request details."
        }
        guard let pathway = pathway else { return "Choose a pathway." }
        guard mode != nil else { return "Choose a participation mode for \(pathway.label)." }
        if !confirmed { return "Confirm the learning commitment to continue." }
        return "Ready to record training enrollment."
    }
}

private enum TrainingEnrollmentPalette {
    static let surface = Color(red: 247.0 / 255, green: 249.0 / 255, blue: 252.0 / 255)
    static let row = Color.white
    static let selected = Color(red: 229.0 / 255, green: 241.0 / 255, blue: 255.0 / 255)
    static let accent = Color(red: 36.0 / 255, green: 89.0 / 255, blue: 166.0 / 255)
    static let disabled = Color(red: 217.0 / 255, green: 225.0 / 255, blue: 236.0 / 255)
    static let ink = Color(red: 21.0 / 255, green: 36.0 / 255, blue: 59.0 / 255)
    static let muted = Color(red: 82.0 / 255, green: 97.0 / 255, blue: 116.0 / 255)
    static let outline = Color(red: 184.0 / 255, green: 197.0 / 255, blue: 214.0 / 255)
}

/// Preserves the authored colors when a native button is disabled or pressed.
@available(iOS 14, macOS 11, *)
private struct TrainingEnrollmentButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

/// An enrollment panel that expands naturally within a caller-owned vertical scroll view.
@available(iOS 14, macOS 11, *)
public struct TrainingPathwayEnrollment: View {
    private let input: TrainingPathwayInput
    private let onEvent: (String) -> Void
    @State private var state: TrainingEnrollmentState

    public init(input: TrainingPathwayInput, onEvent: @escaping (String) -> Void) {
        self.input = input
        self.onEvent = onEvent
        _state = State(initialValue: TrainingEnrollmentState(input: input))
    }

    public var body: some View {
        // Render the current caller input immediately, including before onChange commits it.
        let current = state.reconciled(with: input)
        return VStack(alignment: .leading, spacing: 12) {
            header
            caption("Pathway")
            ForEach(TrainingPathway.allCases, id: \.rawValue) { pathway in
                choice(
                    pathway.label,
                    selected: current.pathway == pathway,
                    enabled: !current.recorded && pathway.isEligible(for: input)
                ) { choose(pathway) }
            }
            caption("Mode")
            ForEach(TrainingParticipationMode.allCases, id: \.rawValue) { mode in
                choice(
                    mode.label,
                    selected: current.mode == mode,
                    enabled: !current.recorded && mode.isEligible(for: input, pathway: current.pathway)
                ) { choose(mode) }
            }
            text(current.summary(for: input), size: 16, weight: .semibold, muted: false)
                .accessibilityIdentifier("training-pathway.summary")
            choice(
                "I confirm the learning commitment",
                selected: current.confirmed,
                enabled: !current.recorded && current.hasValidChoices(for: input),
                action: toggleConfirmation
            )
            text(current.status(for: input))
                .accessibilityIdentifier("training-pathway.status")
            text(current.recorded ? "Training enrollment recorded." : "No request recorded.")
                .accessibilityIdentifier("training-pathway.receipt")
            primary(enabled: current.canRecord(for: input))
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(TrainingEnrollmentPalette.surface))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("training-pathway.surface")
        .onChange(of: input) { updatedInput in
            state = state.reconciled(with: updatedInput)
        }
    }

    private var header: some View {
        Group {
            text(input.title, size: 24, weight: .semibold, muted: false)
                .accessibilityIdentifier("training-pathway.title")
            text(input.context)
                .accessibilityIdentifier("training-pathway.context")
            text(input.notes.joined(separator: "\n\n"))
                .accessibilityIdentifier("training-pathway.notes")
        }
    }

    private func text(
        _ value: String,
        size: CGFloat = 15,
        weight: Font.Weight = .regular,
        muted: Bool = true
    ) -> some View {
        Text(verbatim: value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(muted ? TrainingEnrollmentPalette.muted : TrainingEnrollmentPalette.ink)
            .multilineTextAlignment(.leading)
            .lineLimit(nil)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityLabel(Text(verbatim: value))
    }

    private func caption(_ value: String) -> some View {
        text(value, size: 16, weight: .semibold, muted: false)
    }

    private func choice(
        _ label: String,
        selected: Bool,
        enabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(verbatim: label)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(enabled ? TrainingEnrollmentPalette.ink : TrainingEnrollmentPalette.muted)
                    .multilineTextAlignment(.leading)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if selected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(enabled ? TrainingEnrollmentPalette.accent : TrainingEnrollmentPalette.muted)
                        .accessibilityHidden(true)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .inset(by: selected ? 2 : 1)
                    .fill(selected ? TrainingEnrollmentPalette.selected : TrainingEnrollmentPalette.row)
            )
            .background(RoundedRectangle(cornerRadius: 8).fill(selected ? TrainingEnrollmentPalette.accent : TrainingEnrollmentPalette.outline))
            .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(TrainingEnrollmentButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(verbatim: label))
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func primary(enabled: Bool) -> some View {
        Button(action: record) {
            Text("Record training enrollment")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(enabled ? .white : TrainingEnrollmentPalette.muted)
                .multilineTextAlignment(.center)
                .lineLimit(nil)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(RoundedRectangle(cornerRadius: 8).fill(enabled ? TrainingEnrollmentPalette.accent : TrainingEnrollmentPalette.disabled))
                .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(TrainingEnrollmentButtonStyle())
        .disabled(!enabled)
    }

    private func choose(_ pathway: TrainingPathway) {
        var next = state.reconciled(with: input)
        guard !next.recorded, pathway.isEligible(for: input), next.pathway != pathway else { return }
        next.pathway = pathway
        next.mode = nil
        next.confirmed = false
        state = next
    }

    private func choose(_ mode: TrainingParticipationMode) {
        var next = state.reconciled(with: input)
        guard !next.recorded, mode.isEligible(for: input, pathway: next.pathway), next.mode != mode else { return }
        next.mode = mode
        next.confirmed = false
        state = next
    }

    private func toggleConfirmation() {
        var next = state.reconciled(with: input)
        guard !next.recorded, next.hasValidChoices(for: input) else { return }
        next.confirmed.toggle()
        state = next
    }

    private func record() {
        var next = state.reconciled(with: input)
        guard next.canRecord(for: input), let pathway = next.pathway, let mode = next.mode else { return }
        onEvent("training|\(input.entityID)|\(input.revision)|\(pathway.rawValue)|\(mode.rawValue)|\(input.completedHours)")
        next.recorded = true
        state = next
    }
}
