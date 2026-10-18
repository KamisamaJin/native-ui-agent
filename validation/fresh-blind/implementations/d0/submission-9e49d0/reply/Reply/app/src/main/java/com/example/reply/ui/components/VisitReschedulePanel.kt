package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

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

private data class VisitPalette(
    val panel: Color, val primary: Color, val secondary: Color, val inset: Color,
    val border: Color, val accent: Color, val selected: Color,
    val warning: Color, val warningFill: Color, val success: Color, val successFill: Color,
    val buttonText: Color, val disabledFill: Color, val disabledText: Color,
)

@Composable
private fun visitPalette(): VisitPalette = if (isSystemInDarkTheme()) VisitPalette(
    Color(0xFF161C27), Color(0xFFF2F4F7), Color(0xFFB8C4D4), Color(0xFF202938),
    Color(0xFF485568), Color(0xFF84ADFF), Color(0xFF162F51), Color(0xFFFFD691),
    Color(0xFF3B2D17), Color(0xFF75E0AD), Color(0xFF163629), Color(0xFF10213D),
    Color(0xFF344054), Color(0xFFB8C4D4),
) else VisitPalette(
    Color(0xFFFFFFFF), Color(0xFF182230), Color(0xFF526174), Color(0xFFF4F6F9),
    Color(0xFFD5DDE7), Color(0xFF175CD3), Color(0xFFEFF6FF), Color(0xFF854A0E),
    Color(0xFFFFF7E0), Color(0xFF087443), Color(0xFFEAFBF2), Color.White,
    Color(0xFFE4E7EC), Color(0xFF667085),
)

@Composable
private fun VisitText(
    value: String,
    color: Color,
    modifier: Modifier = Modifier,
    size: Int = 14,
    line: Int = 20,
    weight: FontWeight = FontWeight.Normal,
) {
    Text(value, modifier = modifier, color = color,
        style = TextStyle(fontSize = size.sp, lineHeight = line.sp, fontWeight = weight))
}

@Composable
fun VisitReschedulePanel(
    model: VisitRescheduleModel,
    onAction: (VisitRescheduleAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = visitPalette()
    Column(
        modifier.fillMaxWidth().testTag("visit.panel")
            .background(colors.panel, RoundedCornerShape(20.dp)).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            VisitText(if (model.mode == VisitRescheduleMode.Confirmed) "Visit rescheduled" else "Reschedule visit",
                colors.primary, Modifier.testTag("visit.title").semantics { heading() }, 22, 28, FontWeight.SemiBold)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                VisitText(model.serviceTitle, colors.primary, Modifier.testTag("visit.service"), 17, 23, FontWeight.SemiBold)
                VisitText(model.location, colors.secondary, Modifier.testTag("visit.location"))
            }
            VisitAppointmentCard(
                if (model.mode == VisitRescheduleMode.Confirmed) "Previous appointment" else "Current appointment",
                model.currentAppointment, colors, Modifier.testTag("visit.current"),
            )
        }
        when (model.mode) {
            VisitRescheduleMode.Loading -> Row(
                Modifier.fillMaxWidth().testTag("visit.loading").semantics(mergeDescendants = true) {},
                horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(Modifier.size(20.dp), color = colors.accent, strokeWidth = 2.dp)
                VisitText("Checking available appointments…", colors.secondary, Modifier.weight(1f))
            }
            VisitRescheduleMode.Unavailable -> {
                Column(Modifier.fillMaxWidth().testTag("visit.unavailable"), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    VisitText("No appointments available", colors.primary, size = 17, line = 23, weight = FontWeight.SemiBold)
                    model.unavailableMessage?.let { VisitText(it, colors.secondary) }
                }
                VisitPrimaryButton("Check again", "visit.retry", true, colors) { onAction(VisitRescheduleAction.Retry) }
            }
            VisitRescheduleMode.Confirmed -> {
                model.confirmation?.let { confirmation ->
                    Column(Modifier.fillMaxWidth().testTag("visit.confirmation")
                        .background(colors.successFill, RoundedCornerShape(12.dp)).padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        VisitText("✓  New appointment confirmed", colors.success, size = 17, line = 23, weight = FontWeight.SemiBold)
                        VisitText(confirmation.appointment.dayLabel, colors.primary, size = 15, weight = FontWeight.SemiBold)
                        VisitText(confirmation.appointment.timeLabel, colors.primary)
                        VisitText("Reference: ${confirmation.reference}", colors.success, Modifier.testTag("visit.reference"))
                        VisitText(confirmation.note, colors.primary)
                    }
                }
                VisitPrimaryButton("Done", "visit.done", true, colors) { onAction(VisitRescheduleAction.Done) }
            }
            VisitRescheduleMode.Choosing -> VisitChoices(model, colors, onAction)
        }
    }
}

@Composable
private fun VisitAppointmentCard(label: String, appointment: VisitAppointment, colors: VisitPalette, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth().background(colors.inset, RoundedCornerShape(12.dp)).padding(12.dp)
        .semantics(mergeDescendants = true) {}, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        VisitText(label, colors.secondary, size = 13, line = 18, weight = FontWeight.SemiBold)
        VisitText(appointment.dayLabel, colors.primary, size = 15, weight = FontWeight.SemiBold)
        VisitText(appointment.timeLabel, colors.secondary)
    }
}

