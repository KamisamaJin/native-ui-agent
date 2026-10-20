package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.clickable

public data class CollectionConditionObject(
    val id: String,
    val title: String,
    val material: String,
    val inspectionNote: String,
    val status: String,
    val reason: String?,
    val editable: Boolean,
    val required: Boolean,
)

public data class CollectionConditionReviewRequest(
    val id: String,
    val title: String,
    val context: String,
    val focusID: String,
    val queueWidth: Double,
    val notes: List<String>,
    val objects: List<CollectionConditionObject>,
)

public data class CollectionConditionAssessment(
    val id: String,
    val status: String,
    val reason: String?,
)

private fun CollectionConditionAssessment.isComplete(): Boolean =
    status == "stable" || (status == "care" && reason in listOf("surface", "structure"))

@Composable
public fun CollectionConditionReviewPanel(
    request: CollectionConditionReviewRequest,
    onConfirm: (String, List<CollectionConditionAssessment>) -> Unit,
) {
    val palette = conditionPalette(isSystemInDarkTheme())
    var decisions by remember(request.id) {
        mutableStateOf(request.objects.associate { obj ->
            obj.id to CollectionConditionAssessment(obj.id, obj.status, obj.reason.takeIf { obj.status == "care" })
        })
    }
    var focusID by remember(request.id) {
        mutableStateOf(request.objects.firstOrNull { it.id == request.focusID }?.id ?: request.objects.firstOrNull()?.id)
    }
    fun decision(obj: CollectionConditionObject) = decisions[obj.id]
        ?: CollectionConditionAssessment(obj.id, obj.status, obj.reason.takeIf { obj.status == "care" })
    val completed = request.objects.count { decision(it).isComplete() }
    val careCount = request.objects.count { decision(it).status == "care" }
    val required = request.objects.filter { it.required }
    val remaining = required.count { !decision(it).isComplete() }
    val ready = remaining == 0
    val validation = when {
        required.any { decision(it).status == "care" && !decision(it).isComplete() } -> "Choose a care category"
        remaining > 0 -> "$remaining required decision${if (remaining == 1) "" else "s"} remaining"
        else -> "Ready to submit"
    }
    fun classify(obj: CollectionConditionObject, status: String) {
        if (!obj.editable || focusID != obj.id) return
        val old = decision(obj)
        decisions = decisions + (obj.id to CollectionConditionAssessment(obj.id, status,
            old.reason.takeIf { status == "care" && old.status == "care" }))
    }
    fun reason(obj: CollectionConditionObject, category: String) {
        if (!obj.editable || focusID != obj.id || decision(obj).status != "care") return
        decisions = decisions + (obj.id to CollectionConditionAssessment(obj.id, "care", category))
    }

    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            ConditionText(request.title, 22, FontWeight.Bold, palette.ink, Modifier.testTag("condition.title"))
            ConditionText(request.context, 14, FontWeight.Normal, palette.muted)
        }
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            ConditionText("Inspection queue", 16, FontWeight.SemiBold, palette.ink)
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                request.objects.forEachIndexed { index, obj ->
                    val status = when (decision(obj).status) {
                        "stable" -> "Stable"
                        "care" -> "Needs care"
                        else -> "Pending"
                    }
                    ConditionChoice(
                        label = "${obj.title}, $status",
                        identifier = "condition.queue${index + 1}",
                        selected = focusID == obj.id,
                        enabled = true,
                        palette = palette,
                        modifier = Modifier.width(request.queueWidth.dp),
                        minimumHeight = 64,
                    ) { focusID = obj.id }
                }
            }
        }
        val focused = request.objects.firstOrNull { it.id == focusID } ?: request.objects.firstOrNull()
        if (focused != null) {
            val current = decision(focused)
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                ConditionText("Object inspector", 13, FontWeight.SemiBold, palette.accent)
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ConditionText(focused.title, 20, FontWeight.SemiBold, palette.ink, Modifier.testTag("condition.focused"))
                    ConditionText(focused.material, 14, FontWeight.Normal, palette.muted)
                    if (!focused.editable) ConditionText("Read only", 13, FontWeight.SemiBold, palette.muted)
                }
                ConditionText(focused.inspectionNote, 14, FontWeight.Normal, palette.muted,
                    Modifier.testTag("condition.inspectionNote"))
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ConditionChoice("Stable", "condition.stable", current.status == "stable", focused.editable, palette) {
                        classify(focused, "stable")
                    }
                    ConditionChoice("Needs care", "condition.care", current.status == "care", focused.editable, palette) {
                        classify(focused, "care")
                    }
                }
                if (current.status == "care") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        ConditionText("Care category", 16, FontWeight.SemiBold, palette.ink,
                            Modifier.testTag("condition.reasonGroup"))
                        ConditionChoice("Surface", "condition.surface", current.reason == "surface", focused.editable,
                            palette, exactHeight = 48) { reason(focused, "surface") }
                        ConditionChoice("Structure", "condition.structure", current.reason == "structure", focused.editable,
                            palette, exactHeight = 48) { reason(focused, "structure") }
                    }
                }
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            ConditionText("$completed of ${request.objects.size} reviewed • $careCount follow-up${if (careCount == 1) "" else "s"}",
                18, FontWeight.SemiBold, palette.ink, Modifier.testTag("condition.summary"))
            ConditionText(validation, 14, FontWeight.SemiBold, palette.accent, Modifier.testTag("condition.validation"))
            val shape = RoundedCornerShape(10.dp)
            Box(
                Modifier.fillMaxWidth().height(56.dp)
                    .background(if (ready) palette.accent else palette.border, shape)
                    .testTag("condition.primary")
                    .clickable(enabled = ready, role = Role.Button) {
                        if (ready) onConfirm(request.id, request.objects.map { decision(it) }.sortedBy { it.id })
                    }
                    .padding(horizontal = 12.dp),
                contentAlignment = Alignment.CenterStart,
            ) {
                ConditionText("Submit review", 16, FontWeight.SemiBold, if (ready) palette.primaryInk else palette.muted)
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            ConditionText("Review notes", 16, FontWeight.SemiBold, palette.ink, Modifier.testTag("condition.notes"))
            request.notes.forEach { ConditionText(it, 14, FontWeight.Normal, palette.muted) }
        }
    }
}

