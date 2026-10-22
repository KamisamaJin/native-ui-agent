package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.util.Locale

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
        mutableStateOf(model.incidents.firstOrNull {
            it.id == model.initialSelectedID && it.available
        }?.id)
    }
    var expanded by remember(model.revision) { mutableStateOf(model.initialDetailsExpanded) }
    val selected = model.incidents.firstOrNull { it.id == selectedID && it.available }
    val colors = RiverColors(MaterialTheme.colorScheme.background.luminance() < 0.5f)
    val bodyStyle = TextStyle(
        color = colors.ink,
        fontSize = 16.sp,
        lineHeight = 20.8.sp,
        fontWeight = FontWeight.Normal,
        textAlign = TextAlign.Start,
    )
    val supportingStyle = bodyStyle.copy(fontSize = 14.sp, lineHeight = 18.2.sp)
    val emphasisStyle = bodyStyle.copy(fontWeight = FontWeight.SemiBold)

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(colors.canvas)
            .testTag("river.canvas")
            .semantics(mergeDescendants = false) {}
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        RiverText(
            model.title,
            bodyStyle.copy(fontSize = 22.sp, lineHeight = 28.6.sp, fontWeight = FontWeight.SemiBold),
            Modifier.testTag("river.title").semantics { heading() },
        )
        RiverText(model.subtitle, bodyStyle)

        Box(
            Modifier.fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .background(colors.notice)
                .testTag("river.notice")
                .semantics(mergeDescendants = true) {}
                .padding(16.dp),
        ) {
            RiverText(model.notice, bodyStyle)
        }

        Column(Modifier.padding(top = 8.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Box(
                Modifier.fillMaxWidth()
                    .testTag("river.disclosure")
                    .clickable(role = Role.Button) {
                        expanded = !expanded
                        onDetailsChange(expanded)
                    }
                    .padding(vertical = 4.dp),
            ) {
                RiverText(if (expanded) "Hide reading dossier" else "Show reading dossier", emphasisStyle)
            }

            if (expanded && selected == null) {
                RiverText(model.guidance, bodyStyle, Modifier.padding(vertical = 4.dp))
            }

            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                model.incidents.forEach { incident ->
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Box(
                            Modifier.fillMaxWidth().drawBehind {
                                val offset = 5.dp.toPx()
                                val x = if (layoutDirection == LayoutDirection.Ltr) offset else size.width - offset
                                drawLine(colors.enabled, Offset(x, 0f), Offset(x, size.height), 2.dp.toPx())
                            }.padding(start = 12.dp),
                        ) {
                            Column(
                                modifier = Modifier.fillMaxWidth()
                                    .clip(RoundedCornerShape(10.dp))
                                    .background(if (selected?.id == incident.id) colors.selected else colors.surface)
                                    .testTag("river.choice.${incident.id}")
                                    .selectable(
                                        selected = selected?.id == incident.id,
                                        enabled = incident.available,
                                        role = Role.Button,
                                        onClick = {
                                            if (incident.available) {
                                                selectedID = incident.id
                                                onSelect(incident.id)
                                            }
                                        },
                                    )
                                    .heightIn(min = 56.dp)
                                    .padding(16.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp),
                            ) {
                                RiverText(
                                    if (incident.available) incident.label else "${incident.label} · Unavailable",
                                    emphasisStyle,
                                )
                                RiverText(incident.severity.uppercase(Locale.ROOT), supportingStyle.copy(fontWeight = FontWeight.SemiBold))
                                if (!incident.available) {
                                    RiverText(incident.unavailableReason, supportingStyle)
                                }
                            }
                        }
                        if (expanded && selected?.id == incident.id) {
                            RiverText(incident.detail, bodyStyle, Modifier.padding(start = 24.dp, top = 4.dp, bottom = 4.dp))
                        }
                    }
                }
            }
        }

        RiverText(
            selected?.let { "Reviewing: ${it.label}" } ?: "No alert selected",
            emphasisStyle,
            Modifier.padding(top = 8.dp).testTag("river.summary"),
        )

        Box(Modifier.padding(top = 8.dp)) {
            Box(
                Modifier.fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(if (selected == null) colors.disabled else colors.enabled)
                    .testTag("river.submit")
                    .clickable(enabled = selected != null, role = Role.Button) {
                        selected?.let { onAcknowledge(it.id) }
                    }
                    .heightIn(min = 56.dp)
                    .padding(horizontal = 18.dp, vertical = 16.dp),
            ) {
                RiverText("Acknowledge alert", emphasisStyle.copy(color = colors.onAction))
            }
        }

        RiverText(model.footer, supportingStyle, Modifier.padding(top = 8.dp).testTag("river.footer"))
    }
}

@Composable
private fun RiverText(text: String, style: TextStyle, modifier: Modifier = Modifier) {
    Text(
        text = text,
        modifier = modifier.fillMaxWidth(),
        style = style,
        softWrap = true,
        overflow = TextOverflow.Visible,
    )
}

private class RiverColors(private val dark: Boolean) {
    private fun color(light: Long, night: Long) = Color(if (dark) night else light)
    val canvas = color(0xFFF5F2EB, 0xFF14282D)
    val notice = color(0xFFE7DED0, 0xFF2D4245)
    val enabled = color(0xFF315F68, 0xFF8CC7C7)
    val disabled = color(0xFFAAA99F, 0xFF52666A)
    val ink = color(0xFF172D32, 0xFFE6F1EF)
    val surface = color(0xFFFFFFFF, 0xFF20383D)
    val selected = color(0xFFD6E6E5, 0xFF31575C)
    val onAction = color(0xFFF8FBFA, 0xFF102D30)
}
