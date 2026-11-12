import SwiftUI

public struct SubscriptionCapacityInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let seatCount: Int
    public let teamQuota: Int
    public let scaleQuota: Int
    public let prepaidMonths: Int
    public let accountBalanceCents: Int

    public init(
        entityID: String,
        revision: Int,
        title: String,
        context: String,
        notes: [String],
        seatCount: Int,
        teamQuota: Int,
        scaleQuota: Int,
        prepaidMonths: Int,
        accountBalanceCents: Int
    ) {
        self.entityID = entityID
        self.revision = revision
        self.title = title
        self.context = context
        self.notes = notes
        self.seatCount = seatCount
        self.teamQuota = teamQuota
        self.scaleQuota = scaleQuota
        self.prepaidMonths = prepaidMonths
        self.accountBalanceCents = accountBalanceCents
    }
}

private enum SubscriptionCapacityPlan: String {
    case scale, team

    var label: String {
        switch self {
        case .scale: return "Scale plan"
        case .team: return "Team plan"
        }
    }
}

private enum SubscriptionCapacityTerm: String {
    case annual, monthly

    var label: String {
        switch self {
        case .annual: return "Annual billing"
        case .monthly: return "Monthly billing"
        }
    }
}

private extension SubscriptionCapacityInput {
    func permits(_ plan: SubscriptionCapacityPlan) -> Bool {
        switch plan {
        case .scale:
            return seatCount >= 10 && seatCount <= scaleQuota
        case .team:
            return seatCount >= 2 && seatCount <= 25 && seatCount <= teamQuota
        }
    }

    func permits(_ term: SubscriptionCapacityTerm, for plan: SubscriptionCapacityPlan) -> Bool {
        guard permits(plan) else { return false }
        switch term {
        case .annual: return plan == .scale && prepaidMonths >= 12
        case .monthly: return accountBalanceCents >= 0
        }
    }
}

private struct SubscriptionCapacityState {
    let entityID: String
    let revision: Int
    var plan: SubscriptionCapacityPlan?
    var term: SubscriptionCapacityTerm?
    var confirmed = false
    var recorded = false

    init(input: SubscriptionCapacityInput) {
        entityID = input.entityID
        revision = input.revision
    }

    func reconciled(with input: SubscriptionCapacityInput) -> SubscriptionCapacityState {
        guard entityID == input.entityID, revision == input.revision else {
            return SubscriptionCapacityState(input: input)
        }
        guard let plan = plan else { return self }
        guard input.permits(plan) else { return SubscriptionCapacityState(input: input) }
        var result = self
        if let term = term, !input.permits(term, for: plan) {
            result.term = nil
            result.confirmed = false
            result.recorded = false
        }
        return result
    }

    func hasValidSelection(for input: SubscriptionCapacityInput) -> Bool {
        guard let plan = plan, let term = term else { return false }
        return input.permits(plan) && input.permits(term, for: plan)
    }
}

private enum SubscriptionCapacityColors {
    static let surface = Color(.sRGB, red: 247 / 255, green: 249 / 255, blue: 252 / 255, opacity: 1)
    static let row = Color(.sRGB, red: 1, green: 1, blue: 1, opacity: 1)
    static let selected = Color(.sRGB, red: 229 / 255, green: 241 / 255, blue: 1, opacity: 1)
    static let accent = Color(.sRGB, red: 36 / 255, green: 89 / 255, blue: 166 / 255, opacity: 1)
    static let disabled = Color(.sRGB, red: 217 / 255, green: 225 / 255, blue: 236 / 255, opacity: 1)
    static let ink = Color(.sRGB, red: 21 / 255, green: 36 / 255, blue: 59 / 255, opacity: 1)
    static let muted = Color(.sRGB, red: 82 / 255, green: 97 / 255, blue: 116 / 255, opacity: 1)
    static let outline = Color(.sRGB, red: 184 / 255, green: 197 / 255, blue: 214 / 255, opacity: 1)
}

private struct SubscriptionCapacityButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

@available(iOS 14, macOS 11, *)
public struct SubscriptionCapacityChange: View {
    private let input: SubscriptionCapacityInput
    private let onEvent: (String) -> Void
    @State private var state: SubscriptionCapacityState

    public init(input: SubscriptionCapacityInput, onEvent: @escaping (String) -> Void) {
        self.input = input
        self.onEvent = onEvent
        _state = State(initialValue: SubscriptionCapacityState(input: input))
    }

    private var current: SubscriptionCapacityState { state.reconciled(with: input) }