@Composable
private fun ConditionText(
    value: String,
    size: Int,
    weight: FontWeight,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Text(value, modifier = modifier.fillMaxWidth(), color = color, softWrap = true,
        style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = size.sp, fontWeight = weight))
}

@Composable
private fun ConditionChoice(
    label: String,
    identifier: String,
    selected: Boolean,
    enabled: Boolean,
    palette: ConditionColors,
    modifier: Modifier = Modifier.fillMaxWidth(),
    minimumHeight: Int = 48,
    exactHeight: Int? = null,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(10.dp)
    val heightModifier = if (exactHeight == null) Modifier.heightIn(min = minimumHeight.dp) else Modifier.height(exactHeight.dp)
    Box(
        modifier.then(heightModifier)
            .background(if (enabled) palette.surface else palette.border, shape)
            .border(1.dp, if (selected) palette.accent else palette.border, shape)
            .testTag(identifier)
            .selectable(selected = selected, enabled = enabled, role = Role.Button, onClick = onClick)
            .semantics(mergeDescendants = true) { contentDescription = label },
        contentAlignment = Alignment.CenterStart,
    ) {
        ConditionText(label, 16, FontWeight.SemiBold, if (enabled) palette.ink else palette.muted,
            Modifier.padding(horizontal = 12.dp, vertical = if (exactHeight == null) 12.dp else 0.dp)
                .clearAndSetSemantics { })
        if (selected) {
            Box(Modifier.align(Alignment.TopEnd).padding(4.dp).size(4.dp).background(palette.accent, CircleShape))
        }
    }
}

private data class ConditionColors(
    val surface: Color,
    val ink: Color,
    val muted: Color,
    val accent: Color,
    val border: Color,
    val primaryInk: Color,
)

private fun conditionPalette(dark: Boolean) = if (dark) {
    ConditionColors(Color(0xFF2A1D36), Color(0xFFEADDF6), Color(0xFFC8B5D9), Color(0xFFD5B6F5), Color(0xFF634E75), Color(0xFF1C1424))
} else {
    ConditionColors(Color(0xFFF6F1FA), Color(0xFF432D58), Color(0xFF746181), Color(0xFF7750A6), Color(0xFFDACDE5), Color(0xFFFFFFFF))
}
