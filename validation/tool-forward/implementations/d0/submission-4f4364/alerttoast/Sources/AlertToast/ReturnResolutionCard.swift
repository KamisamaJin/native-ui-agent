import SwiftUI

private struct RRPalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let rgb = dark ? darkValue : light
        return Color(.sRGB, red: Double((rgb >> 16) & 255) / 255,
                     green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255, opacity: 1)
    }
    var card: Color { color(0xFFFFFF, 0x192224) }
    var panel: Color { color(0xF5F3EE, 0x253033) }
    var text: Color { color(0x20282D, 0xF2F6F3) }
    var secondary: Color { color(0x5D676C, 0xB4C0BB) }
    var border: Color { color(0xD7DDD9, 0x4A5A56) }
    var accent: Color { color(0x21645A, 0x8ED6BD) }
    var foreground: Color { color(0xFFFFFF, 0x12382C) }
    var tint: Color { color(0xEAF5EF, 0x223F36) }
    var disabled: Color { color(0xDFE6E1, 0x34443C) }
    var disabledText: Color { color(0x59655E, 0xBAC8C0) }
    var urgent: Color { color(0xFFF0D2, 0x4A3B1D) }
    var urgentText: Color { color(0x775004, 0xF7D58A) }
    func tile(_ accent: ReturnResolutionAccent) -> Color {
        switch accent {
        case .teal: return color(0xDDEFE9, 0x28483E)
        case .coral: return color(0xF8E2D9, 0x52382F)
        case .indigo: return color(0xE4E5F5, 0x353951)
        }
    }
}

