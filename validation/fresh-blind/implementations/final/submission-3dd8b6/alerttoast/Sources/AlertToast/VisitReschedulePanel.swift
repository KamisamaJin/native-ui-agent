import SwiftUI

private struct VisitPalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let value = dark ? darkValue : light
        return Color(.sRGB, red: Double((value >> 16) & 255) / 255,
                     green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255, opacity: 1)
    }
    var panel: Color { color(0xFFFFFF, 0x161C27) }
    var primary: Color { color(0x182230, 0xF2F4F7) }
    var secondary: Color { color(0x526174, 0xB8C4D4) }
    var inset: Color { color(0xF4F6F9, 0x202938) }
    var border: Color { color(0xD5DDE7, 0x485568) }
    var accent: Color { color(0x175CD3, 0x84ADFF) }
    var selected: Color { color(0xEFF6FF, 0x162F51) }
    var warning: Color { color(0x854A0E, 0xFFD691) }
    var warningFill: Color { color(0xFFF7E0, 0x3B2D17) }
    var success: Color { color(0x087443, 0x75E0AD) }
    var successFill: Color { color(0xEAFBF2, 0x163629) }
    var onAccent: Color { color(0xFFFFFF, 0x10213D) }
    var disabled: Color { color(0xE4E7EC, 0x344054) }
    var onDisabled: Color { color(0x667085, 0xB8C4D4) }
}

