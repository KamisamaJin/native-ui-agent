import SwiftUI

public struct CateringPackageInput: Equatable {
    public let entityID: String
    public let revision: Int
    public let title: String
    public let context: String
    public let notes: [String]
    public let guestCount: Int
    public let vegetarianGuests: Int
    public let vegetarianMeals: Int
    public let buffetCapacity: Int
    public let boxedCapacity: Int
    public let reusableSets: Int
    public let compostableSets: Int

    public init(
        entityID: String,
        revision: Int,
        title: String,
        context: String,
        notes: [String],
        guestCount: Int,
        vegetarianGuests: Int,
        vegetarianMeals: Int,
        buffetCapacity: Int,
        boxedCapacity: Int,
        reusableSets: Int,
        compostableSets: Int
    ) {
        self.entityID = entityID
        self.revision = revision
        self.title = title
        self.context = context
        self.notes = notes
        self.guestCount = guestCount
        self.vegetarianGuests = vegetarianGuests
        self.vegetarianMeals = vegetarianMeals
        self.buffetCapacity = buffetCapacity
        self.boxedCapacity = boxedCapacity
        self.reusableSets = reusableSets
        self.compostableSets = compostableSets
    }
}

@available(iOS 14, macOS 11, *)
public struct CateringPackagePlanner: View {
    private let input: CateringPackageInput
    private let onEvent: (String) -> Void
    @State private var state: CateringPackageState

    public init(input: CateringPackageInput, onEvent: @escaping (String) -> Void) {
        self.input = input
        self.onEvent = onEvent
        _state = State(initialValue: CateringPackageState(input: input))
    }

    public var body: some View {
        // Present the reconciled value immediately, including the render on which
        // the caller changes its input. onChange also commits invalidations.
        let current = state.reconciled(with: input)
        return VStack(alignment: .leading, spacing: 12) {
            VStack(alignment: .leading, spacing: 12) {
                Text(verbatim: input.title)
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(CateringPackageColors.ink)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityIdentifier("catering-package.title")
                secondaryText(input.context, identifier: "catering-package.context")
                secondaryText(input.notes.joined(separator: "\n\n"), identifier: "catering-package.notes")
            }

            VStack(alignment: .leading, spacing: 12) {
                sectionCaption("Package")
                ForEach(CateringPackageChoice.allCases, id: \.self) { choice in
                    choiceButton(
                        choice.label,
                        selected: current.root == choice,
                        enabled: !current.recorded && choice.isEligible(for: input)
                    ) {
                        selectPackage(choice)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                sectionCaption("Service")
                ForEach(CateringServiceChoice.allCases, id: \.self) { choice in
                    choiceButton(
                        choice.label,
                        selected: current.detail == choice,
                        enabled: !current.recorded && choice.isEligible(for: input, root: current.root)
                    ) {
                        selectService(choice)
                    }
                }
            }

            Text(verbatim: current.summary(for: input))
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(CateringPackageColors.ink)
                .lineLimit(nil)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityIdentifier("catering-package.summary")

            choiceButton(
                "I confirm the dietary counts",
                selected: current.confirmed,
                enabled: current.canConfirm(for: input),
                action: toggleConfirmation
            )

            secondaryText(current.status(for: input), identifier: "catering-package.status")
            secondaryText(
                current.recorded ? "Catering order recorded." : "No request recorded.",
                identifier: "catering-package.receipt"
            )
            recordButton(enabled: current.canRecord(for: input))
        }
        .multilineTextAlignment(.leading)
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(CateringPackageColors.surface))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("catering-package.surface")
        .onChange(of: input) { newInput in
            state = state.reconciled(with: newInput)
        }
    }

    private func sectionCaption(_ label: String) -> some View {
        Text(verbatim: label)
            .font(.system(size: 16, weight: .semibold))
            .foregroundColor(CateringPackageColors.ink)
            .lineLimit(nil)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func secondaryText(_ value: String, identifier: String) -> some View {
        Text(verbatim: value)
            .font(.system(size: 15, weight: .regular))
            .foregroundColor(CateringPackageColors.muted)
            .lineLimit(nil)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier(identifier)
    }

    private func choiceButton(
        _ label: String,
        selected: Bool,
        enabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(verbatim: label)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundColor(enabled ? CateringPackageColors.ink : CateringPackageColors.muted)
                    .lineLimit(nil)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if selected {
                    Text(verbatim: "✓")
                        .font(.system(size: 16, weight: .regular))
                        .foregroundColor(enabled ? CateringPackageColors.accent : CateringPackageColors.muted)
                        .accessibilityHidden(true)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .strokeBorder(
                        selected ? CateringPackageColors.accent : CateringPackageColors.outline,
                        lineWidth: selected ? 2 : 1
                    )
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(selected ? CateringPackageColors.selected : CateringPackageColors.row)
                    )
            )
        }
        .buttonStyle(CateringPackageButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(verbatim: label))
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func recordButton(enabled: Bool) -> some View {
        Button(action: recordOrder) {
            Text(verbatim: "Record catering order")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(enabled ? CateringPackageColors.onAccent : CateringPackageColors.muted)
                .lineLimit(nil)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(enabled ? CateringPackageColors.accent : CateringPackageColors.disabled)
                )
        }
        .buttonStyle(CateringPackageButtonStyle())
        .disabled(!enabled)
    }

