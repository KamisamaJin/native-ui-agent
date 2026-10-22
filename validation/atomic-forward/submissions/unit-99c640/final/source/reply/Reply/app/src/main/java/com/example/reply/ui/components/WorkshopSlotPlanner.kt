package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

public data class WorkshopSlot(
    val id: String,
    val label: String,
    val detail: String,
    val available: Boolean,
    val unavailableReason: String,
)

public data class WorkshopSlotPlannerModel(
    val revision: String,
    val title: String,
    val subtitle: String,
    val notice: String,
    val footer: String,
    val guidance: String,
    val initialSelectedID: String?,
    val initialDetailsExpanded: Boolean,
    val slots: List<WorkshopSlot>,
)

@Composable
public fun WorkshopSlotPlanner(
    model: WorkshopSlotPlannerModel,
    onSelect: (String) -> Unit,
    onReserve: (String) -> Unit,
    onDetailsChange: (Boolean) -> Unit,
) {
    var selectedID by remember(model.revision) {
        mutableStateOf(model.slots.firstOrNull { it.id == model.initialSelectedID && it.available }?.id)
    }
    var expanded by remember(model.revision) { mutableStateOf(model.initialDetailsExpanded) }
    val selectedSlot = model.slots.firstOrNull { it.id == selectedID && it.available }
    val palette = WorkshopPalette(isSystemInDarkTheme())
    val fontScale = LocalDensity.current.fontScale
    val body = TextStyle(fontSize = 16.sp, lineHeight = 20.8.sp, fontWeight = FontWeight.Normal, color = palette.ink)
    val supporting = TextStyle(fontSize = 14.sp, lineHeight = 18.2.sp, fontWeight = FontWeight.Normal, color = palette.ink)
    val labelStyle = body.copy(fontWeight = FontWeight.SemiBold)
    val disclosureLabel = if (expanded) "Hide safety briefing" else "Show safety briefing"

    BoxWithConstraints(Modifier.fillMaxWidth()) {
        val columns = if (maxWidth >= 320.dp && fontScale <= 1f) 2 else 1
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .background(palette.canvas)
                .testTag("workshop.canvas")
                .semantics(mergeDescendants = false) { }
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    model.title,
                    modifier = Modifier.fillMaxWidth().testTag("workshop.title").semantics { heading() },
                    style = TextStyle(fontSize = 22.sp, lineHeight = 28.6.sp, fontWeight = FontWeight.SemiBold, color = palette.ink),
                )
                Text(model.subtitle, modifier = Modifier.fillMaxWidth(), style = body)
                Column(
                    Modifier.fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(palette.notice)
                        .testTag("workshop.notice")
                        .semantics(mergeDescendants = true) { }
                        .padding(16.dp),
                ) {
                    Text(model.notice, modifier = Modifier.fillMaxWidth(), style = body)
                }
            }
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                model.slots.chunked(columns).forEach { slots ->
                    Row(
                        modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        slots.forEach { slot ->
                            val isSelected = selectedSlot?.id == slot.id
                            Column(
                                modifier = Modifier.weight(1f).fillMaxHeight()
                                    .heightIn(min = 56.dp)
                                    .clip(RoundedCornerShape(10.dp))
                                    .background(if (isSelected) palette.selected else palette.surface)
                                    .testTag("workshop.choice.${slot.id}")
                                    .semantics { selected = isSelected }
                                    .clickable(enabled = slot.available, role = Role.Button) {
                                        selectedID = slot.id
                                        onSelect(slot.id)
                                    }
                                    .padding(16.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp),
                            ) {
                                Text(
                                    if (slot.available) slot.label else "${slot.label} · Unavailable",
                                    modifier = Modifier.fillMaxWidth(),
                                    style = labelStyle,
                                )
                                if (!slot.available) {
                                    Text(slot.unavailableReason, modifier = Modifier.fillMaxWidth(), style = supporting)
                                }
                                Text(slot.detail, modifier = Modifier.fillMaxWidth(), style = supporting)
                            }
                        }
                        if (slots.size < columns) Spacer(Modifier.weight(1f))
                    }
                }
            }
            Text(
                selectedSlot?.let { "Draft station: ${it.label}" } ?: "No station selected",
                modifier = Modifier.fillMaxWidth().testTag("workshop.summary"),
                style = labelStyle,
            )
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    disclosureLabel,
                    modifier = Modifier.fillMaxWidth().testTag("workshop.disclosure")
                        .clickable(role = Role.Button) {
                            expanded = !expanded
                            onDetailsChange(expanded)
                        },
                    style = labelStyle,
                )
                if (expanded) Text(model.guidance, modifier = Modifier.fillMaxWidth(), style = body)
            }
            Column(
                modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(if (selectedSlot == null) palette.disabled else palette.enabled)
                    .testTag("workshop.submit")
                    .clickable(enabled = selectedSlot != null, role = Role.Button) {
                        selectedSlot?.let { onReserve(it.id) }
                    }
                    .padding(horizontal = 18.dp, vertical = 16.dp),
            ) {
                Text("Request station", modifier = Modifier.fillMaxWidth(), style = labelStyle.copy(color = palette.onAction))
            }
            Text(model.footer, modifier = Modifier.fillMaxWidth().testTag("workshop.footer"), style = supporting)
        }
    }
}

private class WorkshopPalette(dark: Boolean) {
    val canvas = Color(if (dark) 0xFF14282D else 0xFFF5F2EB)
    val notice = Color(if (dark) 0xFF2D4245 else 0xFFE7DED0)
    val enabled = Color(if (dark) 0xFF8CC7C7 else 0xFF315F68)
    val disabled = Color(if (dark) 0xFF52666A else 0xFFAAA99F)
    val ink = Color(if (dark) 0xFFE6F1EF else 0xFF172D32)
    val surface = Color(if (dark) 0xFF20383D else 0xFFFFFFFF)
    val selected = Color(if (dark) 0xFF31575C else 0xFFD6E6E5)
    val onAction = Color(if (dark) 0xFF102D30 else 0xFFF8FBFA)
}
