package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private class VisitColors(dark: Boolean) {
    val panel = Color(if (dark) 0xFF161C27 else 0xFFFFFFFF)
    val primary = Color(if (dark) 0xFFF2F4F7 else 0xFF182230)
    val secondary = Color(if (dark) 0xFFB8C4D4 else 0xFF526174)
    val inset = Color(if (dark) 0xFF202938 else 0xFFF4F6F9)
    val border = Color(if (dark) 0xFF485568 else 0xFFD5DDE7)
    val accent = Color(if (dark) 0xFF84ADFF else 0xFF175CD3)
    val selected = Color(if (dark) 0xFF162F51 else 0xFFEFF6FF)
    val warning = Color(if (dark) 0xFFFFD691 else 0xFF854A0E)
    val warningFill = Color(if (dark) 0xFF3B2D17 else 0xFFFFF7E0)
    val success = Color(if (dark) 0xFF75E0AD else 0xFF087443)
    val successFill = Color(if (dark) 0xFF163629 else 0xFFEAFBF2)
    val onAccent = Color(if (dark) 0xFF10213D else 0xFFFFFFFF)
    val disabled = Color(if (dark) 0xFF344054 else 0xFFE4E7EC)
    val onDisabled = Color(if (dark) 0xFFB8C4D4 else 0xFF667085)
}

@Composable
private fun VisitText(
    value: String, colors: VisitColors, modifier: Modifier = Modifier,
    size: Int = 14, line: Int = 20, strong: Boolean = false,
    color: Color = colors.primary,
) {
    Text(value, modifier, color = color, style = TextStyle(
        fontFamily = FontFamily.Default, fontSize = size.sp, lineHeight = line.sp,
        fontWeight = if (strong) FontWeight.SemiBold else FontWeight.Normal,
    ))
}

/** Caller-controlled rescheduling choices, consent, and actions. */
@Composable
fun VisitReschedulePanel(
    model: VisitRescheduleModel,
    onAction: (VisitRescheduleAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = VisitColors(isSystemInDarkTheme())
    val effective = if (model.mode == VisitRescheduleMode.Choosing) {
        model.groups.firstNotNullOfOrNull { group ->
            group.slots.firstOrNull {
                it.id == model.selectedSlotId && it.availability != VisitSlotAvailability.Unavailable
            }?.let { group to it }
        }
    } else null
    Column(
        modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(colors.panel)
            .testTag("visit.panel").padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            VisitText(if (model.mode == VisitRescheduleMode.Confirmed) "Visit rescheduled" else "Reschedule visit",
                colors, Modifier.testTag("visit.title").semantics { heading() }, 22, 28, true)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                VisitText(model.serviceTitle, colors, Modifier.testTag("visit.service"), 17, 23, true)
                VisitText(model.location, colors, Modifier.testTag("visit.location"), color = colors.secondary)
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
                VisitText("Checking available appointments…", colors, Modifier.weight(1f), color = colors.secondary)
            }
            VisitRescheduleMode.Unavailable -> {
                Column(Modifier.fillMaxWidth().testTag("visit.unavailable"), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    VisitText("No appointments available", colors, size = 17, line = 23, strong = true)
                    model.unavailableMessage?.let { VisitText(it, colors, color = colors.secondary) }
                }
                VisitPrimary("Check again", "visit.retry", true, colors) { onAction(VisitRescheduleAction.Retry) }
            }
            VisitRescheduleMode.Confirmed -> {
                model.confirmation?.let { confirmation ->
                    Column(
                        Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(colors.successFill)
                            .testTag("visit.confirmation").padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        VisitText("✓ New appointment confirmed", colors, size = 17, line = 23, strong = true, color = colors.success)
                        VisitText(confirmation.appointment.dayLabel, colors, size = 15, line = 20, strong = true)
                        VisitText(confirmation.appointment.timeLabel, colors)
                        VisitText("Reference: ${confirmation.reference}", colors, Modifier.testTag("visit.reference"))
                        VisitText(confirmation.note, colors, color = colors.secondary)
                    }
                }
                VisitPrimary("Done", "visit.done", true, colors) { onAction(VisitRescheduleAction.Done) }
            }
            VisitRescheduleMode.Choosing -> {
                Column(Modifier.fillMaxWidth().selectableGroup(), verticalArrangement = Arrangement.spacedBy(20.dp)) {
                    model.groups.forEach { group ->
                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            VisitText(group.dayLabel, colors,
                                Modifier.testTag("visit.group.${group.id}").semantics { heading() }, 15, 20, true)
                            group.slots.forEach { slot ->
                                VisitSlotRow(group, slot, slot.id == effective?.second?.id, colors) {
                                    onAction(VisitRescheduleAction.SelectSlot(slot.id))
                                }
                            }
                        }
                    }
                }
                if (effective != null) {
                    val (group, slot) = effective
                    Column(
                        Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(colors.inset)
                            .testTag("visit.selection_summary").padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        VisitText("New appointment", colors, size = 13, line = 18, strong = true, color = colors.secondary)
                        VisitText(group.dayLabel, colors, size = 15, line = 20, strong = true)
                        VisitText(slot.timeLabel, colors, color = colors.secondary)
                        Spacer(Modifier.height(2.dp))
                        if (slot.feeLabel == null) VisitText("No rescheduling fee", colors, color = colors.secondary)
                        else {
                            VisitText("Rescheduling fee", colors, color = colors.secondary)
                            VisitText(slot.feeLabel, colors, strong = true)
                        }
                    }
                    slot.feeLabel?.let { fee ->
                        Row(
                            Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("visit.fee_consent")
                                .toggleable(value = model.feeAccepted, role = Role.Checkbox,
                                    onValueChange = { onAction(VisitRescheduleAction.SetFeeAccepted(!model.feeAccepted)) })
                                .semantics(mergeDescendants = true) {},
                            horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Checkbox(model.feeAccepted, onCheckedChange = null, modifier = Modifier.size(20.dp),
                                colors = CheckboxDefaults.colors(checkedColor = colors.accent, uncheckedColor = colors.secondary, checkmarkColor = colors.onAccent))
                            VisitText("I agree to the rescheduling fee of $fee.", colors, Modifier.weight(1f))
                        }
                    }
                } else if (model.selectedSlotId != null) {
                    VisitText("That appointment is no longer available. Choose another time.", colors,
                        Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(colors.warningFill)
                            .testTag("visit.selection_warning").padding(12.dp), color = colors.warning)
                }
                if (effective != null || model.selectedSlotId == null) {
                    val guidance = when {
                        effective == null -> "Choose one appointment to continue."
                        effective.second.feeLabel != null && !model.feeAccepted -> "Agree to the fee to continue."
                        else -> "Your current time stays reserved until you confirm."
                    }
                    VisitText(guidance, colors, Modifier.testTag("visit.guidance"), color = colors.secondary)
                }
                VisitPrimary("Confirm new time", "visit.confirm",
                    effective != null && (effective.second.feeLabel == null || model.feeAccepted), colors) {
                    effective?.let { onAction(VisitRescheduleAction.Confirm(it.second.id)) }
                }
            }
        }
    }
}

