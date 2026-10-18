package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class VisitPalette(val panel: Color, val text: Color, val secondary: Color, val inset: Color,
    val border: Color, val accent: Color, val selection: Color, val warningText: Color, val warningFill: Color,
    val successText: Color, val successFill: Color, val onPrimary: Color, val disabled: Color, val onDisabled: Color)

@Composable
private fun visitPalette(): VisitPalette = if (isSystemInDarkTheme()) VisitPalette(
    Color(0xFF161C27), Color(0xFFF2F4F7), Color(0xFFB8C4D4), Color(0xFF202938), Color(0xFF485568),
    Color(0xFF84ADFF), Color(0xFF162F51), Color(0xFFFFD691), Color(0xFF3B2D17), Color(0xFF75E0AD),
    Color(0xFF163629), Color(0xFF10213D), Color(0xFF344054), Color(0xFFB8C4D4)
) else VisitPalette(
    Color(0xFFFFFFFF), Color(0xFF182230), Color(0xFF526174), Color(0xFFF4F6F9), Color(0xFFD5DDE7),
    Color(0xFF175CD3), Color(0xFFEFF6FF), Color(0xFF854A0E), Color(0xFFFFF7E0), Color(0xFF087443),
    Color(0xFFEAFBF2), Color(0xFFFFFFFF), Color(0xFFE4E7EC), Color(0xFF667085)
)

@Composable
private fun VisitText(value: String, color: Color, size: Int = 14, line: Int = 20,
                      weight: FontWeight = FontWeight.Normal, modifier: Modifier = Modifier) {
    Text(value, modifier, color = color, style = TextStyle(fontSize = size.sp, lineHeight = line.sp,
        fontWeight = weight, textDirection = TextDirection.ContentOrLtr))
}

@Composable
fun VisitReschedulePanel(model: VisitRescheduleModel, onAction: (VisitRescheduleAction) -> Unit,
                         modifier: Modifier = Modifier) {
    val p = visitPalette()
    val effective = if (model.mode == VisitRescheduleMode.Choosing) model.groups.firstNotNullOfOrNull { group ->
        group.slots.firstOrNull { it.id == model.selectedSlotId && it.availability != VisitSlotAvailability.Unavailable }
            ?.let { group to it }
    } else null
    Column(modifier.fillMaxWidth().testTag("visit.panel").clip(RoundedCornerShape(20.dp))
        .background(p.panel).padding(16.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            VisitText(if (model.mode == VisitRescheduleMode.Confirmed) "Visit rescheduled" else "Reschedule visit",
                p.text, 22, 28, FontWeight.SemiBold, Modifier.testTag("visit.title"))
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                VisitText(model.serviceTitle, p.text, 17, 23, FontWeight.SemiBold, Modifier.testTag("visit.service"))
                VisitText(model.location, p.secondary, modifier = Modifier.testTag("visit.location"))
            }
        }
        VisitAppointmentCard(if (model.mode == VisitRescheduleMode.Confirmed) "Previous appointment" else "Current appointment",
            model.currentAppointment, p, Modifier.testTag("visit.current"))
        when (model.mode) {
            VisitRescheduleMode.Loading -> Row(Modifier.fillMaxWidth().testTag("visit.loading"),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                CircularProgressIndicator(Modifier.size(20.dp), color = p.accent, strokeWidth = 2.dp)
                VisitText("Checking available appointments…", p.secondary, modifier = Modifier.weight(1f))
            }
            VisitRescheduleMode.Unavailable -> {
                Column(Modifier.fillMaxWidth().testTag("visit.unavailable").background(p.inset, RoundedCornerShape(12.dp)).padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    VisitText("No appointments available", p.text, 17, 23, FontWeight.SemiBold)
                    model.unavailableMessage?.let { VisitText(it, p.secondary) }
                }
                VisitPrimaryButton("Check again", "visit.retry", true, p) { onAction(VisitRescheduleAction.Retry) }
            }
            VisitRescheduleMode.Confirmed -> {
                model.confirmation?.let { confirmation ->
                    Column(Modifier.fillMaxWidth().testTag("visit.confirmation")
                        .background(p.successFill, RoundedCornerShape(12.dp)).padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        VisitText("✓  New appointment confirmed", p.successText, 17, 23, FontWeight.SemiBold)
                        VisitText(confirmation.appointment.dayLabel, p.text, 15, 20, FontWeight.SemiBold)
                        VisitText(confirmation.appointment.timeLabel, p.text)
                        VisitText("Reference: ${confirmation.reference}", p.successText, modifier = Modifier.testTag("visit.reference"))
                        VisitText(confirmation.note, p.secondary)
                    }
                }
                VisitPrimaryButton("Done", "visit.done", true, p) { onAction(VisitRescheduleAction.Done) }
            }
            VisitRescheduleMode.Choosing -> {
                Column(Modifier.selectableGroup(), verticalArrangement = Arrangement.spacedBy(20.dp)) {
                    model.groups.forEach { group ->
                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            VisitText(group.dayLabel, p.text, 15, 20, FontWeight.SemiBold,
                                Modifier.testTag("visit.group.${group.id}"))
                            group.slots.forEach { slot ->
                                VisitSlotRow(group, slot, effective?.second?.id == slot.id, p) {
                                    onAction(VisitRescheduleAction.SelectSlot(slot.id))
                                }
                            }
                        }
                    }
                }
                if (effective != null) {
                    val (group, slot) = effective
                    VisitAppointmentCard("New appointment", VisitAppointment(group.dayLabel, slot.timeLabel), p,
                        Modifier.testTag("visit.selection_summary"), slot.feeLabel ?: "", true)
                    slot.feeLabel?.let { amount ->
                        val consent = "I agree to the rescheduling fee of $amount."
                        Row(Modifier.fillMaxWidth().heightIn(min = 48.dp)
                            .toggleable(value = model.feeAccepted, role = Role.Checkbox,
                                onValueChange = { onAction(VisitRescheduleAction.SetFeeAccepted(!model.feeAccepted)) })
                            .testTag("visit.fee_consent").semantics(mergeDescendants = true) { contentDescription = consent }
                            .padding(vertical = 4.dp), horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(model.feeAccepted, onCheckedChange = null, modifier = Modifier.size(20.dp).clearAndSetSemantics {},
                                colors = CheckboxDefaults.colors(checkedColor = p.accent, uncheckedColor = p.secondary, checkmarkColor = p.onPrimary))
                            VisitText(consent, p.text, modifier = Modifier.weight(1f).clearAndSetSemantics {})
                        }
                    }
                } else if (model.selectedSlotId != null) {
                    VisitText("That appointment is no longer available. Choose another time.", p.warningText,
                        modifier = Modifier.fillMaxWidth().testTag("visit.selection_warning")
                            .background(p.warningFill, RoundedCornerShape(12.dp)).padding(12.dp))
                }
                if (effective != null || model.selectedSlotId == null) {
                    val guidance = when {
                        effective == null -> "Choose one appointment to continue."
                        effective.second.feeLabel != null && !model.feeAccepted -> "Agree to the fee to continue."
                        else -> "Your current time stays reserved until you confirm."
                    }
                    VisitText(guidance, p.secondary, modifier = Modifier.testTag("visit.guidance"))
                }
                val enabled = effective != null && (effective.second.feeLabel == null || model.feeAccepted)
                VisitPrimaryButton("Confirm new time", "visit.confirm", enabled, p) {
                    if (enabled && effective != null) onAction(VisitRescheduleAction.Confirm(effective.second.id))
                }
            }
        }
    }
}

