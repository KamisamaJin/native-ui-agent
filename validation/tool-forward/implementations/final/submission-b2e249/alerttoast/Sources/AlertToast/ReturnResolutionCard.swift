import SwiftUI

private struct ResolutionColors {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let v = dark ? darkValue : light
        return Color(red: Double((v >> 16) & 255) / 255, green: Double((v >> 8) & 255) / 255, blue: Double(v & 255) / 255)
    }
    var card: Color { color(0xFFFFFF, 0x192224) }
    var panel: Color { color(0xF5F3EE, 0x253033) }
    var text: Color { color(0x20282D, 0xF2F6F3) }
    var secondary: Color { color(0x5D676C, 0xB4C0BB) }
    var border: Color { color(0xD7DDD9, 0x4A5A56) }
    var accent: Color { color(0x21645A, 0x8ED6BD) }
    var onAccent: Color { color(0xFFFFFF, 0x12382C) }
    var tint: Color { color(0xEAF5EF, 0x223F36) }
    var disabled: Color { color(0xDFE6E1, 0x34443C) }
    var onDisabled: Color { color(0x59655E, 0xBAC8C0) }
    var urgent: Color { color(0xFFF0D2, 0x4A3B1D) }
    var onUrgent: Color { color(0x775004, 0xF7D58A) }
    func tile(_ accent: ReturnResolutionAccent) -> Color {
        switch accent {
        case .teal: return color(0xDDEFE9, 0x28483E)
        case .coral: return color(0xF8E2D9, 0x52382F)
        case .indigo: return color(0xE4E5F5, 0x353951)
        }
    }
}

