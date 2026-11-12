import SwiftUI

public struct CandidateDispositionInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let portfolioScore: Int
    public let reviewerCapacity: Int
    public let technicalSlots: Int
    public let recruiterSlots: Int
    public let legalHold: Bool
    public let assessmentCount: Int
    public let openRoleCount: Int

    public init(
        entityID: String,
        revision: Int,
        title: String,
        context: String,
        notes: [String],
        portfolioScore: Int,
        reviewerCapacity: Int,
        technicalSlots: Int,
        recruiterSlots: Int,
        legalHold: Bool,
        assessmentCount: Int,
        openRoleCount: Int
    ) {
        self.entityID = entityID
        self.revision = revision
        self.title = title
        self.context = context
        self.notes = notes
        self.portfolioScore = portfolioScore
        self.reviewerCapacity = reviewerCapacity
        self.technicalSlots = technicalSlots
        self.recruiterSlots = recruiterSlots
        self.legalHold = legalHold
        self.assessmentCount = assessmentCount
        self.openRoleCount = openRoleCount
    }
}

private enum CandidateDispositionRoot: String, CaseIterable {
    case continueReview = "continue"
    case archive = "archive"

    var label: String {
        switch self {
        case .continueReview: return "Continue review"
        case .archive: return "Archive application"
        }
    }

    func isEligible(for input: CandidateDispositionInput) -> Bool {
        switch self {
        case .continueReview:
            return input.portfolioScore >= 60 && input.reviewerCapacity >= 1
        case .archive:
            return !input.legalHold
        }
    }
}

private enum CandidateDispositionDetail: String, CaseIterable {
    case technical = "technical"
    case recruiter = "recruiter"
    case skillsGap = "skills-gap"
    case roleClosed = "role-closed"

    var label: String {
        switch self {
        case .technical: return "Technical interview"
        case .recruiter: return "Recruiter screen"
        case .skillsGap: return "Skills gap"
        case .roleClosed: return "Role closed"
        }
    }

    func isEligible(root: CandidateDispositionRoot?, input: CandidateDispositionInput) -> Bool {
        guard let root = root, root.isEligible(for: input) else { return false }
        switch self {
        case .technical:
            return root == .continueReview && input.portfolioScore >= 75 && input.technicalSlots >= 1
        case .recruiter:
            return root == .continueReview && input.recruiterSlots >= 1
        case .skillsGap:
            return root == .archive && input.assessmentCount >= 1
        case .roleClosed:
            return root == .archive && input.openRoleCount == 0
        }
    }
}

private struct CandidateDispositionState: Equatable {
    let entityID: String
    let revision: Int
    var root: CandidateDispositionRoot?
    var detail: CandidateDispositionDetail?
    var confirmed = false
    var recorded = false

    init(input: CandidateDispositionInput) {
        entityID = input.entityID
        revision = input.revision
    }

    func reconciled(with input: CandidateDispositionInput) -> CandidateDispositionState {
        guard entityID == input.entityID, revision == input.revision else {
            return CandidateDispositionState(input: input)
        }
        var next = self
        if let root = root, !root.isEligible(for: input) {
            next.root = nil
            next.detail = nil
            next.confirmed = false
            next.recorded = false
        } else if let detail = detail, !detail.isEligible(root: root, input: input) {
            next.detail = nil
            next.confirmed = false
            next.recorded = false
        }
        return next
    }

    func hasValidSelection(for input: CandidateDispositionInput) -> Bool {
        guard let root = root, let detail = detail else { return false }
        return root.isEligible(for: input) && detail.isEligible(root: root, input: input)
    }

    func canRecord(for input: CandidateDispositionInput) -> Bool {
        return !recorded && confirmed && hasValidSelection(for: input)
    }

    func summary(for input: CandidateDispositionInput) -> String {
        return "Disposition: \(root?.label ?? "Not chosen"). Detail: \(detail?.label ?? "Not chosen"). \(input.portfolioScore) portfolio points."
    }

    func status(for input: CandidateDispositionInput) -> String {
        if recorded { return "Recorded. Selections are locked for this request." }
        if !CandidateDispositionRoot.allCases.contains(where: { $0.isEligible(for: input) }) {
            return "No disposition is eligible for these request details."
        }
        guard let root = root else { return "Choose a disposition." }
        guard detail != nil else { return "Choose a next step or reason for \(root.label)." }
        if !confirmed { return "Confirm the evidence review to continue." }
        return "Ready to record candidate disposition."
    }
}

private enum CandidateDispositionColors {
    static let surface = Color(.sRGB, red: 247.0 / 255, green: 249.0 / 255, blue: 252.0 / 255, opacity: 1)
    static let row = Color(.sRGB, red: 1, green: 1, blue: 1, opacity: 1)
    static let selected = Color(.sRGB, red: 229.0 / 255, green: 241.0 / 255, blue: 1, opacity: 1)
    static let accent = Color(.sRGB, red: 36.0 / 255, green: 89.0 / 255, blue: 166.0 / 255, opacity: 1)
    static let disabled = Color(.sRGB, red: 217.0 / 255, green: 225.0 / 255, blue: 236.0 / 255, opacity: 1)
    static let ink = Color(.sRGB, red: 21.0 / 255, green: 36.0 / 255, blue: 59.0 / 255, opacity: 1)
    static let muted = Color(.sRGB, red: 82.0 / 255, green: 97.0 / 255, blue: 116.0 / 255, opacity: 1)
    static let outline = Color(.sRGB, red: 184.0 / 255, green: 197.0 / 255, blue: 214.0 / 255, opacity: 1)
}

