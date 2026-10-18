import SwiftUI

public enum VisitRescheduleMode: String, Codable {
    case loading, choosing, unavailable, confirmed
}

public enum VisitSlotAvailability: String, Codable {
    case available, limited, unavailable
}

public struct VisitAppointment: Codable {
    public var dayLabel: String
    public var timeLabel: String

    public init(dayLabel: String, timeLabel: String) {
        self.dayLabel = dayLabel
        self.timeLabel = timeLabel
    }
}

public struct VisitSlot: Codable {
    public var id: String
    public var timeLabel: String
    public var detail: String
    public var availability: VisitSlotAvailability
    public var feeLabel: String?
    public var unavailableReason: String?

    public init(id: String, timeLabel: String, detail: String,
                availability: VisitSlotAvailability, feeLabel: String? = nil,
                unavailableReason: String? = nil) {
        self.id = id
        self.timeLabel = timeLabel
        self.detail = detail
        self.availability = availability
        self.feeLabel = feeLabel
        self.unavailableReason = unavailableReason
    }
}

public struct VisitSlotGroup: Codable {
    public var id: String
    public var dayLabel: String
    public var slots: [VisitSlot]

    public init(id: String, dayLabel: String, slots: [VisitSlot] = []) {
        self.id = id
        self.dayLabel = dayLabel
        self.slots = slots
    }

    private enum CodingKeys: String, CodingKey { case id, dayLabel, slots }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        dayLabel = try container.decode(String.self, forKey: .dayLabel)
        slots = try container.decodeIfPresent([VisitSlot].self, forKey: .slots) ?? []
    }
}

public struct VisitConfirmation: Codable {
    public var appointment: VisitAppointment
    public var reference: String
    public var note: String

    public init(appointment: VisitAppointment, reference: String, note: String) {
        self.appointment = appointment
        self.reference = reference
        self.note = note
    }
}

public struct VisitRescheduleModel: Codable {
    public var mode: VisitRescheduleMode
    public var serviceTitle: String
    public var location: String
    public var currentAppointment: VisitAppointment
    public var groups: [VisitSlotGroup]
    public var selectedSlotId: String?
    public var feeAccepted: Bool
    public var unavailableMessage: String?
    public var confirmation: VisitConfirmation?

    public init(mode: VisitRescheduleMode, serviceTitle: String, location: String,
                currentAppointment: VisitAppointment, groups: [VisitSlotGroup] = [],
                selectedSlotId: String? = nil, feeAccepted: Bool,
                unavailableMessage: String? = nil, confirmation: VisitConfirmation? = nil) {
        self.mode = mode
        self.serviceTitle = serviceTitle
        self.location = location
        self.currentAppointment = currentAppointment
        self.groups = groups
        self.selectedSlotId = selectedSlotId
        self.feeAccepted = feeAccepted
        self.unavailableMessage = unavailableMessage
        self.confirmation = confirmation
    }

    private enum CodingKeys: String, CodingKey {
        case mode, serviceTitle, location, currentAppointment, groups, selectedSlotId
        case feeAccepted, unavailableMessage, confirmation
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        mode = try container.decode(VisitRescheduleMode.self, forKey: .mode)
        serviceTitle = try container.decode(String.self, forKey: .serviceTitle)
        location = try container.decode(String.self, forKey: .location)
        currentAppointment = try container.decode(VisitAppointment.self, forKey: .currentAppointment)
        groups = try container.decodeIfPresent([VisitSlotGroup].self, forKey: .groups) ?? []
        selectedSlotId = try container.decodeIfPresent(String.self, forKey: .selectedSlotId)
        feeAccepted = try container.decode(Bool.self, forKey: .feeAccepted)
        unavailableMessage = try container.decodeIfPresent(String.self, forKey: .unavailableMessage)
        confirmation = try container.decodeIfPresent(VisitConfirmation.self, forKey: .confirmation)
    }
}

public enum VisitRescheduleAction {
    case selectSlot(String)
    case setFeeAccepted(Bool)
    case confirm(String)
    case retry
    case done
}

private struct VisitColors {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let value = dark ? darkValue : light
        return Color(red: Double((value >> 16) & 255) / 255,
                     green: Double((value >> 8) & 255) / 255,
                     blue: Double(value & 255) / 255)
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
    var buttonText: Color { color(0xFFFFFF, 0x10213D) }
    var disabledFill: Color { color(0xE4E7EC, 0x344054) }
    var disabledText: Color { color(0x667085, 0xB8C4D4) }
}

@available(iOS 14, macOS 11, *)
private struct VisitText: View {
    let text: String
    let color: Color
    var size: CGFloat = 14
    var weight: Font.Weight = .regular
    @ScaledMetric(relativeTo: .body) private var fontScale: CGFloat = 1

