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

data class CateringPackageInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val guestCount: Int,
    val vegetarianGuests: Int,
    val vegetarianMeals: Int,
    val buffetCapacity: Int,
    val boxedCapacity: Int,
    val reusableSets: Int,
    val compostableSets: Int,
)

@Composable
fun CateringPackagePlanner(input: CateringPackageInput, onEvent: (String) -> Unit) {
    var state by remember { mutableStateOf(CateringPackageState(input.entityID, input.revision)) }
    // Reconcile before composing controls, committing invalidation so a later
    // replacement cannot restore a choice that previously became unavailable.
    val current = state.reconciled(input)
    if (current != state) state = current

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(CateringPackageColors.surface, RoundedCornerShape(12.dp))
            .testTag("catering-package.surface")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        Text(
            text = input.title,
            modifier = Modifier.fillMaxWidth().testTag("catering-package.title"),
            color = CateringPackageColors.ink,
            style = CateringTitleStyle,
            softWrap = true,
            textAlign = TextAlign.Start,
        )
        CateringSecondaryText(input.context, "catering-package.context")
        CateringSecondaryText(input.notes.joinToString("\n\n"), "catering-package.notes")

        CateringCaption("Package")
        CateringPackageChoice.values().forEach { choice ->
            CateringChoiceButton(
                label = choice.label,
                chosen = current.root == choice,
                enabled = !current.recorded && choice.isEligible(input),
            ) {
                val next = state.reconciled(input)
                if (!next.recorded && choice.isEligible(input)) {
                    state = if (next.root == choice) next else next.copy(
                        root = choice,
                        detail = null,
                        confirmed = false,
                    )
                }
            }
        }

        CateringCaption("Service")
        CateringServiceChoice.values().forEach { choice ->
            CateringChoiceButton(
                label = choice.label,
                chosen = current.detail == choice,
                enabled = !current.recorded && choice.isEligible(input, current.root),
            ) {
                val next = state.reconciled(input)
                if (!next.recorded && choice.isEligible(input, next.root)) {
                    state = if (next.detail == choice) next else next.copy(
                        detail = choice,
                        confirmed = false,
                    )
                }
            }
        }

        Text(
            text = current.summary(input),
            modifier = Modifier.fillMaxWidth().testTag("catering-package.summary"),
            color = CateringPackageColors.ink,
            style = CateringSectionStyle,
            softWrap = true,
            textAlign = TextAlign.Start,
        )
        CateringChoiceButton(
            label = "I confirm the dietary counts",
            chosen = current.confirmed,
            enabled = current.canConfirm(input),
        ) {
            val next = state.reconciled(input)
            if (next.canConfirm(input)) state = next.copy(confirmed = !next.confirmed)
        }
        CateringSecondaryText(current.status(input), "catering-package.status")
        CateringSecondaryText(
            if (current.recorded) "Catering order recorded." else "No request recorded.",
            "catering-package.receipt",
        )

        val recordEnabled = current.canRecord(input)
        Button(
            onClick = {
                val next = state.reconciled(input)
                val root = next.root
                val detail = next.detail
                if (root != null && detail != null && next.canRecord(input)) {
                    onEvent("catering|${input.entityID}|${input.revision}|${root.id}|${detail.id}|${input.guestCount}")
                    state = next.copy(recorded = true)
                }
            },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            enabled = recordEnabled,
            shape = RoundedCornerShape(8.dp),
            elevation = null,
            colors = ButtonDefaults.buttonColors(
                containerColor = CateringPackageColors.accent,
                contentColor = CateringPackageColors.onAccent,
                disabledContainerColor = CateringPackageColors.disabled,
                disabledContentColor = CateringPackageColors.muted,
            ),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(
                text = "Record catering order",
                modifier = Modifier.fillMaxWidth(),
                color = if (recordEnabled) CateringPackageColors.onAccent else CateringPackageColors.muted,
                style = CateringSectionStyle,
                softWrap = true,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun CateringCaption(label: String) {
    Text(
        text = label,
        modifier = Modifier.fillMaxWidth(),
        color = CateringPackageColors.ink,
        style = CateringSectionStyle,
        softWrap = true,
        textAlign = TextAlign.Start,
    )
}

@Composable
private fun CateringSecondaryText(value: String, tag: String) {
    Text(
        text = value,
        modifier = Modifier.fillMaxWidth().testTag(tag),
        color = CateringPackageColors.muted,
        style = CateringBodyStyle,
        softWrap = true,
        textAlign = TextAlign.Start,
    )
}

@Composable
private fun CateringChoiceButton(
    label: String,
    chosen: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val fill = if (chosen) CateringPackageColors.selected else CateringPackageColors.row
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .semantics { selected = chosen },
        enabled = enabled,
        shape = RoundedCornerShape(8.dp),
        border = BorderStroke(
            width = if (chosen) 2.dp else 1.dp,
            color = if (chosen) CateringPackageColors.accent else CateringPackageColors.outline,
        ),
        elevation = null,
        colors = ButtonDefaults.buttonColors(
            containerColor = fill,
            contentColor = CateringPackageColors.ink,
            disabledContainerColor = fill,
            disabledContentColor = CateringPackageColors.muted,
        ),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = label,
                modifier = Modifier.weight(1f),
                color = if (enabled) CateringPackageColors.ink else CateringPackageColors.muted,
                style = CateringBodyStyle,
                softWrap = true,
                textAlign = TextAlign.Start,
            )
            if (chosen) {
                Text(
                    text = "✓",
                    modifier = Modifier.clearAndSetSemantics {},
                    color = if (enabled) CateringPackageColors.accent else CateringPackageColors.muted,
                    style = CateringBodyStyle.copy(fontSize = 16.sp, lineHeight = 22.sp),
                )
            }
        }
    }
}

