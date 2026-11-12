import SwiftUI

public struct VisitorAccessInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let guestCount: Int
    public let sponsorActive: Bool
    public let badgeTrainingComplete: Bool
    public let researchCapacity: Int
    public let officeCapacity: Int
    public let verifiedIDs: Int
    public let labInductions: Int
    public let escortCount: Int

    public init(
        entityID: String,
        revision: Int,
        title: String,
        context: String,
        notes: [String],
        guestCount: Int,
        sponsorActive: Bool,
        badgeTrainingComplete: Bool,
        researchCapacity: Int,
        officeCapacity: Int,
        verifiedIDs: Int,
        labInductions: Int,
        escortCount: Int
    ) {
        self.entityID = entityID
        self.revision = revision
        self.title = title
        self.context = context
        self.notes = notes
        self.guestCount = guestCount
        self.sponsorActive = sponsorActive
        self.badgeTrainingComplete = badgeTrainingComplete
        self.researchCapacity = researchCapacity
        self.officeCapacity = officeCapacity
        self.verifiedIDs = verifiedIDs
        self.labInductions = labInductions
        self.escortCount = escortCount
    }
}

private enum VisitorAccessArea: String, CaseIterable, Hashable {
    case research
    case office

    var label: String {
        switch self {
        case .research: return "Research floor"
        case .office: return "Office floor"
        }
    }

    func isEligible(for input: VisitorAccessInput) -> Bool {
        guard input.sponsorActive, input.guestCount > 0 else { return false }
        switch self {
        case .research:
            return input.badgeTrainingComplete && input.guestCount <= input.researchCapacity
        case .office:
            return input.guestCount <= input.officeCapacity
        }
    }
}

private enum VisitorAccessCredential: String, CaseIterable, Hashable {
    case researchBadge = "research-badge"
    case visitorEscort = "visitor-escort"

    var label: String {
        switch self {
        case .researchBadge: return "Research badge"
        case .visitorEscort: return "Visitor escort"
        }
    }

    func isEligible(in area: VisitorAccessArea?, for input: VisitorAccessInput) -> Bool {
        guard let area = area, area.isEligible(for: input) else { return false }
        switch self {
        case .researchBadge:
            return area == .research
                && input.verifiedIDs >= input.guestCount
                && input.labInductions >= input.guestCount
        case .visitorEscort:
            return input.escortCount >= input.guestCount
        }
    }
}

private struct VisitorAccessSelection: Equatable {
    let entityID: String
    let revision: Int
    var area: VisitorAccessArea?
    var credential: VisitorAccessCredential?
    var confirmed = false
    var recorded = false

    init(input: VisitorAccessInput) {
        entityID = input.entityID
        revision = input.revision
        area = nil
        credential = nil
    }

    func reconciled(with input: VisitorAccessInput) -> VisitorAccessSelection {
        guard entityID == input.entityID, revision == input.revision else {
            return VisitorAccessSelection(input: input)
        }
        var next = self
        if let area = area, !area.isEligible(for: input) {
            next.area = nil
            next.credential = nil
            next.confirmed = false
            next.recorded = false
        } else if let credential = credential,
                  !credential.isEligible(in: area, for: input) {
            next.credential = nil
            next.confirmed = false
            next.recorded = false
        }
        return next
    }

    func hasValidChoices(for input: VisitorAccessInput) -> Bool {
        guard let area = area, let credential = credential else { return false }
        return area.isEligible(for: input) && credential.isEligible(in: area, for: input)
    }

    func canRecord(for input: VisitorAccessInput) -> Bool {
        !recorded && confirmed && hasValidChoices(for: input)
    }

    func summary(for input: VisitorAccessInput) -> String {
        "Area: \(area?.label ?? "Not chosen"). Credential: \(credential?.label ?? "Not chosen"). \(input.guestCount) visitors."
    }

    func status(for input: VisitorAccessInput) -> String {
        if recorded { return "Recorded. Selections are locked for this request." }
        if !VisitorAccessArea.allCases.contains(where: { $0.isEligible(for: input) }) {
            return "No access area is eligible for these request details."
        }
        guard let area = area else { return "Choose a access area." }
        guard credential != nil else { return "Choose a credential route for \(area.label)." }
        guard confirmed else { return "Confirm the visitor briefing to continue." }
        return "Ready to record visitor clearance."
    }
}

@available(iOS 14, macOS 11, *)
private enum VisitorAccessColors {
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
private struct VisitorAccessButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

@available(iOS 14, macOS 11, *)
public struct VisitorAccessPreclearance: View {
    private let input: VisitorAccessInput
    private let onEvent: (String) -> Void
    @State private var selection: VisitorAccessSelection

