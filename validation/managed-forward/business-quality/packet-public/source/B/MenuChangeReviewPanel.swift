import SwiftUI

public struct MenuReplacementOption: Codable, Equatable {
    public let id: String
    public let title: String
    public let detail: String
    public let pricePerServingCents: Int
    public let minimumServings: Int
    public let maximumServings: Int
    public let available: Bool

    public init(id: String, title: String, detail: String,
                pricePerServingCents: Int, minimumServings: Int,
                maximumServings: Int, available: Bool) {
        self.id = id
        self.title = title
        self.detail = detail
        self.pricePerServingCents = pricePerServingCents
        self.minimumServings = minimumServings
        self.maximumServings = maximumServings
        self.available = available
    }
}

public struct MenuChangeModel: Codable, Equatable {
    public let requestID: String
    public let revision: Int
    public let orderReference: String
    public let venue: String
    public let occasion: String
    public let originalDish: String
    public let respondBy: String
    public let requestedServings: Int
    public let prepaidTotalCents: Int
    public let trayReturnCreditCents: Int
    public let notice: String
    public let options: [MenuReplacementOption]
    public let kitchenNotes: [String]

    public init(requestID: String, revision: Int, orderReference: String,
                venue: String, occasion: String, originalDish: String,
                respondBy: String, requestedServings: Int,
                prepaidTotalCents: Int, trayReturnCreditCents: Int,
                notice: String, options: [MenuReplacementOption],
                kitchenNotes: [String]) {
        self.requestID = requestID
        self.revision = revision
        self.orderReference = orderReference
        self.venue = venue
        self.occasion = occasion
        self.originalDish = originalDish
        self.respondBy = respondBy
        self.requestedServings = requestedServings
        self.prepaidTotalCents = prepaidTotalCents
        self.trayReturnCreditCents = trayReturnCreditCents
        self.notice = notice
        self.options = options
        self.kitchenNotes = kitchenNotes
    }
}

public struct MenuChangeSubmission: Equatable {
    public let requestID: String
    public let revision: Int
    public let optionID: String
    public let servings: Int
    public let useTrayCredit: Bool
    public let balanceCents: Int

    public init(requestID: String, revision: Int, optionID: String,
                servings: Int, useTrayCredit: Bool, balanceCents: Int) {
        self.requestID = requestID
        self.revision = revision
        self.optionID = optionID
        self.servings = servings
        self.useTrayCredit = useTrayCredit
        self.balanceCents = balanceCents
    }

    public var wireValue: String {
        "menu.submit|request=\(requestID)|revision=\(revision)|option=\(optionID)|servings=\(servings)|trayCredit=\(useTrayCredit ? "true" : "false")|balanceCents=\(balanceCents)"
    }
}

private struct MenuReviewDraft {
    var requestID: String
    var revision: Int
    var selectedID: String?
    var servings: Int
    var useTrayCredit = false
    var accepted = false
    var sent = false

    init(model: MenuChangeModel) {
        requestID = model.requestID
        revision = model.revision
        servings = model.requestedServings
    }

    func reconciled(with model: MenuChangeModel) -> MenuReviewDraft {
        guard requestID == model.requestID else { return MenuReviewDraft(model: model) }
        guard revision != model.revision else { return self }
        var next = self
        next.revision = model.revision
        next.accepted = false
        next.sent = false
        next.useTrayCredit = useTrayCredit && model.trayReturnCreditCents > 0
        if let option = model.options.first(where: { $0.id == selectedID && $0.available }) {
            next.servings = min(max(servings, option.minimumServings), option.maximumServings)
        } else {
            next.selectedID = nil
        }
        return next
    }

    func selectedOption(in model: MenuChangeModel) -> MenuReplacementOption? {
        model.options.first { $0.id == selectedID && $0.available }
    }

    func appliedCredit(in model: MenuChangeModel) -> Int {
        useTrayCredit ? model.trayReturnCreditCents : 0
    }

    func balance(in model: MenuChangeModel) -> Int? {
        guard let option = selectedOption(in: model) else { return nil }
        return option.pricePerServingCents * servings - model.prepaidTotalCents - appliedCredit(in: model)
    }

    var status: String {
        if sent { return "Request sent. Waiting for the kitchen." }
        if selectedID == nil { return "Choose a replacement to continue." }
        if !accepted { return "Review the balance and accept the updated menu." }
        return "Ready to send to the kitchen."
    }
}

