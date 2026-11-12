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

/** Immutable caller-owned facts and content for an enrollment request. */
data class TrainingPathwayInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val completedHours: Int,
    val completedModules: List<String>,
    val cohortSeats: Int,
    val deviceCredits: Int,
    val assessmentSlots: Int,
    val practiceSeats: Int,
)

private enum class TrainingPathway(val id: String, val label: String) {
    Guided("guided", "Guided cohort"),
    Independent("independent", "Independent lab");

    fun isEligible(input: TrainingPathwayInput): Boolean {
        if (!input.completedModules.contains("foundation")) return false
        return when (this) {
            Guided -> input.completedHours >= 8 && input.cohortSeats >= 1
            Independent -> input.completedHours >= 4 && input.deviceCredits >= 2
        }
    }
}

private enum class TrainingParticipationMode(val id: String, val label: String) {
    Certificate("certificate", "Certificate assessment"),
    Practice("practice", "Practice only");

    fun isEligible(input: TrainingPathwayInput, pathway: TrainingPathway?): Boolean {
        if (pathway == null || !pathway.isEligible(input)) return false
        return when (this) {
            Certificate -> pathway == TrainingPathway.Guided &&
                input.completedHours >= 12 && input.assessmentSlots >= 1
            Practice -> input.practiceSeats >= 1
        }
    }
}

private data class TrainingEnrollmentState(
    val entityID: String,
    val revision: Int,
    val pathway: TrainingPathway? = null,
    val mode: TrainingParticipationMode? = null,
    val confirmed: Boolean = false,
    val recorded: Boolean = false,
) {
    /** Reconcile identity first, then parent eligibility, then dependent eligibility. */
    fun reconciled(input: TrainingPathwayInput): TrainingEnrollmentState {
        if (entityID != input.entityID || revision != input.revision) {
            return TrainingEnrollmentState(input.entityID, input.revision)
        }
        if (pathway != null && !pathway.isEligible(input)) {
            return copy(pathway = null, mode = null, confirmed = false, recorded = false)
        }
        if (mode != null && !mode.isEligible(input, pathway)) {
            return copy(mode = null, confirmed = false, recorded = false)
        }
        return this
    }

    fun hasValidChoices(input: TrainingPathwayInput): Boolean =
        pathway != null && mode != null && pathway.isEligible(input) && mode.isEligible(input, pathway)

    fun canRecord(input: TrainingPathwayInput): Boolean =
        !recorded && confirmed && hasValidChoices(input)

    fun summary(input: TrainingPathwayInput): String =
        "Pathway: ${pathway?.label ?: "Not chosen"}. Mode: ${mode?.label ?: "Not chosen"}. ${input.completedHours} completed hours."

    fun status(input: TrainingPathwayInput): String = when {
        recorded -> "Recorded. Selections are locked for this request."
        TrainingPathway.values().none { it.isEligible(input) } ->
            "No pathway is eligible for these request details."
        pathway == null -> "Choose a pathway."
        mode == null -> "Choose a participation mode for ${pathway.label}."
        !confirmed -> "Confirm the learning commitment to continue."
        else -> "Ready to record training enrollment."
    }
}

private object TrainingEnrollmentPalette {
    val surface = Color(0xFFF7F9FC)
    val row = Color(0xFFFFFFFF)
    val selected = Color(0xFFE5F1FF)
    val accent = Color(0xFF2459A6)
    val disabled = Color(0xFFD9E1EC)
    val ink = Color(0xFF15243B)
    val muted = Color(0xFF526174)
    val outline = Color(0xFFB8C5D6)
}

private val TrainingBodyStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 15.sp,
    fontWeight = FontWeight.Normal,
    lineHeight = 21.sp,
    letterSpacing = 0.sp,
)

private val TrainingSectionStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 16.sp,
    fontWeight = FontWeight.SemiBold,
    lineHeight = 22.sp,
    letterSpacing = 0.sp,
)