    public var body: some View {
        let selection = current
        let valid = selection.hasValidSelection(for: input)
        return VStack(alignment: .leading, spacing: 12) {
            label(input.title, size: 24, weight: .semibold, color: SubscriptionCapacityColors.ink,
                  identifier: "subscription-capacity.title")
            label(input.context, identifier: "subscription-capacity.context")
            label(input.notes.joined(separator: "\n\n"), identifier: "subscription-capacity.notes")

            VStack(alignment: .leading, spacing: 12) {
                caption("Plan")
                planButton(.scale, selection: selection)
                planButton(.team, selection: selection)
            }
            VStack(alignment: .leading, spacing: 12) {
                caption("Term")
                termButton(.annual, selection: selection)
                termButton(.monthly, selection: selection)
            }

            label("Plan: \(selection.plan?.label ?? "Not chosen"). Term: \(selection.term?.label ?? "Not chosen"). \(input.seatCount) seats.",
                  size: 16, weight: .semibold, color: SubscriptionCapacityColors.ink,
                  identifier: "subscription-capacity.summary")
            choiceButton("I confirm the capacity commitment", selected: selection.confirmed,
                         enabled: valid && !selection.recorded, action: toggleConfirmation)
            label(status(for: selection), identifier: "subscription-capacity.status")
            label(selection.recorded ? "Capacity change recorded." : "No request recorded.",
                  identifier: "subscription-capacity.receipt")
            primaryButton(enabled: valid && selection.confirmed && !selection.recorded)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .fixedSize(horizontal: false, vertical: true)
        .background(RoundedRectangle(cornerRadius: 12).fill(SubscriptionCapacityColors.surface))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("subscription-capacity.surface")
        .onChange(of: input) { replacement in
            state = state.reconciled(with: replacement)
        }
    }

    private func label(
        _ text: String,
        size: CGFloat = 15,
        weight: Font.Weight = .regular,
        color: Color = SubscriptionCapacityColors.muted,
        identifier: String
    ) -> some View {
        Text(text)
            .font(.system(size: size, weight: weight, design: .default))
            .foregroundColor(color)
            .multilineTextAlignment(.leading)
            .lineLimit(nil)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityLabel(Text(text))
            .accessibilityIdentifier(identifier)
    }

    private func caption(_ text: String) -> some View {
        Text(text)
            .font(.system(size: 16, weight: .semibold, design: .default))
            .foregroundColor(SubscriptionCapacityColors.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func planButton(_ plan: SubscriptionCapacityPlan, selection: SubscriptionCapacityState) -> some View {
        choiceButton(plan.label, selected: selection.plan == plan,
                     enabled: !selection.recorded && input.permits(plan)) { choose(plan) }
    }

    private func termButton(_ term: SubscriptionCapacityTerm, selection: SubscriptionCapacityState) -> some View {
        let enabled = !selection.recorded && selection.plan.map { input.permits(term, for: $0) } == true
        return choiceButton(term.label, selected: selection.term == term, enabled: enabled) { choose(term) }
    }

    private func choiceButton(
        _ title: String,
        selected: Bool,
        enabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(title)
                    .font(.system(size: 15, weight: .regular, design: .default))
                    .foregroundColor(enabled ? SubscriptionCapacityColors.ink : SubscriptionCapacityColors.muted)
                    .multilineTextAlignment(.leading)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if selected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 16, weight: .regular))
                        .foregroundColor(enabled ? SubscriptionCapacityColors.accent : SubscriptionCapacityColors.muted)
                        .frame(width: 16, height: 16)
                        .accessibilityHidden(true)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .background(
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(selected ? SubscriptionCapacityColors.selected : SubscriptionCapacityColors.row)
                    RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(selected ? SubscriptionCapacityColors.accent : SubscriptionCapacityColors.outline,
                                      lineWidth: selected ? 2 : 1)
                }
            )
            .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(SubscriptionCapacityButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(title))
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func primaryButton(enabled: Bool) -> some View {
        Button(action: record) {
            Text("Record capacity change")
                .font(.system(size: 16, weight: .semibold, design: .default))
                .foregroundColor(enabled ? SubscriptionCapacityColors.row : SubscriptionCapacityColors.muted)
                .multilineTextAlignment(.center)
                .lineLimit(nil)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(RoundedRectangle(cornerRadius: 8)
                    .fill(enabled ? SubscriptionCapacityColors.accent : SubscriptionCapacityColors.disabled))
                .contentShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(SubscriptionCapacityButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text("Record capacity change"))
    }

    private func status(for selection: SubscriptionCapacityState) -> String {
        if selection.recorded { return "Recorded. Selections are locked for this request." }
        if !input.permits(.scale) && !input.permits(.team) {
            return "No plan is eligible for these request details."
        }
        guard let plan = selection.plan else { return "Choose a plan." }
        if selection.term == nil { return "Choose a billing term for \(plan.label)." }
        if !selection.confirmed { return "Confirm the capacity commitment to continue." }
        return "Ready to record capacity change."
    }

    private func choose(_ plan: SubscriptionCapacityPlan) {
        var next = current
        guard !next.recorded, input.permits(plan), next.plan != plan else { return }
        next.plan = plan
        next.term = nil
        next.confirmed = false
        state = next
    }

    private func choose(_ term: SubscriptionCapacityTerm) {
        var next = current
        guard !next.recorded, let plan = next.plan, input.permits(term, for: plan), next.term != term else { return }
        next.term = term
        next.confirmed = false
        state = next
    }

    private func toggleConfirmation() {
        var next = current
        guard !next.recorded, next.hasValidSelection(for: input) else { return }
        next.confirmed.toggle()
        state = next
    }

    private func record() {
        var next = current
        guard !next.recorded, next.confirmed, next.hasValidSelection(for: input),
              let plan = next.plan, let term = next.term else { return }
        onEvent("capacity|\(input.entityID)|\(input.revision)|\(plan.rawValue)|\(term.rawValue)|\(input.seatCount)")
        next.recorded = true
        state = next
    }
}