private struct MenuReviewPalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let value = dark ? darkValue : light
        return Color(.sRGB, red: Double((value >> 16) & 255) / 255,
                     green: Double((value >> 8) & 255) / 255,
                     blue: Double(value & 255) / 255, opacity: 1)
    }
    var canvas: Color { color(0xF5F2EA, 0x101A15) }
    var surface: Color { color(0xFFFFFF, 0x19291F) }
    var ink: Color { color(0x1F2A25, 0xF2F7F3) }
    var secondary: Color { color(0x59665E, 0xB8C8BC) }
    var accent: Color { color(0x216B4A, 0x8DDBAF) }
    var selection: Color { color(0xE9F3ED, 0x254735) }
    var border: Color { color(0xCBD5CC, 0x3D5848) }
    var noticeInk: Color { color(0x975A16, 0xFFCA80) }
    var noticeFill: Color { color(0xFFF0D9, 0x382A17) }
    var sendInk: Color { color(0xFFFFFF, 0x102017) }
    var disabledFill: Color { color(0xD9E2DC, 0x344A3C) }
    var disabledInk: Color { color(0x68756D, 0x93A99A) }
}

// Each label supplies its enabled/disabled palette. Keep native Button semantics
// without applying a second disabled opacity to the complete card or action.
private struct MenuReviewButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

private func menuMoney(_ cents: Int) -> String {
    let magnitude = cents.magnitude
    let fraction = magnitude % 100
    return "$\(magnitude / 100).\(fraction < 10 ? "0" : "")\(fraction)"
}