@Composable
private fun VisitAppointmentCard(label: String, appointment: VisitAppointment, p: VisitPalette,
                                 modifier: Modifier, fee: String = "", showFee: Boolean = false) {
    Column(modifier.fillMaxWidth().background(p.inset, RoundedCornerShape(12.dp)).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)) {
        VisitText(label, p.secondary, 13, 18, FontWeight.SemiBold)
        VisitText(appointment.dayLabel, p.text, 15, 20, FontWeight.SemiBold)
        VisitText(appointment.timeLabel, p.secondary)
        if (showFee) VisitText(if (fee.isEmpty()) "No rescheduling fee" else "Rescheduling fee  $fee",
            p.text, modifier = Modifier.padding(top = 6.dp))
    }
}

@Composable
private fun VisitSlotRow(group: VisitSlotGroup, slot: VisitSlot, selected: Boolean, p: VisitPalette, onSelect: () -> Unit) {
    val eligible = slot.availability != VisitSlotAvailability.Unavailable
    val availability = when (slot.availability) {
        VisitSlotAvailability.Available -> "Available"
        VisitSlotAvailability.Limited -> "Few left"
        VisitSlotAvailability.Unavailable -> "Unavailable"
    }
    val metadata = if (eligible) "$availability · ${slot.feeLabel?.let { "$it fee" } ?: "No fee"}" else availability
    val description = listOfNotNull(group.dayLabel, slot.timeLabel, slot.detail, metadata,
        if (!eligible) slot.unavailableReason else null).joinToString(", ")
    val shape = RoundedCornerShape(12.dp)
    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).clip(shape)
        .background(if (selected) p.selection else if (eligible) p.panel else p.inset)
        .border(if (selected) 2.dp else 1.dp, if (selected) p.accent else p.border, shape)
        .selectable(selected, enabled = eligible, role = Role.RadioButton, onClick = { if (!selected && eligible) onSelect() })
        .testTag("visit.slot.${slot.id}").semantics(mergeDescendants = true) { contentDescription = description }
        .padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
        RadioButton(selected, onClick = null, enabled = eligible,
            modifier = Modifier.padding(top = 1.dp).size(20.dp).clearAndSetSemantics {},
            colors = RadioButtonDefaults.colors(selectedColor = p.accent, unselectedColor = p.secondary,
                disabledSelectedColor = p.secondary, disabledUnselectedColor = p.secondary))
        Column(Modifier.weight(1f).clearAndSetSemantics {}, verticalArrangement = Arrangement.spacedBy(6.dp)) {
            VisitText(slot.timeLabel, if (eligible) p.text else p.secondary, 17, 23, FontWeight.SemiBold)
            VisitText(slot.detail, p.secondary)
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                VisitText(metadata, p.secondary, 13, 18)
                if (!eligible) slot.unavailableReason?.let { VisitText(it, p.secondary, 13, 18) }
            }
        }
    }
}

@Composable
private fun VisitPrimaryButton(label: String, id: String, enabled: Boolean, p: VisitPalette, action: () -> Unit) {
    Button(action, Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag(id), enabled = enabled,
        shape = RoundedCornerShape(12.dp), contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = p.accent, contentColor = p.onPrimary,
            disabledContainerColor = p.disabled, disabledContentColor = p.onDisabled)) {
        VisitText(label, if (enabled) p.onPrimary else p.onDisabled, 16, 22, FontWeight.SemiBold)
    }
}