/** Expands vertically; scrolling remains with the host. */
@Composable
fun TrainingPathwayEnrollment(input: TrainingPathwayInput, onEvent: (String) -> Unit) {
    var state by remember {
        mutableStateOf(TrainingEnrollmentState(input.entityID, input.revision))
    }
    val current = state.reconciled(input)
    // A guarded state adjustment commits replacement invalidation before showing children.
    if (current != state) state = current

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(TrainingEnrollmentPalette.surface, RoundedCornerShape(12.dp))
            .testTag("training-pathway.surface")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        Text(
            text = input.title,
            modifier = Modifier.fillMaxWidth().testTag("training-pathway.title"),
            style = TextStyle(
                fontFamily = FontFamily.SansSerif,
                fontSize = 24.sp,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 30.sp,
                letterSpacing = 0.sp,
            ),
            color = TrainingEnrollmentPalette.ink,
            textAlign = TextAlign.Start,
        )
        TrainingBody(input.context, "training-pathway.context")
        TrainingBody(input.notes.joinToString("\n\n"), "training-pathway.notes")
        TrainingCaption("Pathway")
        TrainingPathway.values().forEach { pathway ->
            TrainingChoice(
                label = pathway.label,
                selected = current.pathway == pathway,
                enabled = !current.recorded && pathway.isEligible(input),
            ) {
                val next = state.reconciled(input)
                if (!next.recorded && pathway.isEligible(input) && next.pathway != pathway) {
                    state = next.copy(pathway = pathway, mode = null, confirmed = false)
                }
            }
        }
        TrainingCaption("Mode")
        TrainingParticipationMode.values().forEach { mode ->
            TrainingChoice(
                label = mode.label,
                selected = current.mode == mode,
                enabled = !current.recorded && mode.isEligible(input, current.pathway),
            ) {
                val next = state.reconciled(input)
                if (!next.recorded && mode.isEligible(input, next.pathway) && next.mode != mode) {
                    state = next.copy(mode = mode, confirmed = false)
                }
            }
        }
        Text(
            text = current.summary(input),
            modifier = Modifier.fillMaxWidth().testTag("training-pathway.summary"),
            style = TrainingSectionStyle,
            color = TrainingEnrollmentPalette.ink,
            textAlign = TextAlign.Start,
        )
        TrainingChoice(
            label = "I confirm the learning commitment",
            selected = current.confirmed,
            enabled = !current.recorded && current.hasValidChoices(input),
        ) {
            val next = state.reconciled(input)
            if (!next.recorded && next.hasValidChoices(input)) {
                state = next.copy(confirmed = !next.confirmed)
            }
        }
        TrainingBody(current.status(input), "training-pathway.status")
        TrainingBody(
            if (current.recorded) "Training enrollment recorded." else "No request recorded.",
            "training-pathway.receipt",
        )
        TrainingPrimary(enabled = current.canRecord(input)) {
            val next = state.reconciled(input)
            val pathway = next.pathway
            val mode = next.mode
            if (next.canRecord(input) && pathway != null && mode != null) {
                onEvent("training|${input.entityID}|${input.revision}|${pathway.id}|${mode.id}|${input.completedHours}")
                state = next.copy(recorded = true)
            }
        }
    }
}

@Composable
private fun TrainingBody(value: String, tag: String) {
    Text(
        text = value,
        modifier = Modifier.fillMaxWidth().testTag(tag),
        style = TrainingBodyStyle,
        color = TrainingEnrollmentPalette.muted,
        textAlign = TextAlign.Start,
    )
}

@Composable
private fun TrainingCaption(label: String) {
    Text(
        text = label,
        modifier = Modifier.fillMaxWidth(),
        style = TrainingSectionStyle,
        color = TrainingEnrollmentPalette.ink,
        textAlign = TextAlign.Start,
    )
}

@Composable
private fun TrainingChoice(
    label: String,
    selected: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val fill = if (selected) TrainingEnrollmentPalette.selected else TrainingEnrollmentPalette.row
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .semantics { this.selected = selected },
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = fill,
            contentColor = TrainingEnrollmentPalette.ink,
            disabledContainerColor = fill,
            disabledContentColor = TrainingEnrollmentPalette.muted,
        ),
        border = BorderStroke(
            if (selected) 2.dp else 1.dp,
            if (selected) TrainingEnrollmentPalette.accent else TrainingEnrollmentPalette.outline,
        ),
        elevation = null,
        contentPadding = PaddingValues(16.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = label,
                modifier = Modifier.weight(1f),
                style = TrainingBodyStyle.copy(lineHeight = 20.sp),
                color = if (enabled) TrainingEnrollmentPalette.ink else TrainingEnrollmentPalette.muted,
                textAlign = TextAlign.Start,
            )
            if (selected) {
                Text(
                    text = "✓",
                    modifier = Modifier.clearAndSetSemantics { },
                    style = TrainingSectionStyle,
                    color = if (enabled) TrainingEnrollmentPalette.accent else TrainingEnrollmentPalette.muted,
                )
            }
        }
    }
}

@Composable
private fun TrainingPrimary(enabled: Boolean, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = TrainingEnrollmentPalette.accent,
            contentColor = Color.White,
            disabledContainerColor = TrainingEnrollmentPalette.disabled,
            disabledContentColor = TrainingEnrollmentPalette.muted,
        ),
        elevation = null,
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Text(
            text = "Record training enrollment",
            modifier = Modifier.fillMaxWidth(),
            style = TrainingSectionStyle,
            color = if (enabled) Color.White else TrainingEnrollmentPalette.muted,
            textAlign = TextAlign.Center,
        )
    }
}
