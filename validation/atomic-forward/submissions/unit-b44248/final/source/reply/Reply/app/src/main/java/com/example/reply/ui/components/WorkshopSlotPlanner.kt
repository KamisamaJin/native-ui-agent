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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
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
    key(model.revision) {
        var selectedID by remember {
            mutableStateOf(model.slots.firstOrNull {
                it.id == model.initialSelectedID && it.available
            }?.id)
        }
        var detailsExpanded by remember { mutableStateOf(model.initialDetailsExpanded) }
        val current = model.slots.firstOrNull { it.id == selectedID && it.available }
        val palette = workshopPalette(isSystemInDarkTheme())
        val ordinaryText = LocalDensity.current.fontScale <= 1f
        BoxWithConstraints(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .background(palette.canvas)
                .semantics(mergeDescendants = false) {}
                .testTag("workshop.canvas"),
        ) {
            val columns = if (maxWidth >= 320.dp && ordinaryText) 2 else 1
            Column(
                modifier = Modifier.fillMaxWidth().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp),
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(
                        text = model.title,
                        color = palette.ink,
                        fontSize = 22.sp,
                        lineHeight = 28.6.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.fillMaxWidth()
                            .testTag("workshop.title").semantics { heading() },
                    )
                    WorkshopText(model.subtitle, palette.ink)
                    Column(
                        Modifier.fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(palette.notice)
                            .semantics(mergeDescendants = true) {}
                            .testTag("workshop.notice")
                            .padding(16.dp),
                    ) {
                        WorkshopText(model.notice, palette.ink)
                    }
                }
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    model.slots.chunked(columns).forEach { slots ->
                        Row(
                            modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            slots.forEach { slot ->
                                WorkshopSlotCard(
                                    slot = slot,
                                    isSelected = current?.id == slot.id,
                                    palette = palette,
                                    modifier = Modifier.weight(1f).fillMaxHeight(),
                                    onClick = {
                                        selectedID = slot.id
                                        onSelect(slot.id)
                                    },
                                )
                            }
                            if (slots.size < columns) Spacer(Modifier.weight(1f))
                        }
                    }
                }
                WorkshopText(
                    text = current?.let { "Draft station: ${it.label}" } ?: "No station selected",
                    color = palette.ink,
                    weight = FontWeight.SemiBold,
                    modifier = Modifier.testTag("workshop.summary"),
                )
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    WorkshopText(
                        text = if (detailsExpanded) "Hide safety briefing" else "Show safety briefing",
                        color = palette.ink,
                        weight = FontWeight.SemiBold,
                        modifier = Modifier.fillMaxWidth()
                            .clickable(role = Role.Button) {
                                detailsExpanded = !detailsExpanded
                                onDetailsChange(detailsExpanded)
                            }
                            .testTag("workshop.disclosure"),
                    )
                    if (detailsExpanded) WorkshopText(model.guidance, palette.ink)
                }
                Column(
                    Modifier.fillMaxWidth()
                        .heightIn(min = 56.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(if (current != null) palette.enabled else palette.disabled)
                        .clickable(enabled = current != null, role = Role.Button) {
                            current?.let { onReserve(it.id) }
                        }
                        .testTag("workshop.submit")
                        .padding(horizontal = 18.dp, vertical = 16.dp),
                    verticalArrangement = Arrangement.Center,
                ) {
                    WorkshopText("Request station", palette.onAction, weight = FontWeight.SemiBold)
                }
                WorkshopText(
                    text = model.footer,
                    color = palette.ink,
                    supporting = true,
                    modifier = Modifier.testTag("workshop.footer"),
                )
            }
        }
    }
}

@Composable
private fun WorkshopSlotCard(
    slot: WorkshopSlot,
    isSelected: Boolean,
    palette: WorkshopColors,
    modifier: Modifier,
    onClick: () -> Unit,
) {
    Column(
        modifier.heightIn(min = 56.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(if (isSelected) palette.selected else palette.surface)
            .clickable(enabled = slot.available, role = Role.Button, onClick = onClick)
            .semantics { selected = isSelected }
            .testTag("workshop.choice.${slot.id}")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        WorkshopText(
            text = if (slot.available) slot.label else "${slot.label} · Unavailable",
            color = palette.ink,
            weight = FontWeight.SemiBold,
        )
        if (!slot.available) WorkshopText(slot.unavailableReason, palette.ink, supporting = true)
        WorkshopText(slot.detail, palette.ink, supporting = true)
    }
}

@Composable
private fun WorkshopText(
    text: String,
    color: Color,
    modifier: Modifier = Modifier,
    supporting: Boolean = false,
    weight: FontWeight = FontWeight.Normal,
) {
    Text(
        text = text,
        modifier = modifier.fillMaxWidth(),
        color = color,
        fontSize = if (supporting) 14.sp else 16.sp,
        lineHeight = if (supporting) 18.2.sp else 20.8.sp,
        fontWeight = weight,
        softWrap = true,
    )
}

private data class WorkshopColors(
    val canvas: Color,
    val notice: Color,
    val enabled: Color,
    val disabled: Color,
    val ink: Color,
    val surface: Color,
    val selected: Color,
    val onAction: Color,
)

private fun workshopPalette(dark: Boolean): WorkshopColors = if (dark) {
    WorkshopColors(
        canvas = Color(0xFF14282D), notice = Color(0xFF2D4245),
        enabled = Color(0xFF8CC7C7), disabled = Color(0xFF52666A),
        ink = Color(0xFFE6F1EF), surface = Color(0xFF20383D),
        selected = Color(0xFF31575C), onAction = Color(0xFF102D30),
    )
} else {
    WorkshopColors(
        canvas = Color(0xFFF5F2EB), notice = Color(0xFFE7DED0),
        enabled = Color(0xFF315F68), disabled = Color(0xFFAAA99F),
        ink = Color(0xFF172D32), surface = Color(0xFFFFFFFF),
        selected = Color(0xFFD6E6E5), onAction = Color(0xFFF8FBFA),
    )
}
