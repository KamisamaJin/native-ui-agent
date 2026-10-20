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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

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

private data class ConditionColors(
    val canvas: Color,
    val surface: Color,
    val ink: Color,
    val muted: Color,
    val accent: Color,
    val border: Color,
    val primaryInk: Color,
)

@Composable
private fun conditionColors(): ConditionColors = if (isSystemInDarkTheme()) {
    ConditionColors(
        Color(0xFF1C1424), Color(0xFF2A1D36), Color(0xFFEADDF6),
        Color(0xFFC8B5D9), Color(0xFFD5B6F5), Color(0xFF634E75), Color(0xFF1C1424),
    )
} else {
    ConditionColors(
        Color(0xFFFFFFFF), Color(0xFFF6F1FA), Color(0xFF432D58),
        Color(0xFF746181), Color(0xFF7750A6), Color(0xFFDACDE5), Color(0xFFFFFFFF),
    )
}

private fun CollectionConditionAssessment.isComplete(): Boolean =
    status == "stable" || (status == "care" && reason in listOf("surface", "structure"))

private fun CollectionConditionObject.initialAssessment() = CollectionConditionAssessment(
    id = id,
    status = status,
    reason = if (status == "care") reason else null,
)

private fun conditionStatusName(status: String): String = when (status) {
    "stable" -> "Stable"
    "care" -> "Needs care"
    else -> "Pending"
}

@Composable
public fun CollectionConditionReviewPanel(
    request: CollectionConditionReviewRequest,
    onConfirm: (String, List<CollectionConditionAssessment>) -> Unit,
) {
    val colors = conditionColors()
    var decisions by remember(request.id) {
        mutableStateOf(request.objects.associate { it.id to it.initialAssessment() })
    }
    var focusID by remember(request.id) {
        mutableStateOf(request.objects.firstOrNull { it.id == request.focusID }?.id
            ?: request.objects.firstOrNull()?.id)
    }
    fun assessment(item: CollectionConditionObject): CollectionConditionAssessment =
        decisions[item.id] ?: item.initialAssessment()

    val focused = request.objects.firstOrNull { it.id == focusID } ?: request.objects.firstOrNull()
    val completed = request.objects.count { assessment(it).isComplete() }
    val followUps = request.objects.count { assessment(it).status == "care" }
    val remaining = request.objects.count { it.required && !assessment(it).isComplete() }
    val ready = remaining == 0
    val missingCategory = request.objects.any {
        it.required && assessment(it).status == "care" && !assessment(it).isComplete()
    }
    val validation = when {
        missingCategory -> "Choose a care category"
        remaining > 0 -> "$remaining required decision${if (remaining == 1) "" else "s"} remaining"
        else -> "Ready to submit"
    }
    val summary = "$completed of ${request.objects.size} reviewed • $followUps follow-up${if (followUps == 1) "" else "s"}"

    fun classify(item: CollectionConditionObject, status: String) {
        if (!item.editable || item.id != focused?.id) return
        val old = assessment(item)
        decisions = decisions + (item.id to CollectionConditionAssessment(
            item.id, status, if (status == "care" && old.status == "care") old.reason else null,
        ))
    }
    fun setReason(item: CollectionConditionObject, reason: String) {
        if (!item.editable || item.id != focused?.id || assessment(item).status != "care") return
        decisions = decisions + (item.id to CollectionConditionAssessment(item.id, "care", reason))
    }

    Column(
        modifier = Modifier.fillMaxWidth().background(colors.canvas),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            ConditionText(request.title, 22, colors.ink, FontWeight.Bold, "condition.title")
            ConditionText(request.context, 14, colors.muted)
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            ConditionText("Inspection queue", 16, colors.ink, FontWeight.SemiBold)
            request.objects.forEachIndexed { index, item ->
                ConditionChoice(
                    label = "${item.title}, ${conditionStatusName(assessment(item).status)}",
                    identifier = "condition.queue${index + 1}",
                    selected = focused?.id == item.id,
                    enabled = true,
                    colors = colors,
                    minHeight = 64.dp,
                    width = request.queueWidth.dp,
                    onClick = { focusID = item.id },
                )
            }
        }
        if (focused != null) {
            val value = assessment(focused)
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ConditionText("Object inspector", 13, colors.accent, FontWeight.SemiBold)
                    ConditionText(focused.title, 20, colors.ink, FontWeight.SemiBold, "condition.focused")
                    ConditionText(focused.material, 14, colors.muted)
                    if (!focused.editable) ConditionText("Read only", 14, colors.muted, FontWeight.SemiBold)
                }
                ConditionText(focused.inspectionNote, 14, colors.muted, identifier = "condition.inspectionNote")
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ConditionChoice("Stable", "condition.stable", value.status == "stable", focused.editable, colors) {
                        classify(focused, "stable")
                    }
                    ConditionChoice("Needs care", "condition.care", value.status == "care", focused.editable, colors) {
                        classify(focused, "care")
                    }
                }
                if (value.status == "care") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        ConditionText("Care category", 14, colors.ink, FontWeight.SemiBold, "condition.reasonGroup")
                        ConditionChoice("Surface", "condition.surface", value.reason == "surface", focused.editable,
                            colors, exactHeight = 48.dp) { setReason(focused, "surface") }
                        ConditionChoice("Structure", "condition.structure", value.reason == "structure", focused.editable,
                            colors, exactHeight = 48.dp) { setReason(focused, "structure") }
                    }
                }
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            ConditionText(summary, 18, colors.ink, FontWeight.SemiBold, "condition.summary")
            ConditionText(validation, 14, colors.accent, FontWeight.SemiBold, "condition.validation")
            ConditionPrimary(ready, colors) {
                if (ready) onConfirm(request.id, request.objects.map { assessment(it) }.sortedBy { it.id })
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            ConditionText("Review notes", 16, colors.ink, FontWeight.SemiBold, "condition.notes")
            request.notes.forEach { ConditionText(it, 14, colors.muted) }
        }
    }
}

