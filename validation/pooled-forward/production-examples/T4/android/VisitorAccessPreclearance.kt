package com.example.reply.ui.components.business

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
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
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.reply.R

data class VisitorAccessInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val guestCount: Int,
    val sponsorActive: Boolean,
    val badgeTrainingComplete: Boolean,
    val researchCapacity: Int,
    val officeCapacity: Int,
    val verifiedIDs: Int,
    val labInductions: Int,
    val escortCount: Int,
)

private enum class VisitorAccessArea(val stableID: String, val label: String) {
    Research("research", "Research floor"),
    Office("office", "Office floor");

    fun isEligible(input: VisitorAccessInput): Boolean {
        if (!input.sponsorActive || input.guestCount <= 0) return false
        return when (this) {
            Research -> input.badgeTrainingComplete && input.guestCount <= input.researchCapacity
            Office -> input.guestCount <= input.officeCapacity
        }
    }
}

private enum class VisitorAccessCredential(val stableID: String, val label: String) {
    ResearchBadge("research-badge", "Research badge"),
    VisitorEscort("visitor-escort", "Visitor escort");

    fun isEligible(area: VisitorAccessArea?, input: VisitorAccessInput): Boolean {
        if (area == null || !area.isEligible(input)) return false
        return when (this) {
            ResearchBadge -> area == VisitorAccessArea.Research &&
                input.verifiedIDs >= input.guestCount && input.labInductions >= input.guestCount
            VisitorEscort -> input.escortCount >= input.guestCount
        }
    }
}

private data class VisitorAccessSelection(
    val entityID: String,
    val revision: Int,
    val area: VisitorAccessArea? = null,
    val credential: VisitorAccessCredential? = null,
    val confirmed: Boolean = false,
    val recorded: Boolean = false,
) {
    fun reconciled(input: VisitorAccessInput): VisitorAccessSelection = when {
        entityID != input.entityID || revision != input.revision ->
            VisitorAccessSelection(input.entityID, input.revision)
        area != null && !area.isEligible(input) ->
            copy(area = null, credential = null, confirmed = false, recorded = false)
        credential != null && !credential.isEligible(area, input) ->
            copy(credential = null, confirmed = false, recorded = false)
        else -> this
    }

    fun hasValidChoices(input: VisitorAccessInput): Boolean =
        area != null && area.isEligible(input) &&
            credential != null && credential.isEligible(area, input)

    fun canRecord(input: VisitorAccessInput): Boolean =
        !recorded && confirmed && hasValidChoices(input)

    fun summary(input: VisitorAccessInput): String =
        "Area: ${area?.label ?: "Not chosen"}. Credential: ${credential?.label ?: "Not chosen"}. ${input.guestCount} visitors."

    fun status(input: VisitorAccessInput): String = when {
        recorded -> "Recorded. Selections are locked for this request."
        VisitorAccessArea.entries.none { it.isEligible(input) } ->
            "No access area is eligible for these request details."
        area == null -> "Choose a access area."
        credential == null -> "Choose a credential route for ${area.label}."
        !confirmed -> "Confirm the visitor briefing to continue."
        else -> "Ready to record visitor clearance."
    }
}

private object VisitorAccessColors {
    val Surface = Color(0xFFF7F9FC)
    val Row = Color(0xFFFFFFFF)
    val Selected = Color(0xFFE5F1FF)
    val Accent = Color(0xFF2459A6)
    val Disabled = Color(0xFFD9E1EC)
    val Ink = Color(0xFF15243B)
    val Muted = Color(0xFF526174)
    val Outline = Color(0xFFB8C5D6)
}

private val VisitorBodyStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 15.sp,
    fontWeight = FontWeight.Normal,
    lineHeight = 21.sp,
    letterSpacing = 0.sp,
)

private val VisitorSectionStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 16.sp,
    fontWeight = FontWeight.SemiBold,
    lineHeight = 22.sp,
    letterSpacing = 0.sp,
)

private val VisitorTitleStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 24.sp,
    fontWeight = FontWeight.SemiBold,
    lineHeight = 30.sp,
    letterSpacing = 0.sp,
)

