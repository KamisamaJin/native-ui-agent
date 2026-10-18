import Foundation

public enum VisitRescheduleMode: String, Codable { case loading, choosing, unavailable, confirmed }
public enum VisitSlotAvailability: String, Codable { case available, limited, unavailable }

public struct VisitAppointment: Codable {
    public var dayLabel: String
    public var timeLabel: String
    public init(dayLabel: String, timeLabel: String) {
        self.dayLabel = dayLabel; self.timeLabel = timeLabel
    }
}

public struct VisitSlot: Codable {
    public var id: String
    public var timeLabel: String
    public var detail: String
    public var availability: VisitSlotAvailability
    public var feeLabel: String?
    public var unavailableReason: String?
    public init(id: String, timeLabel: String, detail: String, availability: VisitSlotAvailability,
                feeLabel: String? = nil, unavailableReason: String? = nil) {
        self.id = id; self.timeLabel = timeLabel; self.detail = detail
        self.availability = availability; self.feeLabel = feeLabel; self.unavailableReason = unavailableReason
    }
}

public struct VisitSlotGroup: Codable {
    public var id: String
    public var dayLabel: String
    public var slots: [VisitSlot]
    public init(id: String, dayLabel: String, slots: [VisitSlot] = []) {
        self.id = id; self.dayLabel = dayLabel; self.slots = slots
    }
    private enum CodingKeys: String, CodingKey { case id, dayLabel, slots }
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        id = try values.decode(String.self, forKey: .id)
        dayLabel = try values.decode(String.self, forKey: .dayLabel)
        slots = try values.decodeIfPresent([VisitSlot].self, forKey: .slots) ?? []
    }
}

public struct VisitConfirmation: Codable {
    public var appointment: VisitAppointment
    public var reference: String
    public var note: String
    public init(appointment: VisitAppointment, reference: String, note: String) {
        self.appointment = appointment; self.reference = reference; self.note = note
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
        self.mode = mode; self.serviceTitle = serviceTitle; self.location = location
        self.currentAppointment = currentAppointment; self.groups = groups
        self.selectedSlotId = selectedSlotId; self.feeAccepted = feeAccepted
        self.unavailableMessage = unavailableMessage; self.confirmation = confirmation
    }
    private enum CodingKeys: String, CodingKey {
        case mode, serviceTitle, location, currentAppointment, groups, selectedSlotId, feeAccepted, unavailableMessage, confirmation
    }
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        mode = try values.decode(VisitRescheduleMode.self, forKey: .mode)
        serviceTitle = try values.decode(String.self, forKey: .serviceTitle)
        location = try values.decode(String.self, forKey: .location)
        currentAppointment = try values.decode(VisitAppointment.self, forKey: .currentAppointment)
        groups = try values.decodeIfPresent([VisitSlotGroup].self, forKey: .groups) ?? []
        selectedSlotId = try values.decodeIfPresent(String.self, forKey: .selectedSlotId)
        feeAccepted = try values.decode(Bool.self, forKey: .feeAccepted)
        unavailableMessage = try values.decodeIfPresent(String.self, forKey: .unavailableMessage)
        confirmation = try values.decodeIfPresent(VisitConfirmation.self, forKey: .confirmation)
    }
}

public enum VisitRescheduleAction {
    case selectSlot(String)
    case setFeeAccepted(Bool)
    case confirm(String)
    case retry
    case done
}
