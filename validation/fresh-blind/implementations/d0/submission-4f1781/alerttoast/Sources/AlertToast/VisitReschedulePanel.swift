import SwiftUI

private struct VisitPalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let value = dark ? darkValue : light
        return Color(red: Double((value >> 16) & 255) / 255,
                     green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255)
    }
    var panel: Color { color(0xFFFFFF, 0x161C27) }
    var text: Color { color(0x182230, 0xF2F4F7) }
    var secondary: Color { color(0x526174, 0xB8C4D4) }
    var inset: Color { color(0xF4F6F9, 0x202938) }
    var border: Color { color(0xD5DDE7, 0x485568) }
    var accent: Color { color(0x175CD3, 0x84ADFF) }
    var selection: Color { color(0xEFF6FF, 0x162F51) }
    var warningText: Color { color(0x854A0E, 0xFFD691) }
    var warningFill: Color { color(0xFFF7E0, 0x3B2D17) }
    var successText: Color { color(0x087443, 0x75E0AD) }
    var successFill: Color { color(0xEAFBF2, 0x163629) }
    var onPrimary: Color { color(0xFFFFFF, 0x10213D) }
    var disabled: Color { color(0xE4E7EC, 0x344054) }
    var onDisabled: Color { color(0x667085, 0xB8C4D4) }
}

@available(iOS 14, macOS 11, *)
private struct VisitText: View {
    let value: String
    let color: Color
    let weight: Font.Weight
    let line: CGFloat
    let base: CGFloat
    @ScaledMetric(relativeTo: .body) private var size: CGFloat = 14
    init(_ value: String, color: Color, size: CGFloat = 14, line: CGFloat = 20, weight: Font.Weight = .regular) {
        self.value = value
        self.color = color
        self.weight = weight
        self.line = line
        self.base = size
        _size = ScaledMetric(wrappedValue: size, relativeTo: .body)
    }
    var body: some View {
        Text(verbatim: value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color)
            .lineSpacing(max(0, line - base * 1.2) * size / base)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
    }
}