@Composable
fun VisitorAccessPreclearance(input: VisitorAccessInput, onEvent: (String) -> Unit) {
    var selection by remember { mutableStateOf(VisitorAccessSelection(input.entityID, input.revision)) }
    val current = selection.reconciled(input)
    // Conditional reconciliation stabilizes before children consume replacement facts.
    if (selection != current) selection = current

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(VisitorAccessColors.Surface, RoundedCornerShape(12.dp))
            .testTag("visitor-preclearance.surface")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        VisitorContentText(input.title, "visitor-preclearance.title", VisitorTitleStyle, VisitorAccessColors.Ink)
        VisitorContentText(input.context, "visitor-preclearance.context")
        VisitorContentText(input.notes.joinToString("\n\n"), "visitor-preclearance.notes")

        Text("Area", style = VisitorSectionStyle, color = VisitorAccessColors.Ink, textAlign = TextAlign.Start)
        VisitorAccessArea.entries.forEach { area ->
            VisitorChoiceButton(
                label = area.label,
                isSelected = current.area == area,
                enabled = !current.recorded && area.isEligible(input),
            ) {
                val next = selection.reconciled(input)
                if (!next.recorded && area.isEligible(input) && next.area != area) {
                    selection = next.copy(area = area, credential = null, confirmed = false)
                }
            }
        }

        Text("Credential", style = VisitorSectionStyle, color = VisitorAccessColors.Ink, textAlign = TextAlign.Start)
        VisitorAccessCredential.entries.forEach { credential ->
            VisitorChoiceButton(
                label = credential.label,
                isSelected = current.credential == credential,
                enabled = !current.recorded && credential.isEligible(current.area, input),
            ) {
                val next = selection.reconciled(input)
                if (!next.recorded && credential.isEligible(next.area, input) && next.credential != credential) {
                    selection = next.copy(credential = credential, confirmed = false)
                }
            }
        }

        VisitorContentText(
            current.summary(input), "visitor-preclearance.summary", VisitorSectionStyle, VisitorAccessColors.Ink,
        )
        VisitorChoiceButton(
            label = "I confirm the visitor briefing",
            isSelected = current.confirmed,
            enabled = !current.recorded && current.hasValidChoices(input),
        ) {
            val next = selection.reconciled(input)
            if (!next.recorded && next.hasValidChoices(input)) {
                selection = next.copy(confirmed = !next.confirmed)
            }
        }
        VisitorContentText(current.status(input), "visitor-preclearance.status")
        VisitorContentText(
            if (current.recorded) "Visitor clearance recorded." else "No request recorded.",
            "visitor-preclearance.receipt",
        )
        Button(
            onClick = {
                val next = selection.reconciled(input)
                val area = next.area
                val credential = next.credential
                if (next.canRecord(input) && area != null && credential != null) {
                    onEvent("visitor|${input.entityID}|${input.revision}|${area.stableID}|${credential.stableID}|${input.guestCount}")
                    selection = next.copy(recorded = true)
                }
            },
            enabled = current.canRecord(input),
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            shape = RoundedCornerShape(8.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = VisitorAccessColors.Accent,
                contentColor = VisitorAccessColors.Row,
                disabledContainerColor = VisitorAccessColors.Disabled,
                disabledContentColor = VisitorAccessColors.Muted,
            ),
            elevation = null,
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(
                "Record visitor clearance",
                modifier = Modifier.fillMaxWidth(),
                style = VisitorSectionStyle,
                textAlign = TextAlign.Center,
                softWrap = true,
            )
        }
    }
}

@Composable
private fun VisitorContentText(
    value: String,
    identifier: String,
    style: TextStyle = VisitorBodyStyle,
    color: Color = VisitorAccessColors.Muted,
) {
    Text(
        text = value,
        modifier = Modifier.fillMaxWidth().testTag(identifier),
        style = style,
        color = color,
        textAlign = TextAlign.Start,
        softWrap = true,
    )
}

@Composable
private fun VisitorChoiceButton(
    label: String,
    isSelected: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val fill = if (isSelected) VisitorAccessColors.Selected else VisitorAccessColors.Row
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .semantics { selected = isSelected },
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = fill,
            contentColor = VisitorAccessColors.Ink,
            disabledContainerColor = fill,
            disabledContentColor = VisitorAccessColors.Muted,
        ),
        border = BorderStroke(
            if (isSelected) 2.dp else 1.dp,
            if (isSelected) VisitorAccessColors.Accent else VisitorAccessColors.Outline,
        ),
        elevation = null,
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = label,
                modifier = Modifier.weight(1f),
                style = VisitorBodyStyle,
                textAlign = TextAlign.Start,
                softWrap = true,
            )
            if (isSelected) {
                Spacer(Modifier.width(12.dp))
                Icon(
                    painter = painterResource(R.drawable.ic_check),
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = if (enabled) VisitorAccessColors.Accent else VisitorAccessColors.Muted,
                )
            }
        }
    }
}
