package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
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
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class BicycleServiceOption(
    val id: String,
    val label: String,
    val detail: String,
    val available: Boolean,
    val unavailableReason: String,
    val minutes: Int,
)

data class BicycleServiceIntakeModel(
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
fun BicycleServiceIntake(
    model: BicycleServiceIntakeModel,
    onToggle: (String, Boolean) -> Unit,
    onSubmit: (List<String>) -> Unit,
    onDetailsChange: (Boolean) -> Unit,
) {
    val palette = bicyclePalette(isSystemInDarkTheme())
    var selectedIDs by remember(model.revision) {
        mutableStateOf(model.initialSelectedIDs.toSet().intersect(
            model.services.filter { it.available }.map { it.id }.toSet()
        ))
    }
    var detailsExpanded by remember(model.revision) {
        mutableStateOf(model.initialDetailsExpanded)
    }
    val chosen = model.services.filter { it.available && it.id in selectedIDs }
    val summary = if (chosen.isEmpty()) "No work selected · 0 min"
        else "Work: ${chosen.joinToString(" + ") { it.label }} · ${chosen.sumOf { it.minutes }} min"

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(palette.canvas, RoundedCornerShape(12.dp))
            .semantics(mergeDescendants = false) { }
            .testTag("bicycle.canvas")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            BicycleCopy(
                model.title, palette.ink,
                modifier = Modifier.testTag("bicycle.title").semantics { heading() },
                fontSize = 22, weight = FontWeight.SemiBold,
            )
            BicycleCopy(model.subtitle, palette.ink)
            BicycleCopy(
                model.notice, palette.ink,
                modifier = Modifier.fillMaxWidth()
                    .background(palette.notice, RoundedCornerShape(10.dp))
                    .testTag("bicycle.notice")
                    .padding(16.dp),
            )
        }

        val groups = listOf(
            "Inspection" to model.services.filter { it.id == "a" || it.id == "b" },
            "Specialist work" to model.services.filter { it.id == "c" },
            "Care and adjustments" to model.services.filter { it.id !in setOf("a", "b", "c") },
        )
        groups.forEach { (groupTitle, services) ->
            if (services.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    BicycleCopy(groupTitle, palette.ink,
                        modifier = Modifier.semantics { heading() },
                        weight = FontWeight.SemiBold)
                    services.forEach { service ->
                        val selected = service.available && service.id in selectedIDs
                        Column(
                            modifier = Modifier.fillMaxWidth()
                                .heightIn(min = 56.dp)
                                .clip(RoundedCornerShape(10.dp))
                                .background(if (selected) palette.selected else palette.surface)
                                .selectable(
                                    selected = selected,
                                    enabled = service.available,
                                    role = Role.Button,
                                    onClick = {
                                        val nextSelected = service.id !in selectedIDs
                                        selectedIDs = if (nextSelected) selectedIDs + service.id
                                            else selectedIDs - service.id
                                        onToggle(service.id, nextSelected)
                                    },
                                )
                                .testTag("bicycle.choice.${service.id}")
                                .padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            BicycleCopy(
                                "${if (selected) "☑" else "☐"} ${service.label}" +
                                    if (service.available) "" else " · Unavailable",
                                palette.ink, weight = FontWeight.SemiBold,
                            )
                            if (!service.available) {
                                BicycleCopy(service.unavailableReason, palette.ink, fontSize = 14)
                            }
                            if (service.detail.isNotEmpty()) {
                                BicycleCopy(service.detail, palette.ink, fontSize = 14)
                            }
                        }
                    }
                }
            }
        }

        BicycleCopy(summary, palette.ink,
            modifier = Modifier.testTag("bicycle.summary"), weight = FontWeight.SemiBold)

        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            TextButton(
                onClick = {
                    detailsExpanded = !detailsExpanded
                    onDetailsChange(detailsExpanded)
                },
                modifier = Modifier.fillMaxWidth().testTag("bicycle.disclosure"),
                shape = RectangleShape,
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.textButtonColors(contentColor = palette.ink),
            ) {
                BicycleCopy(if (detailsExpanded) "Hide handover notes" else "Show handover notes",
                    palette.ink, weight = FontWeight.SemiBold)
            }
            if (detailsExpanded) {
                BicycleCopy(model.guidance, palette.ink)
            }
        }

        Button(
            onClick = { onSubmit(chosen.map { it.id }) },
            enabled = chosen.isNotEmpty(),
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

        BicycleCopy(model.footer, palette.ink,
            modifier = Modifier.testTag("bicycle.footer"), fontSize = 14)
    }
}

@Composable
private fun BicycleCopy(
    value: String,
    color: Color,
    modifier: Modifier = Modifier,
    fontSize: Int = 16,
    weight: FontWeight = FontWeight.Normal,
) {
    Text(
        text = value,
        modifier = modifier.fillMaxWidth(),
        color = color,
        style = TextStyle(
            fontSize = fontSize.sp,
            fontWeight = weight,
            lineHeight = (fontSize * 1.3f).sp,
            textAlign = TextAlign.Start,
        ),
        softWrap = true,
    )
}

private data class BicyclePalette(
    val canvas: Color,
    val notice: Color,
    val enabled: Color,
    val disabled: Color,
    val ink: Color,
    val surface: Color,
    val selected: Color,
    val onAction: Color,
)

private fun bicyclePalette(dark: Boolean) = if (dark) BicyclePalette(
    canvas = Color(0xFF14282D), notice = Color(0xFF2D4245),
    enabled = Color(0xFF8CC7C7), disabled = Color(0xFF52666A),
    ink = Color(0xFFE6F1EF), surface = Color(0xFF20383D),
    selected = Color(0xFF31575C), onAction = Color(0xFF102D30),
) else BicyclePalette(
    canvas = Color(0xFFF5F2EB), notice = Color(0xFFE7DED0),
    enabled = Color(0xFF315F68), disabled = Color(0xFFAAA99F),
    ink = Color(0xFF172D32), surface = Color(0xFFFFFFFF),
    selected = Color(0xFFD6E6E5), onAction = Color(0xFFF8FBFA),
)
