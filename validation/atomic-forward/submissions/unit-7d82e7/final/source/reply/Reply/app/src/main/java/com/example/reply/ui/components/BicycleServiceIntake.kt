package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

public data class BicycleServiceOption(
    val id: String,
    val label: String,
    val detail: String,
    val available: Boolean,
    val unavailableReason: String,
    val minutes: Int,
)

public data class BicycleServiceIntakeModel(
    val revision: String,
    val title: String,
    val subtitle: String,
    val notice: String,
    val footer: String,
    val guidance: String,
    val initialSelectedIDs: List<String>,
    val initialDetailsExpanded: Boolean,
    val services: List<BicycleServiceOption>,
)

@Composable
public fun BicycleServiceIntake(
    model: BicycleServiceIntakeModel,
    onToggle: (String, Boolean) -> Unit,
    onSubmit: (List<String>) -> Unit,
    onDetailsChange: (Boolean) -> Unit,
) {
    val palette = BicyclePalette(isSystemInDarkTheme())
    var selectedIDs by remember(model.revision) {
        mutableStateOf(model.initialSelectedIDs.toSet().intersect(model.services.filter { it.available }.map { it.id }.toSet()))
    }
    var detailsExpanded by remember(model.revision) { mutableStateOf(model.initialDetailsExpanded) }
    val selectedServices = model.services.filter { it.available && it.id in selectedIDs }
    val summary = if (selectedServices.isEmpty()) {
        "No work selected · 0 min"
    } else {
        "Work: ${selectedServices.joinToString(" + ") { it.label }} · ${selectedServices.sumOf { it.minutes }} min"
    }
    val disclosureLabel = if (detailsExpanded) "Hide handover notes" else "Show handover notes"

    Column(
        modifier = Modifier.fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(palette.canvas)
            .testTag("bicycle.canvas")
            .semantics(mergeDescendants = false) {}
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            BicycleCopy(model.title, palette.ink, size = 22, weight = FontWeight.SemiBold,
                modifier = Modifier.testTag("bicycle.title").semantics { heading() })
            BicycleCopy(model.subtitle, palette.ink)
            Box(
                Modifier.fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(palette.notice)
                    .testTag("bicycle.notice")
                    .semantics(mergeDescendants = true) {}
                    .padding(16.dp),
            ) {
                BicycleCopy(model.notice, palette.ink)
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
            val groups = listOf(
                "Inspection" to model.services.filter { it.id == "a" || it.id == "b" },
                "Specialist work" to model.services.filter { it.id == "c" },
                "Care and adjustments" to model.services.filter { it.id !in setOf("a", "b", "c") },
            )
            groups.forEach { (name, services) ->
                if (services.isNotEmpty()) {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        BicycleCopy(name, palette.ink, weight = FontWeight.SemiBold,
                            modifier = Modifier.semantics { heading() })
                        services.forEach { service ->
                            val selected = service.available && service.id in selectedIDs
                            BicycleServiceButton(service, selected, palette) {
                                val next = service.id !in selectedIDs
                                selectedIDs = if (next) selectedIDs + service.id else selectedIDs - service.id
                                onToggle(service.id, next)
                            }
                        }
                    }
                }
            }
        }

        BicycleCopy(summary, palette.ink, weight = FontWeight.SemiBold,
            modifier = Modifier.testTag("bicycle.summary"))

        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            TextButton(
                onClick = {
                    detailsExpanded = !detailsExpanded
                    onDetailsChange(detailsExpanded)
                },
                modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("bicycle.disclosure"),
                shape = RectangleShape,
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.textButtonColors(contentColor = palette.ink),
            ) {
                BicycleCopy(disclosureLabel, palette.ink, weight = FontWeight.SemiBold)
            }
            if (detailsExpanded) BicycleCopy(model.guidance, palette.ink)
        }

        Button(
            onClick = { if (selectedServices.isNotEmpty()) onSubmit(selectedServices.map { it.id }) },
            enabled = selectedServices.isNotEmpty(),
            modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("bicycle.submit"),
            shape = RoundedCornerShape(10.dp),
            contentPadding = PaddingValues(16.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = palette.enabled,
                contentColor = palette.onAction,
                disabledContainerColor = palette.disabled,
                disabledContentColor = palette.onAction,
            ),
        ) {
            BicycleCopy("Send service draft", palette.onAction, weight = FontWeight.SemiBold)
        }
        BicycleCopy(model.footer, palette.ink, size = 14, modifier = Modifier.testTag("bicycle.footer"))
    }
}

@Composable
private fun BicycleServiceButton(
    service: BicycleServiceOption,
    selected: Boolean,
    palette: BicyclePalette,
    onToggle: () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth()
            .heightIn(min = 56.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(if (selected) palette.selected else palette.surface)
            .testTag("bicycle.choice.${service.id}")
            .selectable(selected = selected, enabled = service.available, role = Role.Button,
                onClick = { if (service.available) onToggle() })
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(if (selected) "☑" else "☐", color = palette.ink, fontSize = 16.sp,
                modifier = Modifier.clearAndSetSemantics {})
            BicycleCopy(service.label + if (service.available) "" else " · Unavailable",
                palette.ink, weight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
        }
        if (!service.available) BicycleCopy(service.unavailableReason, palette.ink, size = 14)
        if (service.detail.isNotEmpty()) BicycleCopy(service.detail, palette.ink, size = 14)
    }
}

@Composable
private fun BicycleCopy(
    text: String,
    color: Color,
    size: Int = 16,
    weight: FontWeight = FontWeight.Normal,
    modifier: Modifier = Modifier,
) {
    Text(
        text = text,
        modifier = modifier.fillMaxWidth(),
        color = color,
        style = TextStyle(fontSize = size.sp, fontWeight = weight, textAlign = TextAlign.Start),
        softWrap = true,
    )
}

private class BicyclePalette(dark: Boolean) {
    val canvas = Color(if (dark) 0xFF14282D else 0xFFF5F2EB)
    val notice = Color(if (dark) 0xFF2D4245 else 0xFFE7DED0)
    val enabled = Color(if (dark) 0xFF8CC7C7 else 0xFF315F68)
    val disabled = Color(if (dark) 0xFF52666A else 0xFFAAA99F)
    val ink = Color(if (dark) 0xFFE6F1EF else 0xFF172D32)
    val surface = Color(if (dark) 0xFF20383D else 0xFFFFFFFF)
    val selected = Color(if (dark) 0xFF31575C else 0xFFD6E6E5)
    val onAction = Color(if (dark) 0xFF102D30 else 0xFFF8FBFA)
}