    private func selectPackage(_ choice: CateringPackageChoice) {
        var next = state.reconciled(with: input)
        guard !next.recorded, choice.isEligible(for: input) else { return }
        if next.root != choice {
            next.root = choice
            next.detail = nil
            next.confirmed = false
        }
        state = next
    }

    private func selectService(_ choice: CateringServiceChoice) {
        var next = state.reconciled(with: input)
        guard !next.recorded, choice.isEligible(for: input, root: next.root) else { return }
        if next.detail != choice {
            next.detail = choice
            next.confirmed = false
        }
        state = next
    }

    private func toggleConfirmation() {
        var next = state.reconciled(with: input)
        guard next.canConfirm(for: input) else { return }
        next.confirmed.toggle()
        state = next
    }

    private func recordOrder() {
        var next = state.reconciled(with: input)
        guard next.canRecord(for: input), let root = next.root, let detail = next.detail else { return }
        onEvent("catering|\(input.entityID)|\(input.revision)|\(root.rawValue)|\(detail.rawValue)|\(input.guestCount)")
        next.recorded = true
        state = next
    }
}

private enum CateringPackageChoice: String, CaseIterable {
    case buffet
    case boxed

    var label: String {
        switch self {
        case .buffet: return "Buffet package"
        case .boxed: return "Boxed package"
        }
    }

    func isEligible(for input: CateringPackageInput) -> Bool {
        switch self {
        case .buffet:
            return input.guestCount >= 6 && input.guestCount <= input.buffetCapacity
        case .boxed:
            return input.guestCount <= input.boxedCapacity && input.vegetarianMeals >= input.vegetarianGuests
        }
    }
}

private enum CateringServiceChoice: String, CaseIterable {
    case reusable
    case compostable

    var label: String {
        switch self {
        case .reusable: return "Reusable service"
        case .compostable: return "Compostable service"
        }
    }

    func isEligible(for input: CateringPackageInput, root: CateringPackageChoice?) -> Bool {
        guard let root = root, root.isEligible(for: input) else { return false }
        switch self {
        case .reusable:
            return root == .buffet && input.reusableSets >= input.guestCount
        case .compostable:
            return input.compostableSets >= input.guestCount
        }
    }
}

private struct CateringPackageState: Equatable {
    let entityID: String
    let revision: Int
    var root: CateringPackageChoice? = nil
    var detail: CateringServiceChoice? = nil
    var confirmed = false
    var recorded = false

    init(input: CateringPackageInput) {
        entityID = input.entityID
        revision = input.revision
    }

    func reconciled(with input: CateringPackageInput) -> CateringPackageState {
        guard entityID == input.entityID, revision == input.revision else {
            return CateringPackageState(input: input)
        }
        var result = self
        guard let root = root, root.isEligible(for: input) else {
            return CateringPackageState(input: input)
        }
        if let detail = detail, !detail.isEligible(for: input, root: root) {
            result.detail = nil
            result.confirmed = false
            result.recorded = false
        }
        return result
    }

    func canConfirm(for input: CateringPackageInput) -> Bool {
        guard !recorded, let root = root, let detail = detail else { return false }
        return root.isEligible(for: input) && detail.isEligible(for: input, root: root)
    }

    func canRecord(for input: CateringPackageInput) -> Bool {
        confirmed && canConfirm(for: input)
    }

    func summary(for input: CateringPackageInput) -> String {
        "Package: \(root?.label ?? "Not chosen"). Service: \(detail?.label ?? "Not chosen"). \(input.guestCount) guests."
    }

    func status(for input: CateringPackageInput) -> String {
        if recorded { return "Recorded. Selections are locked for this request." }
        if !CateringPackageChoice.allCases.contains(where: { $0.isEligible(for: input) }) {
            return "No package is eligible for these request details."
        }
        guard let root = root else { return "Choose a package." }
        guard detail != nil else { return "Choose a service for \(root.label)." }
        if !confirmed { return "Confirm the dietary counts to continue." }
        return "Ready to record catering order."
    }
}

@available(iOS 14, macOS 11, *)
private struct CateringPackageButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

@available(iOS 14, macOS 11, *)
private enum CateringPackageColors {
    static let surface = Color(.sRGB, red: 247 / 255.0, green: 249 / 255.0, blue: 252 / 255.0, opacity: 1)
    static let row = Color(.sRGB, red: 1, green: 1, blue: 1, opacity: 1)
    static let selected = Color(.sRGB, red: 229 / 255.0, green: 241 / 255.0, blue: 1, opacity: 1)
    static let accent = Color(.sRGB, red: 36 / 255.0, green: 89 / 255.0, blue: 166 / 255.0, opacity: 1)
    static let disabled = Color(.sRGB, red: 217 / 255.0, green: 225 / 255.0, blue: 236 / 255.0, opacity: 1)
    static let ink = Color(.sRGB, red: 21 / 255.0, green: 36 / 255.0, blue: 59 / 255.0, opacity: 1)
    static let muted = Color(.sRGB, red: 82 / 255.0, green: 97 / 255.0, blue: 116 / 255.0, opacity: 1)
    static let onAccent = Color(.sRGB, red: 1, green: 1, blue: 1, opacity: 1)
    static let outline = Color(.sRGB, red: 184 / 255.0, green: 197 / 255.0, blue: 214 / 255.0, opacity: 1)
}