private enum class CateringPackageChoice(val id: String, val label: String) {
    BUFFET("buffet", "Buffet package"),
    BOXED("boxed", "Boxed package");

    fun isEligible(input: CateringPackageInput): Boolean = when (this) {
        BUFFET -> input.guestCount >= 6 && input.guestCount <= input.buffetCapacity
        BOXED -> input.guestCount <= input.boxedCapacity && input.vegetarianMeals >= input.vegetarianGuests
    }
}

private enum class CateringServiceChoice(val id: String, val label: String) {
    REUSABLE("reusable", "Reusable service"),
    COMPOSTABLE("compostable", "Compostable service");

    fun isEligible(input: CateringPackageInput, root: CateringPackageChoice?): Boolean {
        if (root == null || !root.isEligible(input)) return false
        return when (this) {
            REUSABLE -> root == CateringPackageChoice.BUFFET && input.reusableSets >= input.guestCount
            COMPOSTABLE -> input.compostableSets >= input.guestCount
        }
    }
}

private data class CateringPackageState(
    val entityID: String,
    val revision: Int,
    val root: CateringPackageChoice? = null,
    val detail: CateringServiceChoice? = null,
    val confirmed: Boolean = false,
    val recorded: Boolean = false,
) {
    fun reconciled(input: CateringPackageInput): CateringPackageState {
        if (entityID != input.entityID || revision != input.revision) {
            return CateringPackageState(input.entityID, input.revision)
        }
        if (root == null || !root.isEligible(input)) {
            return CateringPackageState(input.entityID, input.revision)
        }
        if (detail != null && !detail.isEligible(input, root)) {
            return copy(detail = null, confirmed = false, recorded = false)
        }
        return this
    }

    fun canConfirm(input: CateringPackageInput): Boolean =
        !recorded && root != null && detail != null &&
            root.isEligible(input) && detail.isEligible(input, root)

    fun canRecord(input: CateringPackageInput): Boolean = confirmed && canConfirm(input)

    fun summary(input: CateringPackageInput): String =
        "Package: ${root?.label ?: "Not chosen"}. Service: ${detail?.label ?: "Not chosen"}. ${input.guestCount} guests."

    fun status(input: CateringPackageInput): String = when {
        recorded -> "Recorded. Selections are locked for this request."
        CateringPackageChoice.values().none { it.isEligible(input) } ->
            "No package is eligible for these request details."
        root == null -> "Choose a package."
        detail == null -> "Choose a service for ${root.label}."
        !confirmed -> "Confirm the dietary counts to continue."
        else -> "Ready to record catering order."
    }
}

private object CateringPackageColors {
    val surface = Color(0xFFF7F9FC)
    val row = Color(0xFFFFFFFF)
    val selected = Color(0xFFE5F1FF)
    val accent = Color(0xFF2459A6)
    val disabled = Color(0xFFD9E1EC)
    val ink = Color(0xFF15243B)
    val muted = Color(0xFF526174)
    val onAccent = Color(0xFFFFFFFF)
    val outline = Color(0xFFB8C5D6)
}

private val CateringTitleStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontWeight = FontWeight.SemiBold,
    fontSize = 24.sp,
    lineHeight = 30.sp,
    letterSpacing = 0.sp,
)

private val CateringBodyStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontWeight = FontWeight.Normal,
    fontSize = 15.sp,
    lineHeight = 21.sp,
    letterSpacing = 0.sp,
)

private val CateringSectionStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontWeight = FontWeight.SemiBold,
    fontSize = 16.sp,
    lineHeight = 22.sp,
    letterSpacing = 0.sp,
)
