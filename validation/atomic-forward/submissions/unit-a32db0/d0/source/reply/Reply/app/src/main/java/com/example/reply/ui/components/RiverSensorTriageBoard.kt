package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

public data class RiverSensorIncident(
    val id: String,
    val label: String,
    val detail: String,
    val available: Boolean,
    val unavailableReason: String,
    val severity: String,
)

public data class RiverSensorTriageModel(
    val revision: String,
    val title: String,
    val subtitle: String,
    val notice: String,
    val footer: String,
    val guidance: String,
    val initialSelectedID: String?,
    val initialDetailsExpanded: Boolean,
    val incidents: List<RiverSensorIncident>,
)

@Composable
public fun RiverSensorTriageBoard(
    model: RiverSensorTriageModel,
    onSelect: (String) -> Unit,
    onAcknowledge: (String) -> Unit,
    onDetailsChange: (Boolean) -> Unit,
) {
    var selectedID by remember(model.revision) {
        mutableStateOf(model.incidents.firstOrNull { it.id == model.initialSelectedID && it.available }?.id)
    }
    var detailsExpanded by remember(model.revision) { mutableStateOf(model.initialDetailsExpanded) }
    val selected = model.incidents.firstOrNull { it.id == selectedID && it.available }
    val palette = RiverSensorPalette(isSystemInDarkTheme())
    val disclosureLabel = if (detailsExpanded) "Hide reading dossier" else "Show reading dossier"

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(palette.canvas, RoundedCornerShape(12.dp))
            .semantics(mergeDescendants = false) { }
            .testTag("river.canvas")
            .padding(16.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            RiverCopy(model.title, palette.ink, Modifier.testTag("river.title").semantics { heading() }, 22.sp, FontWeight.SemiBold)
            RiverCopy(model.subtitle, palette.ink)
            Column(
                Modifier.fillMaxWidth()
                    .background(palette.notice, RoundedCornerShape(10.dp))
                    .semantics(mergeDescendants = true) { }
                    .testTag("river.notice")
                    .padding(16.dp),
            ) { RiverCopy(model.notice, palette.ink) }
        }
        Spacer(Modifier.height(20.dp))
        Box(
            Modifier.fillMaxWidth()
                .clickable(role = Role.Button) {
                    detailsExpanded = !detailsExpanded
                    onDetailsChange(detailsExpanded)
                }
                .testTag("river.disclosure")
                .padding(vertical = 4.dp),
        ) { RiverCopy(disclosureLabel, palette.ink, weight = FontWeight.SemiBold) }
        Spacer(Modifier.height(12.dp))
        if (detailsExpanded && selected == null) {
            Box(Modifier.fillMaxWidth().background(palette.surface, RoundedCornerShape(10.dp)).padding(12.dp)) {
                RiverCopy(model.guidance, palette.ink)
            }
            Spacer(Modifier.height(12.dp))
        }
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            model.incidents.forEach { incident ->
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Row(Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
                        Box(Modifier.width(10.dp).fillMaxHeight().drawBehind {
                            drawLine(
                                color = palette.action,
                                start = Offset(size.width / 2f, 0f),
                                end = Offset(size.width / 2f, size.height + 12.dp.toPx()),
                                strokeWidth = 2.dp.toPx(),
                            )
                        })
                        Spacer(Modifier.width(2.dp))
                        Column(
                            modifier = Modifier.weight(1f)
                                .heightIn(min = 56.dp)
                                .clip(RoundedCornerShape(10.dp))
                                .background(if (selected?.id == incident.id) palette.selected else palette.surface)
                                .selectable(
                                    selected = selected?.id == incident.id,
                                    enabled = incident.available,
                                    role = Role.Button,
                                    onClick = {
                                        selectedID = incident.id
                                        onSelect(incident.id)
                                    },
                                )
                                .testTag("river.choice.${incident.id}")
                                .padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            RiverCopy(incident.label + if (incident.available) "" else " · Unavailable", palette.ink, weight = FontWeight.SemiBold)
                            RiverCopy(incident.severity.uppercase(), palette.ink, size = 12.sp, weight = FontWeight.SemiBold)
                            if (!incident.available) RiverCopy(incident.unavailableReason, palette.ink, size = 14.sp)
                        }
                    }
                    if (detailsExpanded && selected?.id == incident.id) {
                        RiverCopy(incident.detail, palette.ink, Modifier.padding(start = 24.dp, end = 12.dp, top = 4.dp, bottom = 4.dp))
                    }
                }
            }
        }
        Spacer(Modifier.height(20.dp))
        RiverCopy(selected?.let { "Reviewing: ${it.label}" } ?: "No alert selected", palette.ink, Modifier.testTag("river.summary"), weight = FontWeight.SemiBold)
        Spacer(Modifier.height(20.dp))
        Box(
            Modifier.fillMaxWidth()
                .heightIn(min = 56.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(if (selected == null) palette.disabled else palette.action)
                .clickable(enabled = selected != null, role = Role.Button) {
                    selected?.let { onAcknowledge(it.id) }
                }
                .testTag("river.submit")
                .padding(horizontal = 18.dp, vertical = 16.dp),
            contentAlignment = Alignment.CenterStart,
        ) { RiverCopy("Acknowledge alert", palette.onAction, weight = FontWeight.SemiBold) }
        Spacer(Modifier.height(20.dp))
        RiverCopy(model.footer, palette.ink, Modifier.testTag("river.footer"), 14.sp)
    }
}

@Composable
private fun RiverCopy(
    text: String,
    color: Color,
    modifier: Modifier = Modifier,
    size: TextUnit = 16.sp,
    weight: FontWeight = FontWeight.Normal,
) {
    Text(
        text = text,
        modifier = modifier.fillMaxWidth(),
        color = color,
        style = TextStyle(fontSize = size, lineHeight = size * 1.3f, fontWeight = weight),
        softWrap = true,
    )
}

private class RiverSensorPalette(dark: Boolean) {
    val canvas = Color(if (dark) 0xFF14282D else 0xFFF5F2EB)
    val notice = Color(if (dark) 0xFF2D4245 else 0xFFE7DED0)
    val action = Color(if (dark) 0xFF8CC7C7 else 0xFF315F68)
    val disabled = Color(if (dark) 0xFF52666A else 0xFFAAA99F)
    val ink = Color(if (dark) 0xFFE6F1EF else 0xFF172D32)
    val surface = Color(if (dark) 0xFF20383D else 0xFFFFFFFF)
    val selected = Color(if (dark) 0xFF31575C else 0xFFD6E6E5)
    val onAction = Color(if (dark) 0xFF102D30 else 0xFFF8FBFA)
}
