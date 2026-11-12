package com.example.reply.ui.components.business

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class CandidateDispositionInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val portfolioScore: Int,
    val reviewerCapacity: Int,
    val technicalSlots: Int,
    val recruiterSlots: Int,
    val legalHold: Boolean,
    val assessmentCount: Int,
    val openRoleCount: Int,
)

private enum class CandidateDispositionRoot(val stableID: String, val label: String) {
    Continue("continue", "Continue review"),
    Archive("archive", "Archive application");

    fun isEligible(input: CandidateDispositionInput): Boolean = when (this) {
        Continue -> input.portfolioScore >= 60 && input.reviewerCapacity >= 1
        Archive -> !input.legalHold
    }
}

private enum class CandidateDispositionDetail(val stableID: String, val label: String) {
    Technical("technical", "Technical interview"),
    Recruiter("recruiter", "Recruiter screen"),
    SkillsGap("skills-gap", "Skills gap"),
    RoleClosed("role-closed", "Role closed");

    fun isEligible(root: CandidateDispositionRoot?, input: CandidateDispositionInput): Boolean {
        if (root == null || !root.isEligible(input)) return false
        return when (this) {
            Technical -> root == CandidateDispositionRoot.Continue && input.portfolioScore >= 75 && input.technicalSlots >= 1
            Recruiter -> root == CandidateDispositionRoot.Continue && input.recruiterSlots >= 1
            SkillsGap -> root == CandidateDispositionRoot.Archive && input.assessmentCount >= 1
            RoleClosed -> root == CandidateDispositionRoot.Archive && input.openRoleCount == 0
        }
    }
}

private data class CandidateDispositionState(
    val entityID: String,
    val revision: Int,
    val root: CandidateDispositionRoot? = null,
    val detail: CandidateDispositionDetail? = null,
    val confirmed: Boolean = false,
    val recorded: Boolean = false,
) {
    fun reconciled(input: CandidateDispositionInput): CandidateDispositionState {
        if (entityID != input.entityID || revision != input.revision) {
            return CandidateDispositionState(input.entityID, input.revision)
        }
        return when {
            root != null && !root.isEligible(input) -> copy(
                root = null, detail = null, confirmed = false, recorded = false,
            )
            detail != null && !detail.isEligible(root, input) -> copy(
                detail = null, confirmed = false, recorded = false,
            )
            else -> this
        }
    }

    fun hasValidSelection(input: CandidateDispositionInput): Boolean =
        root != null && root.isEligible(input) && detail != null && detail.isEligible(root, input)

    fun canRecord(input: CandidateDispositionInput): Boolean =
        !recorded && confirmed && hasValidSelection(input)

    fun summary(input: CandidateDispositionInput): String =
        "Disposition: ${root?.label ?: "Not chosen"}. Detail: ${detail?.label ?: "Not chosen"}. ${input.portfolioScore} portfolio points."

    fun status(input: CandidateDispositionInput): String = when {
        recorded -> "Recorded. Selections are locked for this request."
        CandidateDispositionRoot.entries.none { it.isEligible(input) } ->
            "No disposition is eligible for these request details."
        root == null -> "Choose a disposition."
        detail == null -> "Choose a next step or reason for ${root.label}."
        !confirmed -> "Confirm the evidence review to continue."
        else -> "Ready to record candidate disposition."
    }
}

private object CandidateDispositionColors {
    val Surface = Color(0xFFF7F9FC)
    val Row = Color(0xFFFFFFFF)
    val Selected = Color(0xFFE5F1FF)
    val Accent = Color(0xFF2459A6)
    val Disabled = Color(0xFFD9E1EC)
    val Ink = Color(0xFF15243B)
    val Muted = Color(0xFF526174)
    val Outline = Color(0xFFB8C5D6)
}

private val candidateDispositionBodyStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 15.sp,
    fontWeight = FontWeight.Normal,
    letterSpacing = 0.sp,
)
private val candidateDispositionSectionStyle = candidateDispositionBodyStyle.copy(
    fontSize = 16.sp,
    fontWeight = FontWeight.SemiBold,
)
private val candidateDispositionTitleStyle = candidateDispositionBodyStyle.copy(
    fontSize = 24.sp,
    fontWeight = FontWeight.SemiBold,
)