@Composable
private fun VisitAppointmentCard(label: String, appointment: VisitAppointment, colors: VisitColors, modifier: Modifier) {
    Column(modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(colors.inset).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        VisitText(label, colors, size = 13, line = 18, strong = true, color = colors.secondary)
        VisitText(appointment.dayLabel, colors, size = 15, line = 20, strong = true)
        VisitText(appointment.timeLabel, colors, color = colors.secondary)
    }
}

@Composable
private fun VisitSlotRow(group: VisitSlotGroup, slot: VisitSlot, selected: Boolean, colors: VisitColors, onSelect: () -> Unit) {
    val enabled = slot.availability != VisitSlotAvailability.Unavailable
    val availability = when (slot.availability) {
        VisitSlotAvailability.Available -> "Available"
        VisitSlotAvailability.Limited -> "Few left"
        VisitSlotAvailability.Unavailable -> "Unavailable"
    }
    val fee = slot.feeLabel?.let { "$it fee" } ?: "No fee"
    val metadata = if (enabled) "$availability · $fee" else availability
    val description = listOf(group.dayLabel, slot.timeLabel, slot.detail, availability,
        if (enabled) fee else slot.unavailableReason.orEmpty()).joinToString(", ")
    Row(
        Modifier.fillMaxWidth().heightIn(min = 48.dp).clip(RoundedCornerShape(12.dp))
            .background(if (selected) colors.selected else if (enabled) colors.panel else colors.inset)
            .border(if (selected) 2.dp else 1.dp, if (selected) colors.accent else colors.border, RoundedCornerShape(12.dp))
            .testTag("visit.slot.${slot.id}")
            .selectable(selected, enabled = enabled, role = Role.RadioButton, onClick = { if (!selected) onSelect() })
            .semantics(mergeDescendants = true) { contentDescription = description }
            .padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top,
    ) {
        Box(Modifier.padding(top = 2.dp).size(20.dp)
            .border(if (selected) 2.dp else 1.5.dp, if (selected) colors.accent else colors.secondary, CircleShape),
            contentAlignment = Alignment.Center) {
            if (selected) Box(Modifier.size(10.dp).background(colors.accent, CircleShape))
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            VisitText(slot.timeLabel, colors, size = 17, line = 23, strong = true, color = if (enabled) colors.primary else colors.secondary)
            VisitText(slot.detail, colors, color = colors.secondary)
            VisitText(metadata, colors, size = 13, line = 18, color = colors.secondary)
            if (!enabled) slot.unavailableReason?.let { VisitText(it, colors, size = 13, line = 18, color = colors.secondary) }
        }
    }
}

@Composable
private fun VisitPrimary(title: String, id: String, enabled: Boolean, colors: VisitColors, onClick: () -> Unit) {
    Button(onClick, Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag(id), enabled = enabled,
        shape = RoundedCornerShape(12.dp), contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = colors.accent, contentColor = colors.onAccent,
            disabledContainerColor = colors.disabled, disabledContentColor = colors.onDisabled)) {
        Text(title, Modifier.fillMaxWidth(), textAlign = TextAlign.Center,
            style = TextStyle(fontSize = 16.sp, lineHeight = 22.sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Default))
    }
}