    private var lineHeight: CGFloat {
        switch size {
        case 22: return 28
        case 17: return 23
        case 16: return 22
        case 13: return 18
        default: return 20
        }
    }

    var body: some View {
        Text(text)
            .font(.system(size: size * fontScale, weight: weight))
            .lineSpacing(max(0, lineHeight - size * 1.2) * fontScale)
            .foregroundColor(color)
            .fixedSize(horizontal: false, vertical: true)
            .multilineTextAlignment(.leading)
            .frame(minHeight: lineHeight * fontScale, alignment: .leading)
    }
}

@available(iOS 14, macOS 11, *)
private struct VisitButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.opacity(configuration.isPressed ? 0.88 : 1)
    }
}

@available(iOS 14, macOS 11, *)
public struct VisitReschedulePanel: View {
    public let model: VisitRescheduleModel
    public let onAction: (VisitRescheduleAction) -> Void
    @Environment(\.colorScheme) private var colorScheme

    public init(model: VisitRescheduleModel,
                onAction: @escaping (VisitRescheduleAction) -> Void) {
        self.model = model
        self.onAction = onAction
    }

    private var colors: VisitColors { VisitColors(dark: colorScheme == .dark) }
    private var selection: (group: VisitSlotGroup, slot: VisitSlot)? {
        guard model.mode == .choosing, let selectedID = model.selectedSlotId else { return nil }
        for group in model.groups {
            if let slot = group.slots.first(where: { $0.id == selectedID && $0.availability != .unavailable }) {
                return (group, slot)
            }
        }
        return nil
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            context
            switch model.mode {
            case .loading:
                HStack(alignment: .center, spacing: 12) {
                    ProgressView().progressViewStyle(CircularProgressViewStyle(tint: colors.accent))
                    VisitText(text: "Checking available appointments…", color: colors.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.loading")
            case .choosing:
                choices
            case .unavailable:
                VStack(alignment: .leading, spacing: 8) {
                    VisitText(text: "No appointments available", color: colors.primary, size: 17, weight: .semibold)
                    if let message = model.unavailableMessage {
                        VisitText(text: message, color: colors.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("visit.unavailable")
                primaryButton("Check again", id: "visit.retry", enabled: true) { onAction(.retry) }
            case .confirmed:
                if let confirmation = model.confirmation {
                    confirmationCard(confirmation)
                }
                primaryButton("Done", id: "visit.done", enabled: true) { onAction(.done) }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 20).fill(colors.panel))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("visit.panel")
    }

    private var context: some View {
        VStack(alignment: .leading, spacing: 16) {
            VisitText(text: model.mode == .confirmed ? "Visit rescheduled" : "Reschedule visit",
                      color: colors.primary, size: 22, weight: .semibold)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("visit.title")
            VStack(alignment: .leading, spacing: 4) {
                VisitText(text: model.serviceTitle, color: colors.primary, size: 17, weight: .semibold)
                    .accessibilityIdentifier("visit.service")
                VisitText(text: model.location, color: colors.secondary)
                    .accessibilityIdentifier("visit.location")
            }
            VStack(alignment: .leading, spacing: 6) {
                VisitText(text: model.mode == .confirmed ? "Previous appointment" : "Current appointment",
                          color: colors.secondary, size: 13, weight: .semibold)
                VisitText(text: model.currentAppointment.dayLabel, color: colors.primary, size: 15, weight: .semibold)
                VisitText(text: model.currentAppointment.timeLabel, color: colors.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(RoundedRectangle(cornerRadius: 12).fill(colors.inset))
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("visit.current")
        }
    }

    private var choices: some View {
        Group {
            VStack(alignment: .leading, spacing: 20) {
                ForEach(model.groups, id: \.id) { group in
                    VStack(alignment: .leading, spacing: 10) {
                        VisitText(text: group.dayLabel, color: colors.primary, size: 15, weight: .semibold)
                            .accessibilityAddTraits(.isHeader)
                            .accessibilityIdentifier("visit.group.\(group.id)")
                        ForEach(group.slots, id: \.id) { slot in
                            slotRow(group: group, slot: slot)
                        }
                    }
                }
            }
            if let effective = selection {
                selectionSummary(group: effective.group, slot: effective.slot)
                if let fee = effective.slot.feeLabel {
                    Toggle(isOn: Binding(get: { model.feeAccepted }, set: { _ in
                        onAction(.setFeeAccepted(!model.feeAccepted))
                    })) {
                        VisitText(text: "I agree to the rescheduling fee of \(fee).", color: colors.primary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .toggleStyle(SwitchToggleStyle(tint: colors.accent))
                    .frame(minHeight: 44)
                    .accessibilityIdentifier("visit.fee_consent")
                }
            } else if model.selectedSlotId != nil {
                VisitText(text: "That appointment is no longer available. Choose another time.", color: colors.warning)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(12)
                    .background(RoundedRectangle(cornerRadius: 12).fill(colors.warningFill))
                    .accessibilityIdentifier("visit.selection_warning")
            }
            if let guidance = guidance {
                VisitText(text: guidance, color: colors.secondary)
                    .accessibilityIdentifier("visit.guidance")
            }
            primaryButton("Confirm new time", id: "visit.confirm", enabled: canConfirm) {
                if let effective = selection { onAction(.confirm(effective.slot.id)) }
            }
        }
    }

    private var guidance: String? {
        guard let selected = selection else {
            return model.selectedSlotId == nil ? "Choose one appointment to continue." : nil
        }
        if selected.slot.feeLabel != nil && !model.feeAccepted { return "Agree to the fee to continue." }
        return "Your current time stays reserved until you confirm."
    }

    private var canConfirm: Bool {
        guard let selected = selection else { return false }
        return selected.slot.feeLabel == nil || model.feeAccepted
    }

    private func slotRow(group: VisitSlotGroup, slot: VisitSlot) -> some View {
        let enabled = slot.availability != .unavailable
        let selected = selection?.slot.id == slot.id
        let availability: String
        switch slot.availability {
        case .available: availability = "Available"
        case .limited: availability = "Few left"
        case .unavailable: availability = "Unavailable"
        }
        let metadata = enabled ? (slot.feeLabel.map { "\($0) fee" } ?? "No fee") : (slot.unavailableReason ?? "")
        let label = "\(group.dayLabel), \(slot.timeLabel), \(slot.detail), \(availability), \(metadata)"
        return Button(action: {
            if enabled && !selected { onAction(.selectSlot(slot.id)) }
        }) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle().stroke(selected ? colors.accent : colors.secondary, lineWidth: selected ? 2 : 1.5)
                    if selected { Circle().fill(colors.accent).frame(width: 10, height: 10) }
                }
                .frame(width: 20, height: 20)
                .padding(.top, 1)
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 6) {
                    VisitText(text: slot.timeLabel, color: enabled ? colors.primary : colors.secondary, size: 17, weight: .semibold)
                    VisitText(text: slot.detail, color: colors.secondary)
                    VisitText(text: enabled ? "\(availability) · \(metadata)" : availability, color: colors.secondary, size: 13)
                    if !enabled { VisitText(text: metadata, color: colors.secondary, size: 13) }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxWidth: .infinity, minHeight: 24, alignment: .leading)
            .padding(12)
            .background(RoundedRectangle(cornerRadius: 12).fill(selected ? colors.selected : (enabled ? colors.panel : colors.inset)))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected ? colors.accent : colors.border, lineWidth: selected ? 2 : 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(VisitButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(label))
        .accessibilityAddTraits(selected ? [.isSelected] : [])
        .accessibilityIdentifier("visit.slot.\(slot.id)")
    }

    private func selectionSummary(group: VisitSlotGroup, slot: VisitSlot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            VisitText(text: "New appointment", color: colors.secondary, size: 13, weight: .semibold)
            VisitText(text: group.dayLabel, color: colors.primary, size: 15, weight: .semibold)
            VisitText(text: slot.timeLabel, color: colors.secondary)
            if let fee = slot.feeLabel {
                HStack(alignment: .top, spacing: 12) {
                    VisitText(text: "Rescheduling fee", color: colors.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    VisitText(text: fee, color: colors.primary, weight: .semibold)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                }
            } else {
                VisitText(text: "No rescheduling fee", color: colors.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 12).fill(colors.inset))
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("visit.selection_summary")
    }

    private func confirmationCard(_ confirmation: VisitConfirmation) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "checkmark.circle.fill").foregroundColor(colors.success).accessibilityHidden(true)
                VisitText(text: "New appointment confirmed", color: colors.success, size: 17, weight: .semibold)
            }
            VisitText(text: confirmation.appointment.dayLabel, color: colors.primary, size: 15, weight: .semibold)
            VisitText(text: confirmation.appointment.timeLabel, color: colors.primary)
            VisitText(text: "Reference: \(confirmation.reference)", color: colors.success)
                .accessibilityIdentifier("visit.reference")
            VisitText(text: confirmation.note, color: colors.primary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 12).fill(colors.successFill))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("visit.confirmation")
    }

    private func primaryButton(_ label: String, id: String, enabled: Bool,
                               action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VisitText(text: label, color: enabled ? colors.buttonText : colors.disabledText, size: 16, weight: .semibold)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(minHeight: 48)
                .background(RoundedRectangle(cornerRadius: 12).fill(enabled ? colors.accent : colors.disabledFill))
                .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(VisitButtonStyle())
        .disabled(!enabled)
        .accessibilityIdentifier(id)
    }
}