@available(iOS 14, macOS 11, *)
public struct VisitReschedulePanel: View {
    public let model: VisitRescheduleModel
    private let onAction: (VisitRescheduleAction) -> Void
    @Environment(\.colorScheme) private var colorScheme
    public init(model: VisitRescheduleModel, onAction: @escaping (VisitRescheduleAction) -> Void) {
        self.model = model
        self.onAction = onAction
    }
    private var palette: VisitPalette { VisitPalette(dark: colorScheme == .dark) }
    private var effectiveSelection: (VisitSlotGroup, VisitSlot)? {
        guard model.mode == .choosing, let id = model.selectedSlotId else { return nil }
        for group in model.groups {
            if let slot = group.slots.first(where: { $0.id == id && $0.availability != .unavailable }) {
                return (group, slot)
            }
        }
        return nil
    }
    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                VisitText(model.mode == .confirmed ? "Visit rescheduled" : "Reschedule visit",
                          color: palette.text, size: 22, line: 28, weight: .semibold)
                    .accessibilityIdentifier("visit.title")
                VStack(alignment: .leading, spacing: 8) {
                    VisitText(model.serviceTitle, color: palette.text, size: 17, line: 23, weight: .semibold)
                        .accessibilityIdentifier("visit.service")
                    VisitText(model.location, color: palette.secondary)
                        .accessibilityIdentifier("visit.location")
                }
            }
            appointmentCard(label: model.mode == .confirmed ? "Previous appointment" : "Current appointment",
                            appointment: model.currentAppointment)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.current")
            stateContent
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(palette.panel)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .accessibilityIdentifier("visit.panel")
    }

    @ViewBuilder private var stateContent: some View {
        switch model.mode {
        case .loading:
            HStack(alignment: .center, spacing: 12) {
                ProgressView().progressViewStyle(CircularProgressViewStyle(tint: palette.accent))
                VisitText("Checking available appointments…", color: palette.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("visit.loading")
        case .unavailable:
            VStack(alignment: .leading, spacing: 8) {
                VisitText("No appointments available", color: palette.text, size: 17, line: 23, weight: .semibold)
                if let message = model.unavailableMessage {
                    VisitText(message, color: palette.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(palette.inset)
            .cornerRadius(12)
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("visit.unavailable")
            primaryButton("Check again", id: "visit.retry", enabled: true) { onAction(.retry) }
        case .confirmed:
            if let confirmation = model.confirmation {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Image(systemName: "checkmark.circle.fill").foregroundColor(palette.successText).accessibilityHidden(true)
                        VisitText("New appointment confirmed", color: palette.successText, size: 17, line: 23, weight: .semibold)
                    }
                    VisitText(confirmation.appointment.dayLabel, color: palette.text, size: 15, line: 20, weight: .semibold)
                    VisitText(confirmation.appointment.timeLabel, color: palette.text)
                    VisitText("Reference: " + confirmation.reference, color: palette.successText)
                        .accessibilityIdentifier("visit.reference")
                    VisitText(confirmation.note, color: palette.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(palette.successFill)
                .cornerRadius(12)
                .accessibilityIdentifier("visit.confirmation")
            }
            primaryButton("Done", id: "visit.done", enabled: true) { onAction(.done) }
        case .choosing:
            chooser
        }
    }

    @ViewBuilder private var chooser: some View {
        VStack(alignment: .leading, spacing: 20) {
            ForEach(model.groups, id: \.id) { group in
                VStack(alignment: .leading, spacing: 10) {
                    VisitText(group.dayLabel, color: palette.text, size: 15, line: 20, weight: .semibold)
                        .accessibilityAddTraits(.isHeader)
                        .accessibilityIdentifier("visit.group." + group.id)
                    ForEach(group.slots, id: \.id) { slot in
                        slotRow(group: group, slot: slot)
                    }
                }
            }
        }
        if let (group, slot) = effectiveSelection {
            appointmentCard(label: "New appointment", appointment: VisitAppointment(dayLabel: group.dayLabel, timeLabel: slot.timeLabel),
                            showsFee: true, fee: slot.feeLabel)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.selection_summary")
            if let fee = slot.feeLabel {
                Toggle(isOn: Binding(get: { model.feeAccepted }, set: { value in onAction(.setFeeAccepted(value)) })) {
                    VisitText("I agree to the rescheduling fee of " + fee + ".", color: palette.text)
                }
                .toggleStyle(SwitchToggleStyle(tint: palette.accent))
                .frame(minHeight: 44)
                .accessibilityIdentifier("visit.fee_consent")
            }
        } else if model.selectedSlotId != nil {
            VisitText("That appointment is no longer available. Choose another time.", color: palette.warningText)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(palette.warningFill)
                .cornerRadius(12)
                .accessibilityIdentifier("visit.selection_warning")
        }
        if effectiveSelection != nil || model.selectedSlotId == nil {
            VisitText(guidance, color: palette.secondary)
                .accessibilityIdentifier("visit.guidance")
        }
        primaryButton("Confirm new time", id: "visit.confirm", enabled: canConfirm) {
            if let (_, slot) = effectiveSelection, canConfirm { onAction(.confirm(slot.id)) }
        }
    }

    private var canConfirm: Bool {
        guard let (_, slot) = effectiveSelection else { return false }
        return slot.feeLabel == nil || model.feeAccepted
    }
    private var guidance: String {
        guard let (_, slot) = effectiveSelection else { return "Choose one appointment to continue." }
        if slot.feeLabel != nil && !model.feeAccepted { return "Agree to the fee to continue." }
        return "Your current time stays reserved until you confirm."
    }
    private func appointmentCard(label: String, appointment: VisitAppointment,
                                 showsFee: Bool = false, fee: String? = nil) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            VisitText(label, color: palette.secondary, size: 13, line: 18, weight: .semibold)
            VisitText(appointment.dayLabel, color: palette.text, size: 15, line: 20, weight: .semibold)
            VisitText(appointment.timeLabel, color: palette.secondary)
            if showsFee {
                VisitText(fee.map { "Rescheduling fee  " + $0 } ?? "No rescheduling fee", color: palette.text)
                    .padding(.top, 6)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(palette.inset)
        .cornerRadius(12)
    }

    private func slotRow(group: VisitSlotGroup, slot: VisitSlot) -> some View {
        let eligible = slot.availability != .unavailable
        let selected = effectiveSelection?.1.id == slot.id
        let availability = slot.availability == .available ? "Available" : slot.availability == .limited ? "Few left" : "Unavailable"
        let metadata = eligible ? availability + " · " + (slot.feeLabel.map { $0 + " fee" } ?? "No fee") : availability
        let label = [group.dayLabel, slot.timeLabel, slot.detail, metadata, eligible ? nil : slot.unavailableReason]
            .compactMap { $0 }.joined(separator: ", ")
        return Button(action: {
            if eligible && !selected { onAction(.selectSlot(slot.id)) }
        }) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle().stroke(selected ? palette.accent : palette.secondary, lineWidth: selected ? 2 : 1.5)
                    if selected { Circle().fill(palette.accent).frame(width: 10, height: 10) }
                }
                .frame(width: 20, height: 20)
                .padding(.top, 1)
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 6) {
                    VisitText(slot.timeLabel, color: eligible ? palette.text : palette.secondary, size: 17, line: 23, weight: .semibold)
                    VisitText(slot.detail, color: palette.secondary)
                    VStack(alignment: .leading, spacing: 2) {
                        VisitText(metadata, color: palette.secondary, size: 13, line: 18)
                        if !eligible, let reason = slot.unavailableReason {
                            VisitText(reason, color: palette.secondary, size: 13, line: 18)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxWidth: .infinity, minHeight: 24, alignment: .leading)
            .padding(12)
            .background(selected ? palette.selection : eligible ? palette.panel : palette.inset)
            .cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? palette.accent : palette.border,
                                                                       lineWidth: selected ? 2 : 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!eligible)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(verbatim: label))
        .accessibilityAddTraits(selected ? [.isSelected] : [])
        .accessibilityIdentifier("visit.slot." + slot.id)
    }

    private func primaryButton(_ title: String, id: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VisitText(title, color: enabled ? palette.onPrimary : palette.onDisabled, size: 16, line: 22, weight: .semibold)
                .frame(maxWidth: .infinity)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(minHeight: 48)
                .background(enabled ? palette.accent : palette.disabled)
                .cornerRadius(12)
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityIdentifier(id)
    }
}