@Composable
private fun VisitChoices(model: VisitRescheduleModel, colors: VisitPalette, onAction: (VisitRescheduleAction) -> Unit) {
    val effective = model.groups.firstNotNullOfOrNull { group ->
        group.slots.firstOrNull { it.id == model.selectedSlotId && it.availability != VisitSlotAvailability.Unavailable }
            ?.let { group to it }
    }
    Column(Modifier.fillMaxWidth().selectableGroup(), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        model.groups.forEach { group ->
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                VisitText(group.dayLabel, colors.primary,
                    Modifier.testTag("visit.group.${group.id}").semantics { heading() }, 15, 20, FontWeight.SemiBold)
                group.slots.forEach { slot ->
                    VisitSlotRow(group, slot, effective?.second?.id == slot.id, colors, onAction)
                }
            }
        }
    }
    if (effective != null) {
        val (group, slot) = effective
        Column(Modifier.fillMaxWidth().testTag("visit.selection_summary")
            .background(colors.inset, RoundedCornerShape(12.dp)).padding(12.dp)
            .semantics(mergeDescendants = true) {}, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            VisitText("New appointment", colors.secondary, size = 13, line = 18, weight = FontWeight.SemiBold)
            VisitText(group.dayLabel, colors.primary, size = 15, weight = FontWeight.SemiBold)
            VisitText(slot.timeLabel, colors.secondary)
            if (slot.feeLabel == null) VisitText("No rescheduling fee", colors.secondary)
            else {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.Top) {
                    VisitText("Rescheduling fee", colors.secondary, Modifier.weight(1f))
                    Column(Modifier.weight(1f), horizontalAlignment = Alignment.End) {
                        VisitText(slot.feeLabel, colors.primary, weight = FontWeight.SemiBold)
                    }
                }
            }
        }
        slot.feeLabel?.let { fee ->
            val label = "I agree to the rescheduling fee of $fee."
            Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("visit.fee_consent")
                .toggleable(value = model.feeAccepted, role = Role.Checkbox,
                    onValueChange = { onAction(VisitRescheduleAction.SetFeeAccepted(!model.feeAccepted)) })
                .semantics(mergeDescendants = true) { contentDescription = label }
                .padding(vertical = 4.dp), horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.Top) {
                Checkbox(model.feeAccepted, onCheckedChange = null, Modifier.size(20.dp),
                    colors = CheckboxDefaults.colors(checkedColor = colors.accent,
                        uncheckedColor = colors.secondary, checkmarkColor = colors.panel))
                VisitText(label, colors.primary, Modifier.weight(1f))
            }
        }
    } else if (model.selectedSlotId != null) {
        VisitText("That appointment is no longer available. Choose another time.", colors.warning,
            Modifier.fillMaxWidth().testTag("visit.selection_warning")
                .background(colors.warningFill, RoundedCornerShape(12.dp)).padding(12.dp))
    }
    val guidance = when {
        effective == null && model.selectedSlotId != null -> null
        effective == null -> "Choose one appointment to continue."
        effective.second.feeLabel != null && !model.feeAccepted -> "Agree to the fee to continue."
        else -> "Your current time stays reserved until you confirm."
    }
    guidance?.let { VisitText(it, colors.secondary, Modifier.testTag("visit.guidance")) }
    VisitPrimaryButton("Confirm new time", "visit.confirm",
        effective != null && (effective.second.feeLabel == null || model.feeAccepted), colors) {
        effective?.let { onAction(VisitRescheduleAction.Confirm(it.second.id)) }
    }
}

@Composable
private fun VisitSlotRow(group: VisitSlotGroup, slot: VisitSlot, selected: Boolean,
    colors: VisitPalette, onAction: (VisitRescheduleAction) -> Unit) {
    val enabled = slot.availability != VisitSlotAvailability.Unavailable
    val availability = when (slot.availability) {
        VisitSlotAvailability.Available -> "Available"
        VisitSlotAvailability.Limited -> "Few left"
        VisitSlotAvailability.Unavailable -> "Unavailable"
    }
    val metadata = if (enabled) slot.feeLabel?.let { "$it fee" } ?: "No fee" else slot.unavailableReason.orEmpty()
    val shape = RoundedCornerShape(12.dp)
    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("visit.slot.${slot.id}")
        .clip(shape).background(if (selected) colors.selected else if (enabled) colors.panel else colors.inset)
        .border(if (selected) 2.dp else 1.dp, if (selected) colors.accent else colors.border, shape)
        .selectable(selected, enabled = enabled, role = Role.RadioButton,
            onClick = { if (!selected) onAction(VisitRescheduleAction.SelectSlot(slot.id)) })
        .semantics(mergeDescendants = true) {
            contentDescription = "${group.dayLabel}, ${slot.timeLabel}, ${slot.detail}, $availability, $metadata"
        }.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
        RadioButton(selected, onClick = null, Modifier.size(20.dp), enabled = enabled,
            colors = RadioButtonDefaults.colors(selectedColor = colors.accent, unselectedColor = colors.secondary,
                disabledSelectedColor = colors.secondary, disabledUnselectedColor = colors.secondary))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            VisitText(slot.timeLabel, if (enabled) colors.primary else colors.secondary, size = 17, line = 23, weight = FontWeight.SemiBold)
            VisitText(slot.detail, colors.secondary)
            VisitText(if (enabled) "$availability · $metadata" else availability, colors.secondary, size = 13, line = 18)
            if (!enabled) VisitText(metadata, colors.secondary, size = 13, line = 18)
        }
    }
}

@Composable
private fun VisitPrimaryButton(label: String, identifier: String, enabled: Boolean,
    colors: VisitPalette, onClick: () -> Unit) {
    Button(onClick, Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag(identifier), enabled = enabled,
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = colors.accent, contentColor = colors.buttonText,
            disabledContainerColor = colors.disabledFill, disabledContentColor = colors.disabledText),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 16.dp, vertical = 12.dp)) {
        VisitText(label, if (enabled) colors.buttonText else colors.disabledText,
            size = 16, line = 22, weight = FontWeight.SemiBold)
    }
}