@available(iOS 14, macOS 11, *)
public struct CandidateDispositionReview: View {
    private let input: CandidateDispositionInput
    private let onEvent: (String) -> Void
    @State private var state: CandidateDispositionState

    public init(input: CandidateDispositionInput, onEvent: @escaping (String) -> Void) {
        self.input = input
        self.onEvent = onEvent
        _state = State(initialValue: CandidateDispositionState(input: input))
    }

    public var body: some View {
        let current = state.reconciled(with: input)
        return VStack(alignment: .leading, spacing: 12) {
            contentText(input.title, size: 24, weight: .semibold, color: CandidateDispositionColors.ink)
                .accessibilityIdentifier("candidate-disposition.title")
            contentText(input.context, color: CandidateDispositionColors.muted)
                .accessibilityIdentifier("candidate-disposition.context")
            contentText(input.notes.joined(separator: "\n\n"), color: CandidateDispositionColors.muted)
                .accessibilityIdentifier("candidate-disposition.notes")
            rootSection(current)
            detailSection(current)
            contentText(current.summary(for: input), size: 16, weight: .semibold, color: CandidateDispositionColors.ink)
                .accessibilityIdentifier("candidate-disposition.summary")
            choiceButton(
                "I confirm the evidence review",
                selected: current.confirmed,
                enabled: !current.recorded && current.hasValidSelection(for: input),
                action: toggleConfirmation
            )
            VStack(alignment: .leading, spacing: 12) {
                contentText(current.status(for: input), color: CandidateDispositionColors.muted)
                    .accessibilityIdentifier("candidate-disposition.status")
                contentText(current.recorded ? "Candidate disposition recorded." : "No request recorded.", color: CandidateDispositionColors.muted)
                    .accessibilityIdentifier("candidate-disposition.receipt")
            }
            primaryButton(enabled: current.canRecord(for: input))
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(CandidateDispositionColors.surface))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("candidate-disposition.surface")
        .onChange(of: input) { replacement in
            state = state.reconciled(with: replacement)
        }
    }

    private func rootSection(_ current: CandidateDispositionState) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            contentText("Disposition", size: 16, weight: .semibold, color: CandidateDispositionColors.ink)
            ForEach(CandidateDispositionRoot.allCases, id: \.self) { root in
                choiceButton(root.label, selected: current.root == root, enabled: !current.recorded && root.isEligible(for: input)) {
                    choose(root)
                }
            }
        }
    }

    private func detailSection(_ current: CandidateDispositionState) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            contentText("Detail", size: 16, weight: .semibold, color: CandidateDispositionColors.ink)
            ForEach(CandidateDispositionDetail.allCases, id: \.self) { detail in
                choiceButton(detail.label, selected: current.detail == detail, enabled: !current.recorded && detail.isEligible(root: current.root, input: input)) {
                    choose(detail)
                }
            }
        }
    }

    private func contentText(_ value: String, size: CGFloat = 15, weight: Font.Weight = .regular, color: Color) -> some View {
        Text(verbatim: value)
            .font(.system(size: size, weight: weight, design: .default))
            .foregroundColor(color)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func choiceButton(_ label: String, selected: Bool, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(verbatim: label)
                    .font(.system(size: 15, weight: .regular, design: .default))
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 0)
                if selected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(enabled ? CandidateDispositionColors.accent : CandidateDispositionColors.muted)
                        .accessibilityHidden(true)
                }
            }
            .foregroundColor(enabled ? CandidateDispositionColors.ink : CandidateDispositionColors.muted)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .background(
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(selected ? CandidateDispositionColors.selected : CandidateDispositionColors.row)
                    RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(selected ? CandidateDispositionColors.accent : CandidateDispositionColors.outline, lineWidth: selected ? 2 : 1)
                }
            )
            .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(verbatim: label))
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func primaryButton(enabled: Bool) -> some View {
        Button(action: record) {
            Text(verbatim: "Record candidate disposition")
                .font(.system(size: 16, weight: .semibold, design: .default))
                .foregroundColor(enabled ? CandidateDispositionColors.row : CandidateDispositionColors.muted)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(RoundedRectangle(cornerRadius: 8).fill(enabled ? CandidateDispositionColors.accent : CandidateDispositionColors.disabled))
                .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
    }

    private func choose(_ root: CandidateDispositionRoot) {
        var next = state.reconciled(with: input)
        guard !next.recorded, root.isEligible(for: input) else { return }
        if next.root != root {
            next.root = root
            next.detail = nil
            next.confirmed = false
        }
        state = next
    }

    private func choose(_ detail: CandidateDispositionDetail) {
        var next = state.reconciled(with: input)
        guard !next.recorded, detail.isEligible(root: next.root, input: input) else { return }
        if next.detail != detail {
            next.detail = detail
            next.confirmed = false
        }
        state = next
    }

    private func toggleConfirmation() {
        var next = state.reconciled(with: input)
        guard !next.recorded, next.hasValidSelection(for: input) else { return }
        next.confirmed.toggle()
        state = next
    }

    private func record() {
        var next = state.reconciled(with: input)
        guard next.canRecord(for: input), let root = next.root, let detail = next.detail else { return }
        onEvent("candidate|\(input.entityID)|\(input.revision)|\(root.rawValue)|\(detail.rawValue)|\(input.portfolioScore)")
        next.recorded = true
        state = next
    }
}