/// A controlled return settlement component. The surrounding view owns its scroll container.
@available(iOS 14.0, macOS 11.0, *)
public struct ReturnResolutionCard: View {
    public let model: ReturnResolutionModel
    public let onAction: (ReturnResolutionAction) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.sizeCategory) private var sizeCategory
    @Environment(\.layoutDirection) private var direction

    public init(model: ReturnResolutionModel, onAction: @escaping (ReturnResolutionAction) -> Void) {
        self.model = model
        self.onAction = onAction
    }

    private var colors: ResolutionColors { ResolutionColors(dark: colorScheme == .dark) }
    private var option: ReturnResolutionOption? { model.options.first { $0.id == model.selectedOptionId && $0.disabledReason == nil } }
    private var size: ReturnResolutionSize? { model.sizes.first { $0.id == model.selectedSizeId && $0.unavailableReason == nil } }
    private var gate: String {
        guard model.options.contains(where: { $0.disabledReason == nil }) else { return model.strings.noOptions }
        guard let choice = option else { return model.strings.chooseOption }
        if choice.kind == .exchange && size == nil { return model.strings.chooseSize }
        if choice.acknowledgementLabel != nil && !model.acknowledgementAccepted { return model.strings.acceptTerms }
        return model.strings.ready
    }
    private var ready: Bool {
        guard let choice = option else { return false }
        return (choice.kind != .exchange || size != nil) && (choice.acknowledgementLabel == nil || model.acknowledgementAccepted)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            header
            item
            if model.status == .editing {
                editing
            } else if model.status == .submitting {
                progress
                summary
            } else {
                result
                summary
                actionButton(model.doneLabel, id: "rr.done", enabled: true) { onAction(.done) }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(colors.card)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(RoundedRectangle(cornerRadius: 20).strokeBorder(colors.border, lineWidth: 1))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("rr.card")
    }

    private func text(_ value: String, _ font: Font = .subheadline, strong: Bool = false, color: Color? = nil) -> some View {
        Text(verbatim: value)
            .font(strong ? font.weight(.semibold) : font)
            .foregroundColor(color ?? colors.text)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            text(model.merchant, .caption, color: colors.secondary)
            text(model.heading, .title2, strong: true)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("rr.header.title")
            text(model.orderReference, .footnote, color: colors.secondary)
            text(model.intro)
            text(model.statusLabel, .caption, strong: true, color: colors.accent)
                .padding(.horizontal, 10).padding(.vertical, 6)
                .background(colors.tint)
                .clipShape(RoundedRectangle(cornerRadius: 20))
                .accessibilityIdentifier("rr.header.badge")
        }
    }

    private var item: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "shippingbox")
                .font(.system(size: 26))
                .foregroundColor(colors.accent)
                .frame(width: 52, height: 52)
                .background(colors.tile(model.item.accent))
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 4) {
                text(model.item.title, .headline, strong: true)
                text(model.item.variant, .footnote, color: colors.secondary)
                text(model.item.quantityLabel, .footnote, color: colors.secondary)
                text(model.item.paidLabel, .footnote, strong: true)
            }.frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("rr.item")
    }

    @ViewBuilder private var editing: some View {
        if let deadline = model.deadline {
            text(deadline.text, .footnote, strong: true, color: deadline.urgent ? colors.onUrgent : colors.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(deadline.urgent ? colors.urgent : colors.panel)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .accessibilityIdentifier("rr.deadline")
        }
        text(model.contextMessage, color: colors.secondary)
        VStack(alignment: .leading, spacing: 12) {
            text(model.optionsTitle, .headline, strong: true)
            ForEach(model.options, id: \.id) { choice in optionButton(choice) }
        }
        if let choice = option {
            VStack(alignment: .leading, spacing: 8) {
                text(choice.detailTitle, .headline, strong: true)
                text(choice.detailBody, color: colors.secondary)
            }
            .resolutionPanel(colors.panel)
            .accessibilityIdentifier("rr.detail")
            if choice.kind == .exchange { sizes }
            if let label = choice.acknowledgementLabel { acknowledgement(label) }
        }
        notes
        if !model.amountRows.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                ForEach(model.amountRows, id: \.id) { row in
                    amountLine(row.label, row.value, emphasized: row.emphasized)
                }
            }
            .accessibilityIdentifier("rr.breakdown")
        }
        summary
        VStack(alignment: .leading, spacing: 12) {
            text(gate, .footnote, color: colors.secondary).accessibilityIdentifier("rr.gate")
            actionButton(option?.primaryLabel ?? model.idlePrimaryLabel, id: "rr.primary", enabled: ready) {
                guard ready, let choice = option else { return }
                onAction(.submit(optionId: choice.id, sizeId: choice.kind == .exchange ? size?.id : nil,
                                 acknowledgementAccepted: choice.acknowledgementLabel != nil ? model.acknowledgementAccepted : false))
            }
            Button(action: { onAction(.keepPurchase) }) {
                text(model.keepLabel, strong: true, color: colors.accent)
                    .frame(maxWidth: .infinity, minHeight: 44)
                    .contentShape(Rectangle())
            }
            .buttonStyle(ResolutionButtonStyle())
            .accessibilityIdentifier("rr.keep")
        }
    }

    private func optionButton(_ choice: ReturnResolutionOption) -> some View {
        let selected = choice.id == option?.id
        return Button(action: {
            if choice.disabledReason == nil { onAction(.selectOption(optionId: choice.id)) }
        }) {
            HStack(alignment: .top, spacing: 10) {
                ZStack {
                    Circle().stroke(selected ? colors.accent : colors.border, lineWidth: 2)
                    if selected { Circle().fill(colors.accent).padding(5) }
                }
                .frame(width: 22, height: 22).accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 8) {
                    text(choice.title, .headline, strong: true)
                    text(choice.description, color: colors.secondary)
                    text(choice.amountLabel, .headline, strong: true)
                    if let tag = choice.tag {
                        text(tag, .caption, strong: true, color: colors.accent)
                            .padding(.horizontal, 8).padding(.vertical, 4)
                            .background(colors.tint).clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    if let reason = choice.disabledReason {
                        text(reason, .footnote, color: colors.secondary)
                            .accessibilityIdentifier("rr.option.\(choice.id).reason")
                    }
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
            .background(selected ? colors.tint : colors.card)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? colors.accent : colors.border, lineWidth: selected ? 2 : 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(ResolutionButtonStyle())
        .disabled(choice.disabledReason != nil)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("rr.option.\(choice.id)")
    }

    private var sizes: some View {
        VStack(alignment: .leading, spacing: 12) {
            text(model.sizesTitle, .headline, strong: true)
            // Eager rows contribute their complete natural height to the parent's scroll view.
            // Two columns fit the narrowest offered card; accessibility text uses one column.
            let columnCount = sizeCategory.isAccessibilityCategory ? 1 : 2
            let rows = stride(from: 0, to: model.sizes.count, by: columnCount).map {
                Array(model.sizes[$0..<min($0 + columnCount, model.sizes.count)])
            }
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(rows.enumerated()), id: \.offset) { row in
                    HStack(alignment: .top, spacing: 8) {
                        ForEach(row.element, id: \.id) { choice in
                            sizeButton(choice)
                        }
                        if row.element.count < columnCount {
                            Spacer(minLength: 0).frame(maxWidth: .infinity)
                        }
                    }
                }
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("rr.sizes")
    }

    private func sizeButton(_ choice: ReturnResolutionSize) -> some View {
        let selected = choice.id == size?.id
        return Button(action: {
            if choice.unavailableReason == nil { onAction(.selectSize(sizeId: choice.id)) }
        }) {
            VStack(alignment: .leading, spacing: 4) {
                text(choice.label, strong: selected)
                if let reason = choice.unavailableReason {
                    text(reason, .caption, color: colors.secondary)
                        .accessibilityIdentifier("rr.size.\(choice.id).reason")
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .background(selected ? colors.tint : colors.card)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? colors.accent : colors.border, lineWidth: selected ? 2 : 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(ResolutionButtonStyle())
        .disabled(choice.unavailableReason != nil)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("rr.size.\(choice.id)")
    }

    private func acknowledgement(_ label: String) -> some View {
        Button(action: { onAction(.setAcknowledgement(accepted: !model.acknowledgementAccepted)) }) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: model.acknowledgementAccepted ? "checkmark.square" : "square")
                    .font(.system(size: 24)).foregroundColor(colors.accent).accessibilityHidden(true)
                text(label).frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(ResolutionButtonStyle())
        .accessibilityLabel(Text(verbatim: label))
        .accessibilityValue(Text(verbatim: model.acknowledgementAccepted ? model.strings.checkedValue : model.strings.uncheckedValue))
        .accessibilityIdentifier("rr.ack")
    }

    private var notes: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button(action: { onAction(.setNotesExpanded(expanded: !model.notesExpanded)) }) {
                HStack(spacing: 8) {
                    text(model.notes.title, strong: true).frame(maxWidth: .infinity, alignment: .leading)
                    Image(systemName: model.notesExpanded ? "chevron.down" : direction == .rightToLeft ? "chevron.left" : "chevron.right")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(colors.secondary).accessibilityHidden(true)
                }
                .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                .contentShape(Rectangle())
            }
            .buttonStyle(ResolutionButtonStyle())
            .accessibilityLabel(Text(verbatim: model.notes.title))
            .accessibilityValue(Text(verbatim: model.notesExpanded ? model.strings.expandedValue : model.strings.collapsedValue))
            .accessibilityIdentifier("rr.notes.toggle")
            if model.notesExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    text(model.notes.body, color: colors.secondary)
                    ForEach(Array(model.notes.bullets.enumerated()), id: \.offset) { pair in
                        HStack(alignment: .top, spacing: 8) {
                            text("•", color: colors.secondary).accessibilityHidden(true)
                            text(pair.element, color: colors.secondary).frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
                .accessibilityIdentifier("rr.notes.body")
            }
        }
        .resolutionPanel(colors.panel)
    }

    private var summary: some View {
        VStack(alignment: .leading, spacing: 8) {
            amountLine(model.totalLabel, model.totalValue, emphasized: true, total: true)
            text(model.totalFootnote, .footnote, color: colors.secondary)
        }
        .accessibilityIdentifier("rr.summary")
    }

    @ViewBuilder private func amountLine(_ label: String, _ value: String, emphasized: Bool, total: Bool = false) -> some View {
        if sizeCategory > .large {
            VStack(alignment: .leading, spacing: 4) {
                text(label, total ? .headline : .subheadline, strong: emphasized)
                text(value, total ? .title3 : .subheadline, strong: emphasized)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
        } else {
            HStack(alignment: .top, spacing: 12) {
                text(label, total ? .headline : .subheadline, strong: emphasized)
                    .frame(maxWidth: .infinity, alignment: .leading)
                text(value, total ? .title3 : .subheadline, strong: emphasized)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
        }
    }

    private var progress: some View {
        VStack(alignment: .leading, spacing: 12) {
            ProgressView().progressViewStyle(CircularProgressViewStyle(tint: colors.accent)).accessibilityHidden(true)
            text(model.progressTitle, .headline, strong: true)
            text(model.progressBody, color: colors.secondary)
        }
        .resolutionPanel(colors.panel)
        .accessibilityElement(children: .combine)
        .accessibilityValue(Text(verbatim: model.strings.busyValue))
        .accessibilityIdentifier("rr.progress")
    }

    private var result: some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: "checkmark.circle.fill").font(.system(size: 26)).foregroundColor(colors.accent).accessibilityHidden(true)
            text(model.resultTitle, .headline, strong: true, color: colors.accent)
            text(model.resultBody)
            text(model.resultReference, .footnote, color: colors.secondary)
        }
        .resolutionPanel(colors.tint)
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("rr.result")
    }

    private func actionButton(_ label: String, id: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: { if enabled { action() } }) {
            text(label, strong: true, color: enabled ? colors.onAccent : colors.onDisabled)
                .padding(12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(enabled ? colors.accent : colors.disabled)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(ResolutionButtonStyle())
        .disabled(!enabled)
        .accessibilityIdentifier(id)
    }
}

@available(iOS 14.0, macOS 11.0, *)
private extension View {
    func resolutionPanel(_ color: Color) -> some View {
        self.frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(color)
            .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

/// Keeps caller-authored color roles legible while native Button still owns disabled semantics.
@available(iOS 14.0, macOS 11.0, *)
private struct ResolutionButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.opacity(configuration.isPressed ? 0.88 : 1)
    }
}