    public init(input: VisitorAccessInput, onEvent: @escaping (String) -> Void) {
        self.input = input
        self.onEvent = onEvent
        _selection = State(initialValue: VisitorAccessSelection(input: input))
    }

    public var body: some View {
        // Render reconciled state immediately; onChange retains it for later updates.
        let current = selection.reconciled(with: input)
        return VStack(alignment: .leading, spacing: 12) {
            contentText(input.title, size: 24, weight: .semibold, color: VisitorAccessColors.ink,
                        identifier: "visitor-preclearance.title")
            contentText(input.context, identifier: "visitor-preclearance.context")
            contentText(input.notes.joined(separator: "\n\n"), identifier: "visitor-preclearance.notes")

            VStack(alignment: .leading, spacing: 12) {
                sectionText("Area")
                ForEach(VisitorAccessArea.allCases, id: \.self) { area in
                    choiceButton(area.label, selected: current.area == area,
                                 enabled: !current.recorded && area.isEligible(for: input)) {
                        choose(area)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                sectionText("Credential")
                ForEach(VisitorAccessCredential.allCases, id: \.self) { credential in
                    choiceButton(credential.label, selected: current.credential == credential,
                                 enabled: !current.recorded && credential.isEligible(in: current.area, for: input)) {
                        choose(credential)
                    }
                }
            }

            contentText(current.summary(for: input), size: 16, weight: .semibold,
                        color: VisitorAccessColors.ink, identifier: "visitor-preclearance.summary")
            choiceButton("I confirm the visitor briefing", selected: current.confirmed,
                         enabled: !current.recorded && current.hasValidChoices(for: input)) {
                toggleConfirmation()
            }
            contentText(current.status(for: input), identifier: "visitor-preclearance.status")
            contentText(current.recorded ? "Visitor clearance recorded." : "No request recorded.",
                        identifier: "visitor-preclearance.receipt")
            primaryButton(enabled: current.canRecord(for: input))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 12).fill(VisitorAccessColors.surface))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("visitor-preclearance.surface")
        .onChange(of: input) { replacement in
            selection = selection.reconciled(with: replacement)
        }
    }

    private func contentText(
        _ value: String,
        size: CGFloat = 15,
        weight: Font.Weight = .regular,
        color: Color = VisitorAccessColors.muted,
        identifier: String
    ) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color)
            .lineLimit(nil)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier(identifier)
    }

    private func sectionText(_ value: String) -> some View {
        Text(value)
            .font(.system(size: 16, weight: .semibold))
            .foregroundColor(VisitorAccessColors.ink)
            .lineLimit(nil)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func choiceButton(
        _ label: String,
        selected: Bool,
        enabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(label)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(enabled ? VisitorAccessColors.ink : VisitorAccessColors.muted)
                    .lineLimit(nil)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if selected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(enabled ? VisitorAccessColors.accent : VisitorAccessColors.muted)
                        .accessibilityHidden(true)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .strokeBorder(selected ? VisitorAccessColors.accent : VisitorAccessColors.outline,
                                  lineWidth: selected ? 2 : 1)
                    .background(RoundedRectangle(cornerRadius: 8)
                        .fill(selected ? VisitorAccessColors.selected : VisitorAccessColors.row))
            )
            .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(VisitorAccessButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(label))
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func primaryButton(enabled: Bool) -> some View {
        Button(action: record) {
            Text("Record visitor clearance")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(enabled ? VisitorAccessColors.row : VisitorAccessColors.muted)
                .lineLimit(nil)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(RoundedRectangle(cornerRadius: 8)
                    .fill(enabled ? VisitorAccessColors.accent : VisitorAccessColors.disabled))
                .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(VisitorAccessButtonStyle())
        .disabled(!enabled)
    }

    private func choose(_ area: VisitorAccessArea) {
        var next = selection.reconciled(with: input)
        guard !next.recorded, area.isEligible(for: input), next.area != area else { return }
        next.area = area
        next.credential = nil
        next.confirmed = false
        selection = next
    }

    private func choose(_ credential: VisitorAccessCredential) {
        var next = selection.reconciled(with: input)
        guard !next.recorded, credential.isEligible(in: next.area, for: input),
              next.credential != credential else { return }
        next.credential = credential
        next.confirmed = false
        selection = next
    }

    private func toggleConfirmation() {
        var next = selection.reconciled(with: input)
        guard !next.recorded, next.hasValidChoices(for: input) else { return }
        next.confirmed.toggle()
        selection = next
    }

    private func record() {
        var next = selection.reconciled(with: input)
        guard next.canRecord(for: input), let area = next.area, let credential = next.credential else { return }
        onEvent("visitor|\(input.entityID)|\(input.revision)|\(area.rawValue)|\(credential.rawValue)|\(input.guestCount)")
        next.recorded = true
        selection = next
    }
}