/// An embedded, non-scrolling review of the caller's current menu-change snapshot.
@available(iOS 14, macOS 11, *)
public struct MenuChangeReviewPanel: View {
    private let model: MenuChangeModel
    private let onSubmit: (MenuChangeSubmission) -> Void
    @State private var draft: MenuReviewDraft
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .caption) private var eyebrowSize: CGFloat = 12
    @ScaledMetric(relativeTo: .title) private var titleSize: CGFloat = 28
    @ScaledMetric(relativeTo: .footnote) private var detailSize: CGFloat = 13
    @ScaledMetric(relativeTo: .headline) private var headingSize: CGFloat = 18
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 15
    @ScaledMetric(relativeTo: .title) private var amountSize: CGFloat = 26
    @ScaledMetric(relativeTo: .body) private var buttonSize: CGFloat = 16
    @ScaledMetric(relativeTo: .title2) private var countSize: CGFloat = 20

    public init(model: MenuChangeModel, onSubmit: @escaping (MenuChangeSubmission) -> Void) {
        self.model = model
        self.onSubmit = onSubmit
        _draft = State(initialValue: MenuReviewDraft(model: model))
    }

    private var palette: MenuReviewPalette { MenuReviewPalette(dark: colorScheme == .dark) }
    // Derive the current snapshot before drawing or handling an action. onChange persists
    // that reconciliation without recreating the component's identity.
    private var currentDraft: MenuReviewDraft { draft.reconciled(with: model) }

    public var body: some View {
        let current = currentDraft
        return VStack(alignment: .leading, spacing: 20) {
            header
            text(model.notice, size: bodySize, color: palette.noticeInk)
                .accessibilityIdentifier("menu.notice")
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(palette.noticeFill)
                .cornerRadius(16)
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(palette.border, lineWidth: 1))
            choices(current)
            servingControls(current)
            creditSwitch(current)
            summary(current)
            notes
            footer(current)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(palette.canvas)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("menu.canvas")
        .onChange(of: model) { updated in
            draft = draft.reconciled(with: updated)
        }
    }

    private func text(_ value: String, size: CGFloat, weight: Font.Weight = .regular,
                      color: Color? = nil) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color ?? palette.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func heading(_ value: String) -> some View {
        text(value, size: headingSize, weight: .semibold)
            .accessibilityAddTraits(.isHeader)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            text("MENU CHANGE", size: eyebrowSize, weight: .medium, color: palette.secondary)
            text(model.occasion, size: titleSize, weight: .bold)
                .accessibilityIdentifier("menu.title")
                .accessibilityAddTraits(.isHeader)
            text("Order \(model.orderReference) · \(model.venue) · revision \(model.revision)",
                 size: detailSize, color: palette.secondary)
                .accessibilityIdentifier("menu.context")
            text("Replacing: \(model.originalDish) · \(model.requestedServings) servings",
                 size: detailSize)
                .accessibilityIdentifier("menu.original")
            text("Please respond by \(model.respondBy)", size: detailSize, color: palette.secondary)
        }
    }

    private func choices(_ current: MenuReviewDraft) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            heading("Choose a replacement")
            ForEach(model.options, id: \.id) { option in
                optionButton(option, current: current)
            }
        }
    }

    private func optionButton(_ option: MenuReplacementOption, current: MenuReviewDraft) -> some View {
        let selected = current.selectedID == option.id
        let enabled = option.available && !current.sent
        return Button(action: { select(option.id) }) {
            VStack(alignment: .leading, spacing: 8) {
                text(option.title, size: bodySize, weight: .semibold,
                     color: enabled ? palette.ink : palette.secondary)
                text(option.detail, size: detailSize, color: palette.secondary)
                text("\(menuMoney(option.pricePerServingCents)) per serving",
                     size: detailSize, color: palette.secondary)
                text("\(option.minimumServings)–\(option.maximumServings) servings",
                     size: detailSize, color: palette.secondary)
                if !option.available {
                    text("Unavailable", size: detailSize, color: palette.secondary)
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 64, alignment: .leading)
            .background(selected ? palette.selection : palette.surface)
            .cornerRadius(16)
            .overlay(RoundedRectangle(cornerRadius: 16)
                .stroke(selected ? palette.accent : palette.border, lineWidth: 1))
        }
        .buttonStyle(MenuReviewButtonStyle())
        .disabled(!enabled)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(option.title))
        .accessibilityHint(Text("\(option.detail) \(menuMoney(option.pricePerServingCents)) per serving. \(option.minimumServings)–\(option.maximumServings) servings.\(option.available ? "" : " Unavailable.")"))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("menu.option.\(option.id)")
    }

    private func servingControls(_ current: MenuReviewDraft) -> some View {
        let option = current.selectedOption(in: model)
        return VStack(alignment: .leading, spacing: 8) {
            heading("Servings")
            HStack(alignment: .center, spacing: 8) {
                quantityButton("−", label: "Decrease servings", identifier: "menu.decrease",
                               enabled: !current.sent && option != nil && current.servings > (option?.minimumServings ?? current.servings)) {
                    changeServings(by: -1)
                }
                text("\(current.servings) servings", size: countSize, weight: .semibold)
                    .accessibilityIdentifier("menu.servings")
                    .layoutPriority(1)
                quantityButton("+", label: "Increase servings", identifier: "menu.increase",
                               enabled: !current.sent && option != nil && current.servings < (option?.maximumServings ?? current.servings)) {
                    changeServings(by: 1)
                }
            }
        }
    }

    private func quantityButton(_ symbol: String, label: String, identifier: String,
                                enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(symbol)
                .font(.system(size: countSize, weight: .semibold))
                .foregroundColor(enabled ? palette.accent : palette.disabledInk)
                .padding(8)
                .frame(minWidth: 44, minHeight: 44)
                .background(enabled ? palette.surface : palette.disabledFill)
                .cornerRadius(16)
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(palette.border, lineWidth: 1))
        }
        .buttonStyle(MenuReviewButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(label))
        .accessibilityIdentifier(identifier)
    }

    private func creditSwitch(_ current: MenuReviewDraft) -> some View {
        Toggle(isOn: Binding(get: { currentDraft.useTrayCredit }, set: { value in
            var next = currentDraft
            guard !next.sent, model.trayReturnCreditCents > 0, next.useTrayCredit != value else { return }
            next.useTrayCredit = value
            next.accepted = false
            draft = next
        })) {
            VStack(alignment: .leading, spacing: 8) {
                text("Use tray return credit", size: bodySize)
                text("Offered credit \(menuMoney(model.trayReturnCreditCents))", size: detailSize,
                     color: palette.secondary)
            }
        }
        .toggleStyle(SwitchToggleStyle(tint: palette.accent))
        .disabled(current.sent || model.trayReturnCreditCents == 0)
        .accessibilityLabel(Text("Use tray return credit"))
        .accessibilityIdentifier("menu.credit")
    }

    private func moneyLine(_ label: String, value: String, identifier: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            text(label, size: detailSize, color: palette.secondary)
            text(value, size: bodySize)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text("\(label) \(value)"))
        .accessibilityIdentifier(identifier)
    }

    private func summary(_ current: MenuReviewDraft) -> some View {
        let option = current.selectedOption(in: model)
        return VStack(alignment: .leading, spacing: 8) {
            heading("Balance")
            text(option?.title ?? "No replacement selected", size: bodySize, weight: .semibold)
                .accessibilityIdentifier("menu.selection")
            moneyLine("Replacement total", value: option.map { menuMoney($0.pricePerServingCents * current.servings) } ?? "—",
                      identifier: "menu.replacementTotal")
            moneyLine("Already paid", value: menuMoney(model.prepaidTotalCents), identifier: "menu.prepaid")
            moneyLine("Tray credit applied", value: menuMoney(current.appliedCredit(in: model)), identifier: "menu.creditApplied")
            balanceDisplay(current.balance(in: model))
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.surface)
        .cornerRadius(16)
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(palette.border, lineWidth: 1))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("menu.summary")
    }

    @ViewBuilder private func balanceDisplay(_ cents: Int?) -> some View {
        if let cents = cents {
            if cents == 0 {
                text("No balance due", size: amountSize, weight: .bold)
                    .accessibilityIdentifier("menu.balance")
            } else {
                let label = cents < 0 ? "Refund" : "Additional payment"
                let color = cents < 0 ? palette.accent : palette.ink
                VStack(alignment: .leading, spacing: 8) {
                    text(label, size: bodySize, color: color)
                    text(menuMoney(cents), size: amountSize, weight: .bold, color: color)
                }
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(Text("\(label) \(menuMoney(cents))"))
                .accessibilityIdentifier("menu.balance")
            }
        } else {
            text("Select a dish to calculate the balance", size: bodySize)
                .accessibilityIdentifier("menu.balance")
        }
    }

    private var notes: some View {
        VStack(alignment: .leading, spacing: 8) {
            heading("Kitchen notes")
            VStack(alignment: .leading, spacing: 10) {
                ForEach(model.kitchenNotes.indices, id: \.self) { index in
                    if index == model.kitchenNotes.count - 1 {
                        text(model.kitchenNotes[index], size: bodySize)
                            .accessibilityIdentifier("menu.notes.last")
                    } else {
                        text(model.kitchenNotes[index], size: bodySize)
                    }
                }
            }
        }
    }

    private func footer(_ current: MenuReviewDraft) -> some View {
        let canSend = current.selectedOption(in: model) != nil && current.accepted && !current.sent
        return VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                heading("Your confirmation")
                Toggle(isOn: Binding(get: { currentDraft.accepted }, set: { value in
                    var next = currentDraft
                    guard !next.sent, next.selectedOption(in: model) != nil else { return }
                    next.accepted = value
                    draft = next
                })) {
                    text("I accept the replacement, serving count, and balance shown.", size: bodySize)
                }
                .toggleStyle(SwitchToggleStyle(tint: palette.accent))
                .disabled(current.sent || current.selectedOption(in: model) == nil)
                .accessibilityLabel(Text("I accept the replacement, serving count, and balance shown."))
                .accessibilityIdentifier("menu.ack")
            }
            text(current.status, size: bodySize, color: palette.secondary)
                .accessibilityIdentifier("menu.status")
            Button(action: submit) {
                Text(current.sent ? "Request sent" : "Send replacement request")
                    .font(.system(size: buttonSize, weight: .semibold))
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .foregroundColor(canSend ? palette.sendInk : palette.disabledInk)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .frame(maxWidth: .infinity, minHeight: 52)
                    .background(canSend ? palette.accent : palette.disabledFill)
                    .cornerRadius(16)
            }
            .buttonStyle(MenuReviewButtonStyle())
            .disabled(!canSend)
            .accessibilityIdentifier("menu.submit")
        }
    }

    private func select(_ id: String) {
        var next = currentDraft
        guard !next.sent, next.selectedID != id,
              let option = model.options.first(where: { $0.id == id && $0.available }) else { return }
        next.selectedID = option.id
        next.servings = min(max(next.servings, option.minimumServings), option.maximumServings)
        next.accepted = false
        draft = next
    }

    private func changeServings(by delta: Int) {
        var next = currentDraft
        guard !next.sent, let option = next.selectedOption(in: model) else { return }
        guard delta < 0 ? next.servings > option.minimumServings : next.servings < option.maximumServings else { return }
        next.servings += delta
        next.accepted = false
        draft = next
    }

    private func submit() {
        var next = currentDraft
        guard !next.sent, next.accepted,
              let option = next.selectedOption(in: model), let balance = next.balance(in: model) else { return }
        onSubmit(MenuChangeSubmission(requestID: model.requestID, revision: model.revision,
                                      optionID: option.id, servings: next.servings,
                                      useTrayCredit: next.useTrayCredit, balanceCents: balance))
        next.sent = true
        draft = next
    }
}