@available(iOS 14.0, macOS 11.0, *)
private struct VisitPanelText: View {
    let value: String
    let size: CGFloat
    let weight: Font.Weight
    let color: Color
    @ScaledMetric(relativeTo: .body) private var scale: CGFloat = 1
    init(_ value: String, size: CGFloat = 14, weight: Font.Weight = .regular, color: Color) {
        self.value = value; self.size = size; self.weight = weight; self.color = color
    }
    var body: some View {
        Text(value)
            .font(.system(size: size * scale, weight: weight))
            .foregroundColor(color)
            .lineSpacing(3 * scale)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// A controlled panel. The caller supplies selection, consent, and all displayed visit data.
@available(iOS 14.0, macOS 11.0, *)
public struct VisitReschedulePanel: View {
    public let model: VisitRescheduleModel
    private let onAction: (VisitRescheduleAction) -> Void
    @Environment(\.colorScheme) private var colorScheme
    private var palette: VisitPalette { VisitPalette(dark: colorScheme == .dark) }
    private var effective: (group: VisitSlotGroup, slot: VisitSlot)? {
        guard model.mode == .choosing else { return nil }
        for group in model.groups {
            if let slot = group.slots.first(where: { $0.id == model.selectedSlotId && $0.availability != .unavailable }) {
                return (group, slot)
            }
        }
        return nil
    }
    public init(model: VisitRescheduleModel, onAction: @escaping (VisitRescheduleAction) -> Void) {
        self.model = model; self.onAction = onAction
    }
    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            sharedContext
            switch model.mode {
            case .loading:
                HStack(alignment: .center, spacing: 12) {
                    ProgressView().progressViewStyle(CircularProgressViewStyle(tint: palette.accent))
                    VisitPanelText("Checking available appointments…", color: palette.secondary)
                }
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.loading")
            case .unavailable:
                VStack(alignment: .leading, spacing: 8) {
                    VisitPanelText("No appointments available", size: 17, weight: .semibold, color: palette.primary)
                    if let message = model.unavailableMessage { VisitPanelText(message, color: palette.secondary) }
                }
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.unavailable")
                primary("Check again", identifier: "visit.retry") { onAction(.retry) }
            case .confirmed:
                if let confirmation = model.confirmation { success(confirmation) }
                primary("Done", identifier: "visit.done") { onAction(.done) }
            case .choosing:
                choices
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.panel)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("visit.panel")
    }
    private var sharedContext: some View {
        VStack(alignment: .leading, spacing: 12) {
            VisitPanelText(model.mode == .confirmed ? "Visit rescheduled" : "Reschedule visit",
                           size: 22, weight: .semibold, color: palette.primary)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("visit.title")
            VStack(alignment: .leading, spacing: 4) {
                VisitPanelText(model.serviceTitle, size: 17, weight: .semibold, color: palette.primary)
                    .accessibilityIdentifier("visit.service")
                VisitPanelText(model.location, color: palette.secondary)
                    .accessibilityIdentifier("visit.location")
            }
            appointmentCard(model.mode == .confirmed ? "Previous appointment" : "Current appointment",
                            appointment: model.currentAppointment)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.current")
        }
    }
    private func appointmentCard(_ title: String, appointment: VisitAppointment) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            VisitPanelText(title, size: 13, weight: .semibold, color: palette.secondary)
            VisitPanelText(appointment.dayLabel, size: 15, weight: .semibold, color: palette.primary)
            VisitPanelText(appointment.timeLabel, color: palette.secondary)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.inset)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
    private var choices: some View {
        VStack(alignment: .leading, spacing: 20) {
            ForEach(model.groups, id: \.id) { group in
                VStack(alignment: .leading, spacing: 10) {
                    VisitPanelText(group.dayLabel, size: 15, weight: .semibold, color: palette.primary)
                        .accessibilityAddTraits(.isHeader)
                        .accessibilityIdentifier("visit.group.\(group.id)")
                    ForEach(group.slots, id: \.id) { slot in
                        slotRow(group: group, slot: slot, selected: slot.id == effective?.slot.id)
                    }
                }
            }
            if let selected = effective {
                selectionSummary(group: selected.group, slot: selected.slot)
                if let fee = selected.slot.feeLabel {
                    Toggle(isOn: Binding(get: { model.feeAccepted }, set: { onAction(.setFeeAccepted($0)) })) {
                        VisitPanelText("I agree to the rescheduling fee of \(fee).", color: palette.primary)
                            .frame(minHeight: 44)
                    }
                    .toggleStyle(SwitchToggleStyle(tint: palette.accent))
                    .frame(minHeight: 44)
                    .accessibilityIdentifier("visit.fee_consent")
                }
            } else if model.selectedSlotId != nil {
                VisitPanelText("That appointment is no longer available. Choose another time.", color: palette.warning)
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(palette.warningFill)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .accessibilityIdentifier("visit.selection_warning")
            }
            if effective != nil || model.selectedSlotId == nil {
                VisitPanelText(guidance, color: palette.secondary)
                    .accessibilityIdentifier("visit.guidance")
            }
            primary("Confirm new time", identifier: "visit.confirm", enabled: canConfirm) {
                if let selected = effective { onAction(.confirm(selected.slot.id)) }
            }
        }
    }
    private var guidance: String {
        guard let selected = effective else { return "Choose one appointment to continue." }
        if selected.slot.feeLabel != nil && !model.feeAccepted { return "Agree to the fee to continue." }
        return "Your current time stays reserved until you confirm."
    }
    private var canConfirm: Bool {
        guard let selected = effective else { return false }
        return selected.slot.feeLabel == nil || model.feeAccepted
    }
    private func selectionSummary(group: VisitSlotGroup, slot: VisitSlot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            VisitPanelText("New appointment", size: 13, weight: .semibold, color: palette.secondary)
            VisitPanelText(group.dayLabel, size: 15, weight: .semibold, color: palette.primary)
            VisitPanelText(slot.timeLabel, color: palette.secondary)
            if let fee = slot.feeLabel {
                VisitPanelText("Rescheduling fee", color: palette.secondary).padding(.top, 4)
                VisitPanelText(fee, weight: .semibold, color: palette.primary)
            } else { VisitPanelText("No rescheduling fee", color: palette.secondary).padding(.top, 4) }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.inset)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("visit.selection_summary")
    }
    private func slotRow(group: VisitSlotGroup, slot: VisitSlot, selected: Bool) -> some View {
        let enabled = slot.availability != .unavailable
        let availability = slot.availability == .available ? "Available" : slot.availability == .limited ? "Few left" : "Unavailable"
        let fee = slot.feeLabel.map { "\($0) fee" } ?? "No fee"
        let label = [group.dayLabel, slot.timeLabel, slot.detail, availability,
                     enabled ? fee : slot.unavailableReason ?? ""].joined(separator: ", ")
        return Button(action: { if !selected { onAction(.selectSlot(slot.id)) } }) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle().stroke(selected ? palette.accent : palette.secondary, lineWidth: selected ? 2 : 1.5)
                    if selected { Circle().fill(palette.accent).padding(5) }
                }
                .frame(width: 20, height: 20)
                .padding(.top, 2)
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 8) {
                    VisitPanelText(slot.timeLabel, size: 17, weight: .semibold, color: enabled ? palette.primary : palette.secondary)
                    VisitPanelText(slot.detail, color: palette.secondary)
                    VisitPanelText(enabled ? "\(availability) · \(fee)" : availability, size: 13, color: palette.secondary)
                    if !enabled, let reason = slot.unavailableReason {
                        VisitPanelText(reason, size: 13, color: palette.secondary)
                    }
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .background(selected ? palette.selected : enabled ? palette.panel : palette.inset)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? palette.accent : palette.border, lineWidth: selected ? 2 : 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(VisitUnfadedButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(label))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("visit.slot.\(slot.id)")
    }
    private func success(_ confirmation: VisitConfirmation) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "checkmark.circle.fill").foregroundColor(palette.success).accessibilityHidden(true)
                VisitPanelText("New appointment confirmed", size: 17, weight: .semibold, color: palette.success)
            }
            VisitPanelText(confirmation.appointment.dayLabel, size: 15, weight: .semibold, color: palette.primary)
            VisitPanelText(confirmation.appointment.timeLabel, color: palette.primary)
            VisitPanelText("Reference: \(confirmation.reference)", color: palette.primary)
                .accessibilityIdentifier("visit.reference")
            VisitPanelText(confirmation.note, color: palette.secondary)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.successFill)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("visit.confirmation")
    }
    private func primary(_ title: String, identifier: String, enabled: Bool = true, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VisitPrimaryLabel(title: title, foreground: enabled ? palette.onAccent : palette.onDisabled)
                .padding(.horizontal, 16).padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .background(enabled ? palette.accent : palette.disabled)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(VisitUnfadedButtonStyle())
        .disabled(!enabled)
        .accessibilityIdentifier(identifier)
    }
}

@available(iOS 14.0, macOS 11.0, *)
private struct VisitPrimaryLabel: View {
    let title: String
    let foreground: Color
    @ScaledMetric(relativeTo: .body) private var fontSize: CGFloat = 16
    var body: some View {
        Text(title).font(.system(size: fontSize, weight: .semibold))
            .foregroundColor(foreground).multilineTextAlignment(.center)
            .lineSpacing(3).fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity)
    }
}

@available(iOS 14.0, macOS 11.0, *)
private struct VisitUnfadedButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}