@Composable
fun CandidateDispositionReview(input: CandidateDispositionInput, onEvent: (String) -> Unit) {
    var state by remember { mutableStateOf(CandidateDispositionState(input.entityID, input.revision)) }
    // Reconcile before emitting any UI for the replacement input, retaining only valid state.
    val current = state.reconciled(input)
    if (state != current) state = current

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(CandidateDispositionColors.Surface, RoundedCornerShape(12.dp))
            .testTag("candidate-disposition.surface")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        CandidateDispositionText(input.title, "candidate-disposition.title", candidateDispositionTitleStyle, CandidateDispositionColors.Ink)
        CandidateDispositionText(input.context, "candidate-disposition.context")
        CandidateDispositionText(input.notes.joinToString("\n\n"), "candidate-disposition.notes")
        Text("Disposition", style = candidateDispositionSectionStyle, color = CandidateDispositionColors.Ink)
        CandidateDispositionRoot.entries.forEach { root ->
            CandidateDispositionChoice(
                label = root.label,
                isSelected = current.root == root,
                enabled = !current.recorded && root.isEligible(input),
            ) {
                val next = state.reconciled(input)
                if (!next.recorded && root.isEligible(input)) {
                    state = if (next.root == root) next else next.copy(root = root, detail = null, confirmed = false)
                }
            }
        }
        Text("Detail", style = candidateDispositionSectionStyle, color = CandidateDispositionColors.Ink)
        CandidateDispositionDetail.entries.forEach { detail ->
            CandidateDispositionChoice(
                label = detail.label,
                isSelected = current.detail == detail,
                enabled = !current.recorded && detail.isEligible(current.root, input),
            ) {
                val next = state.reconciled(input)
                if (!next.recorded && detail.isEligible(next.root, input)) {
                    state = if (next.detail == detail) next else next.copy(detail = detail, confirmed = false)
                }
            }
        }
        CandidateDispositionText(current.summary(input), "candidate-disposition.summary", candidateDispositionSectionStyle, CandidateDispositionColors.Ink)
        CandidateDispositionChoice(
            label = "I confirm the evidence review",
            isSelected = current.confirmed,
            enabled = !current.recorded && current.hasValidSelection(input),
        ) {
            val next = state.reconciled(input)
            if (!next.recorded && next.hasValidSelection(input)) {
                state = next.copy(confirmed = !next.confirmed)
            }
        }
        CandidateDispositionText(current.status(input), "candidate-disposition.status")
        CandidateDispositionText(
            if (current.recorded) "Candidate disposition recorded." else "No request recorded.",
            "candidate-disposition.receipt",
        )
        Button(
            onClick = {
                val next = state.reconciled(input)
                val root = next.root
                val detail = next.detail
                if (next.canRecord(input) && root != null && detail != null) {
                    onEvent("candidate|${input.entityID}|${input.revision}|${root.stableID}|${detail.stableID}|${input.portfolioScore}")
                    state = next.copy(recorded = true)
                }
            },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            enabled = current.canRecord(input),
            shape = RoundedCornerShape(8.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = CandidateDispositionColors.Accent,
                contentColor = CandidateDispositionColors.Row,
                disabledContainerColor = CandidateDispositionColors.Disabled,
                disabledContentColor = CandidateDispositionColors.Muted,
            ),
            elevation = null,
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(
                "Record candidate disposition",
                modifier = Modifier.fillMaxWidth(),
                style = candidateDispositionSectionStyle,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun CandidateDispositionText(
    value: String,
    tag: String,
    style: TextStyle = candidateDispositionBodyStyle,
    color: Color = CandidateDispositionColors.Muted,
) {
    Text(
        text = value,
        modifier = Modifier.fillMaxWidth().testTag(tag),
        color = color,
        style = style,
        textAlign = TextAlign.Start,
        softWrap = true,
    )
}

@Composable
private fun CandidateDispositionChoice(
    label: String,
    isSelected: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val fill = if (isSelected) CandidateDispositionColors.Selected else CandidateDispositionColors.Row
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .semantics { selected = isSelected },
        enabled = enabled,
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = fill,
            contentColor = CandidateDispositionColors.Ink,
            disabledContainerColor = fill,
            disabledContentColor = CandidateDispositionColors.Muted,
        ),
        elevation = null,
        border = BorderStroke(
            if (isSelected) 2.dp else 1.dp,
            if (isSelected) CandidateDispositionColors.Accent else CandidateDispositionColors.Outline,
        ),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                label,
                modifier = Modifier.weight(1f),
                style = candidateDispositionBodyStyle,
                textAlign = TextAlign.Start,
                softWrap = true,
            )
            if (isSelected) {
                Text(
                    "✓",
                    modifier = Modifier.clearAndSetSemantics { },
                    style = candidateDispositionBodyStyle.copy(fontSize = 16.sp),
                    color = if (enabled) CandidateDispositionColors.Accent else CandidateDispositionColors.Muted,
                )
            }
        }
    }
}