/// A caller-controlled return decision. Activations only emit requests.
@available(iOS 14, macOS 11, *)
public struct ReturnResolutionCard: View {
    public let model: ReturnResolutionModel
    public let onAction: (ReturnResolutionAction) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .caption) private var caption: CGFloat = 12
    @ScaledMetric(relativeTo: .footnote) private var label: CGFloat = 13
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 15
    @ScaledMetric(relativeTo: .headline) private var section: CGFloat = 17
    @ScaledMetric(relativeTo: .headline) private var money: CGFloat = 18
    @ScaledMetric(relativeTo: .title2) private var heading: CGFloat = 24

    public init(model: ReturnResolutionModel, onAction: @escaping (ReturnResolutionAction) -> Void) {
        self.model = model
        self.onAction = onAction
    }
    private var c: RRPalette { RRPalette(dark: colorScheme == .dark) }
    private var option: ReturnResolutionOption? {
        model.options.first { $0.id == model.selectedOptionId && $0.disabledReason == nil }
    }
    private var size: ReturnResolutionSize? {
        model.sizes.first { $0.id == model.selectedSizeId && $0.unavailableReason == nil }
    }
    private var enabled: Bool {
        guard let option = option else { return false }
        return (option.kind != .exchange || size != nil) &&
            (option.acknowledgementLabel == nil || model.acknowledgementAccepted)
    }
    private var gate: String {
        if !model.options.contains(where: { $0.disabledReason == nil }) { return model.strings.noOptions }
        guard let option = option else { return model.strings.chooseOption }
        if option.kind == .exchange && size == nil { return model.strings.chooseSize }
        if option.acknowledgementLabel != nil && !model.acknowledgementAccepted { return model.strings.acceptTerms }
        return model.strings.ready
    }
    private func text(_ value: String, _ size: CGFloat, _ color: Color, strong: Bool = false) -> some View {
        Text(verbatim: value).font(.system(size: size, weight: strong ? .semibold : .regular))
            .foregroundColor(color).fixedSize(horizontal: false, vertical: true)
            .multilineTextAlignment(.leading)
    }
    private func pill(_ value: String) -> some View {
        text(value, caption, c.accent, strong: true).padding(.horizontal, 10).padding(.vertical, 6)
            .background(c.tint).clipShape(RoundedRectangle(cornerRadius: 16))
    }
    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            header
            item
            switch model.status {
            case .editing:
                editing
            case .submitting:
                progress
            case .complete:
                result
            }
            summary
            if model.status == .editing {
                footer
            } else if model.status == .complete {
                actionButton(model.doneLabel, id: "rr.done") { onAction(.done) }
            }
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(c.card).clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(RoundedRectangle(cornerRadius: 20).stroke(c.border, lineWidth: 1))
        .accessibilityIdentifier("rr.card")
    }
    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            text(model.merchant, caption, c.secondary)
            text(model.heading, heading, c.text, strong: true)
                .accessibilityAddTraits(.isHeader).accessibilityIdentifier("rr.header.title")
            text(model.orderReference, label, c.secondary)
            text(model.intro, bodySize, c.secondary)
            pill(model.statusLabel).accessibilityIdentifier("rr.header.badge")
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
    private var item: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "shippingbox").font(.system(size: 26, weight: .regular))
                .foregroundColor(c.accent).frame(width: 52, height: 52)
                .background(c.tile(model.item.accent)).clipShape(RoundedRectangle(cornerRadius: 12))
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 4) {
                text(model.item.title, section, c.text, strong: true)
                text(model.item.variant, label, c.secondary)
                text(model.item.quantityLabel, label, c.secondary)
                text(model.item.paidLabel, bodySize, c.text, strong: true)
            }.frame(maxWidth: .infinity, alignment: .leading)
        }.accessibilityElement(children: .combine).accessibilityIdentifier("rr.item")
    }
    private var editing: some View {
        Group {
            if let deadline = model.deadline {
                text(deadline.text, label, deadline.urgent ? c.urgentText : c.secondary, strong: true)
                    .frame(maxWidth: .infinity, alignment: .leading).padding(12)
                    .background(deadline.urgent ? c.urgent : c.panel)
                    .clipShape(RoundedRectangle(cornerRadius: 10)).accessibilityIdentifier("rr.deadline")
            }
            text(model.contextMessage, bodySize, c.secondary)
            VStack(alignment: .leading, spacing: 12) {
                text(model.optionsTitle, section, c.text, strong: true)
                ForEach(model.options, id: \.id) { option in optionButton(option) }
            }
            if let option = option {
                details(option)
                if option.kind == .exchange { sizes }
                if let acknowledgement = option.acknowledgementLabel { acknowledgementButton(acknowledgement) }
            }
            notes
            if !model.amountRows.isEmpty { breakdown }
        }
    }
    private func optionName(_ option: ReturnResolutionOption) -> String {
        ([option.title, option.description, option.amountLabel] + [option.tag, option.disabledReason].compactMap { $0 }).joined(separator: ", ")
    }
    private func optionButton(_ value: ReturnResolutionOption) -> some View {
        let selected = option?.id == value.id
        return Button(action: {
            if value.disabledReason == nil { onAction(.selectOption(optionId: value.id)) }
        }) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle().stroke(selected ? c.accent : c.border, lineWidth: 2)
                    if selected { Circle().fill(c.accent).padding(6) }
                }.frame(width: 24, height: 24).accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 8) {
                    text(value.title, section, c.text, strong: true)
                    text(value.description, bodySize, c.secondary)
                    text(value.amountLabel, money, c.text, strong: true)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                    if let tag = value.tag { pill(tag) }
                    if let reason = value.disabledReason {
                        text(reason, label, c.secondary).accessibilityIdentifier("rr.option.\(value.id).reason")
                    }
                }.frame(maxWidth: .infinity, alignment: .leading)
            }.padding(12).frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
                .background(selected ? c.tint : c.card).clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected ? c.accent : c.border, lineWidth: selected ? 2 : 1))
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }.buttonStyle(PlainButtonStyle()).disabled(value.disabledReason != nil)
            .accessibilityLabel(Text(verbatim: optionName(value)))
            .accessibilityAddTraits(selected ? [.isSelected] : [])
            .accessibilityIdentifier("rr.option.\(value.id)")
    }
    private func details(_ option: ReturnResolutionOption) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            text(option.detailTitle, section, c.text, strong: true)
            text(option.detailBody, bodySize, c.secondary)
        }.frame(maxWidth: .infinity, alignment: .leading).padding(12).background(c.panel)
            .clipShape(RoundedRectangle(cornerRadius: 10)).accessibilityIdentifier("rr.detail")
    }
    private var sizes: some View {
        VStack(alignment: .leading, spacing: 12) {
            text(model.sizesTitle, section, c.text, strong: true)
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 96), spacing: 12, alignment: .top)], alignment: .leading, spacing: 12) {
                ForEach(model.sizes, id: \.id) { value in sizeButton(value) }
            }
        }.accessibilityIdentifier("rr.sizes")
    }
    private func sizeButton(_ value: ReturnResolutionSize) -> some View {
        let selected = size?.id == value.id
        return Button(action: {
            if value.unavailableReason == nil { onAction(.selectSize(sizeId: value.id)) }
        }) {
            VStack(alignment: .center, spacing: 4) {
                text(value.label, bodySize, value.unavailableReason == nil ? c.text : c.secondary, strong: selected)
                if let reason = value.unavailableReason {
                    text(reason, caption, c.secondary).accessibilityIdentifier("rr.size.\(value.id).reason")
                }
            }.padding(12).frame(minWidth: 48, maxWidth: .infinity, minHeight: 48)
                .background(selected ? c.tint : c.card).clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected ? c.accent : c.border, lineWidth: selected ? 2 : 1))
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }.buttonStyle(PlainButtonStyle()).disabled(value.unavailableReason != nil)
            .accessibilityLabel(Text(verbatim: ([value.label] + [value.unavailableReason].compactMap { $0 }).joined(separator: ", ")))
            .accessibilityAddTraits(selected ? [.isSelected] : [])
            .accessibilityIdentifier("rr.size.\(value.id)")
    }
    private func acknowledgementButton(_ value: String) -> some View {
        Button(action: { onAction(.setAcknowledgement(accepted: !model.acknowledgementAccepted)) }) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 2).stroke(c.accent, lineWidth: 2)
                    if model.acknowledgementAccepted { Image(systemName: "checkmark").font(.system(size: 16, weight: .semibold)).foregroundColor(c.accent) }
                }.frame(width: 22, height: 22).accessibilityHidden(true)
                text(value, bodySize, c.text).frame(maxWidth: .infinity, alignment: .leading)
            }.padding(.vertical, 8).frame(maxWidth: .infinity, minHeight: 48, alignment: .leading).contentShape(Rectangle())
        }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("rr.ack")
            .accessibilityLabel(Text(verbatim: value))
            .accessibilityValue(Text(verbatim: model.acknowledgementAccepted ? model.strings.checkedValue : model.strings.uncheckedValue))
    }
    private var notes: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button(action: { onAction(.setNotesExpanded(expanded: !model.notesExpanded)) }) {
                HStack(spacing: 12) {
                    text(model.notes.title, bodySize, c.text, strong: true).frame(maxWidth: .infinity, alignment: .leading)
                    Image(systemName: model.notesExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14, weight: .semibold)).foregroundColor(c.accent).accessibilityHidden(true)
                }.frame(maxWidth: .infinity, minHeight: 44, alignment: .leading).contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("rr.notes.toggle")
                .accessibilityLabel(Text(verbatim: model.notes.title))
                .accessibilityValue(Text(verbatim: model.notesExpanded ? model.strings.expandedValue : model.strings.collapsedValue))
            if model.notesExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    text(model.notes.body, bodySize, c.secondary)
                    ForEach(Array(model.notes.bullets.enumerated()), id: \.offset) { _, bullet in
                        HStack(alignment: .top, spacing: 8) {
                            text("•", bodySize, c.secondary).accessibilityHidden(true)
                            text(bullet, bodySize, c.secondary).frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }.accessibilityIdentifier("rr.notes.body")
            }
        }.frame(maxWidth: .infinity, alignment: .leading).padding(12).background(c.panel)
            .clipShape(RoundedRectangle(cornerRadius: 10))
    }
    private var breakdown: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(model.amountRows, id: \.id) { row in
                VStack(alignment: .leading, spacing: 4) {
                    text(row.label, bodySize, c.secondary, strong: row.emphasized)
                    text(row.value, bodySize, c.text, strong: row.emphasized).frame(maxWidth: .infinity, alignment: .trailing)
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
        }.frame(maxWidth: .infinity, alignment: .leading).accessibilityIdentifier("rr.breakdown")
    }
    private var summary: some View {
        VStack(alignment: .leading, spacing: 8) {
            text(model.totalLabel, money, c.text, strong: true)
            text(model.totalValue, heading, c.text, strong: true).frame(maxWidth: .infinity, alignment: .trailing)
            text(model.totalFootnote, caption, c.secondary)
        }.frame(maxWidth: .infinity, alignment: .leading).accessibilityIdentifier("rr.summary")
    }
    private var progress: some View {
        HStack(alignment: .top, spacing: 12) {
            ProgressView().progressViewStyle(CircularProgressViewStyle(tint: c.accent)).accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 8) {
                text(model.progressTitle, section, c.text, strong: true)
                text(model.progressBody, bodySize, c.secondary)
            }.frame(maxWidth: .infinity, alignment: .leading)
        }.frame(maxWidth: .infinity, alignment: .leading).padding(12).background(c.panel)
            .clipShape(RoundedRectangle(cornerRadius: 10)).accessibilityElement(children: .combine)
            .accessibilityValue(Text(verbatim: model.strings.busyValue)).accessibilityIdentifier("rr.progress")
    }
    private var result: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "checkmark.circle.fill").font(.system(size: 24)).foregroundColor(c.accent).accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 8) {
                text(model.resultTitle, section, c.accent, strong: true)
                text(model.resultBody, bodySize, c.accent)
                text(model.resultReference, label, c.accent)
            }.frame(maxWidth: .infinity, alignment: .leading)
        }.frame(maxWidth: .infinity, alignment: .leading).padding(12).background(c.tint)
            .clipShape(RoundedRectangle(cornerRadius: 10)).accessibilityElement(children: .combine).accessibilityIdentifier("rr.result")
    }
    private var footer: some View {
        VStack(alignment: .leading, spacing: 12) {
            text(gate, label, c.secondary).accessibilityIdentifier("rr.gate")
            actionButton(option?.primaryLabel ?? model.idlePrimaryLabel, id: "rr.primary", enabled: enabled) {
                guard enabled, let option = option else { return }
                onAction(.submit(optionId: option.id, sizeId: option.kind == .exchange ? size?.id : nil,
                                 acknowledgementAccepted: option.acknowledgementLabel == nil ? false : model.acknowledgementAccepted))
            }
            Button(action: { onAction(.keepPurchase) }) {
                text(model.keepLabel, bodySize, c.accent, strong: true).padding(.horizontal, 16).padding(.vertical, 12)
                    .frame(maxWidth: .infinity, minHeight: 44).contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("rr.keep")
        }
    }
    private func actionButton(_ value: String, id: String, enabled: Bool = true, action: @escaping () -> Void) -> some View {
        Button(action: { if enabled { action() } }) {
            text(value, bodySize, enabled ? c.foreground : c.disabledText, strong: true)
                .padding(.horizontal, 16).padding(.vertical, 12).frame(maxWidth: .infinity, minHeight: 48)
                .background(enabled ? c.accent : c.disabled).clipShape(RoundedRectangle(cornerRadius: 12))
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }.buttonStyle(PlainButtonStyle()).disabled(!enabled).accessibilityIdentifier(id)
    }
}