@Composable
private fun ConditionText(
    value: String,
    size: Int,
    color: Color,
    weight: FontWeight = FontWeight.Normal,
    identifier: String? = null,
) {
    Text(
        text = value,
        modifier = Modifier.fillMaxWidth().then(if (identifier == null) Modifier else Modifier.testTag(identifier)),
        color = color,
        style = TextStyle(
            fontFamily = FontFamily.SansSerif,
            fontSize = size.sp,
            fontWeight = weight,
            lineHeight = (size * 1.3f).sp,
        ),
        softWrap = true,
    )
}

@Composable
private fun ConditionChoice(
    label: String,
    identifier: String,
    selected: Boolean,
    enabled: Boolean,
    colors: ConditionColors,
    minHeight: Dp = 48.dp,
    exactHeight: Dp? = null,
    width: Dp? = null,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(10.dp)
    val sizeModifier = if (width != null) Modifier.width(width) else Modifier.fillMaxWidth()
    val heightModifier = if (exactHeight != null) Modifier.height(exactHeight) else Modifier.heightIn(min = minHeight)
    Box(
        modifier = sizeModifier.then(heightModifier)
            .clip(shape)
            .background(if (enabled) colors.surface else colors.border)
            .border(1.dp, if (selected) colors.accent else colors.border, shape)
            .testTag(identifier)
            .selectable(selected = selected, enabled = enabled, role = Role.Button, onClick = onClick)
            .semantics(mergeDescendants = true) { contentDescription = label },
        contentAlignment = Alignment.CenterStart,
    ) {
        Text(
            text = label,
            color = if (enabled) colors.ink else colors.muted,
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = if (exactHeight == null) 12.dp else 0.dp),
            style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold, lineHeight = 20.8.sp),
            softWrap = true,
        )
        if (selected) {
            Box(Modifier.align(Alignment.TopEnd).padding(4.dp).size(4.dp).background(colors.accent, CircleShape))
        }
    }
}

@Composable
private fun ConditionPrimary(enabled: Boolean, colors: ConditionColors, onClick: () -> Unit) {
    val shape = RoundedCornerShape(10.dp)
    Box(
        modifier = Modifier.fillMaxWidth().height(56.dp)
            .clip(shape)
            .background(if (enabled) colors.accent else colors.border)
            .testTag("condition.primary")
            .selectable(selected = false, enabled = enabled, role = Role.Button, onClick = onClick)
            .semantics(mergeDescendants = true) { contentDescription = "Submit review" },
        contentAlignment = Alignment.CenterStart,
    ) {
        Text(
            "Submit review",
            modifier = Modifier.padding(horizontal = 12.dp),
            color = if (enabled) colors.primaryInk else colors.muted,
            style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold, lineHeight = 20.8.sp),
            softWrap = true,
        )
    }
}
