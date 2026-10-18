package com.example.reply.ui.components

enum class VisitRescheduleMode { Loading, Choosing, Unavailable, Confirmed }
enum class VisitSlotAvailability { Available, Limited, Unavailable }

data class VisitAppointment(val dayLabel: String, val timeLabel: String)
data class VisitSlot(
    val id: String,
    val timeLabel: String,
    val detail: String,
    val availability: VisitSlotAvailability,
    val feeLabel: String? = null,
    val unavailableReason: String? = null,
)
data class VisitSlotGroup(val id: String, val dayLabel: String, val slots: List<VisitSlot> = emptyList())
data class VisitConfirmation(val appointment: VisitAppointment, val reference: String, val note: String)
data class VisitRescheduleModel(
    val mode: VisitRescheduleMode,
    val serviceTitle: String,
    val location: String,
    val currentAppointment: VisitAppointment,
    val groups: List<VisitSlotGroup> = emptyList(),
    val selectedSlotId: String? = null,
    val feeAccepted: Boolean,
    val unavailableMessage: String? = null,
    val confirmation: VisitConfirmation? = null,
)
sealed class VisitRescheduleAction {
    data class SelectSlot(val slotId: String) : VisitRescheduleAction()
    data class SetFeeAccepted(val accepted: Boolean) : VisitRescheduleAction()
    data class Confirm(val slotId: String) : VisitRescheduleAction()
    object Retry : VisitRescheduleAction()
    object Done : VisitRescheduleAction()
}
