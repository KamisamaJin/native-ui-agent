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
import androidx.compose.foundation.layout.size
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

data class SubscriptionCapacityInput(
    val entityID: String,
    val revision: Int,
    val title: String,
    val context: String,
    val notes: List<String>,
    val seatCount: Int,
    val teamQuota: Int,
    val scaleQuota: Int,
    val prepaidMonths: Int,
    val accountBalanceCents: Int,
)

private enum class CapacityPlan(val id: String, val label: String) {
    Scale("scale", "Scale plan"),
    Team("team", "Team plan"),
}

private enum class CapacityTerm(val id: String, val label: String) {
    Annual("annual", "Annual billing"),
    Monthly("monthly", "Monthly billing"),
}

private fun SubscriptionCapacityInput.permits(plan: CapacityPlan): Boolean = when (plan) {
    CapacityPlan.Scale -> seatCount >= 10 && seatCount <= scaleQuota
    CapacityPlan.Team -> seatCount >= 2 && seatCount <= 25 && seatCount <= teamQuota
}

private fun SubscriptionCapacityInput.permits(term: CapacityTerm, plan: CapacityPlan): Boolean =
    permits(plan) && when (term) {
        CapacityTerm.Annual -> plan == CapacityPlan.Scale && prepaidMonths >= 12
        CapacityTerm.Monthly -> accountBalanceCents >= 0
    }

private data class CapacitySelection(
    val entityID: String,
    val revision: Int,
    val plan: CapacityPlan? = null,
    val term: CapacityTerm? = null,
    val confirmed: Boolean = false,
    val recorded: Boolean = false,
) {
    fun reconciled(input: SubscriptionCapacityInput): CapacitySelection {
        if (entityID != input.entityID || revision != input.revision) return fresh(input)
        val root = plan ?: return this
        if (!input.permits(root)) return fresh(input)
        if (term != null && !input.permits(term, root)) {
            return copy(term = null, confirmed = false, recorded = false)
        }
        return this
    }

    fun hasValidSelection(input: SubscriptionCapacityInput): Boolean =
        plan != null && term != null && input.permits(plan) && input.permits(term, plan)

    companion object {
        fun fresh(input: SubscriptionCapacityInput) = CapacitySelection(input.entityID, input.revision)
    }
}

private object CapacityColors {
    val Surface = Color(0xFFF7F9FC)
    val Row = Color(0xFFFFFFFF)
    val Selected = Color(0xFFE5F1FF)
    val Accent = Color(0xFF2459A6)
    val Disabled = Color(0xFFD9E1EC)
    val Ink = Color(0xFF15243B)
    val Muted = Color(0xFF526174)
    val Outline = Color(0xFFB8C5D6)
}

private val CapacityBodyStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 15.sp,
    fontWeight = FontWeight.Normal,
    lineHeight = 21.sp,
    letterSpacing = 0.sp,
    textAlign = TextAlign.Left,
)

private val CapacitySectionStyle = CapacityBodyStyle.copy(
    fontSize = 16.sp,
    fontWeight = FontWeight.SemiBold,
    lineHeight = 22.sp,
)

@Composable
fun SubscriptionCapacityChange(input: SubscriptionCapacityInput, onEvent: (String) -> Unit) {
    var local by remember { mutableStateOf(CapacitySelection.fresh(input)) }
    val current = local.reconciled(input)
    // Reconcile during composition so replacement content and controls agree immediately.
    if (current != local) local = current

    val choosePlan: (CapacityPlan) -> Unit = { plan ->
        val before = local.reconciled(input)
        if (!before.recorded && input.permits(plan) && before.plan != plan) {
            local = before.copy(plan = plan, term = null, confirmed = false)
        }
    }
    val chooseTerm: (CapacityTerm) -> Unit = { term ->
        val before = local.reconciled(input)
        val plan = before.plan
        if (!before.recorded && plan != null && input.permits(term, plan) && before.term != term) {
            local = before.copy(term = term, confirmed = false)
        }
    }
    val valid = current.hasValidSelection(input)

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(CapacityColors.Surface, RoundedCornerShape(12.dp))
            .testTag("subscription-capacity.surface")
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        CapacityLabel(
            text = input.title,
            tag = "subscription-capacity.title",
            color = CapacityColors.Ink,
            style = CapacityBodyStyle.copy(
                fontSize = 24.sp,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 30.sp,
            ),
        )
        CapacityLabel(input.context, "subscription-capacity.context")
        CapacityLabel(input.notes.joinToString("\n\n"), "subscription-capacity.notes")
        Text("Plan", modifier = Modifier.fillMaxWidth(), style = CapacitySectionStyle, color = CapacityColors.Ink)
        CapacityPlan.entries.forEach { plan ->
            CapacityChoice(
                label = plan.label,
                isSelected = current.plan == plan,
                enabled = !current.recorded && input.permits(plan),
                onClick = { choosePlan(plan) },
            )
        }
        Text("Term", modifier = Modifier.fillMaxWidth(), style = CapacitySectionStyle, color = CapacityColors.Ink)
        CapacityTerm.entries.forEach { term ->
            CapacityChoice(
                label = term.label,
                isSelected = current.term == term,
                enabled = !current.recorded && current.plan?.let { input.permits(term, it) } == true,
                onClick = { chooseTerm(term) },
            )
        }
        CapacityLabel(
            text = "Plan: ${current.plan?.label ?: "Not chosen"}. Term: ${current.term?.label ?: "Not chosen"}. ${input.seatCount} seats.",
            tag = "subscription-capacity.summary",
            color = CapacityColors.Ink,
            style = CapacitySectionStyle,
        )
        CapacityChoice(
            label = "I confirm the capacity commitment",
            isSelected = current.confirmed,
            enabled = valid && !current.recorded,
            onClick = {
                val before = local.reconciled(input)
                if (!before.recorded && before.hasValidSelection(input)) {
                    local = before.copy(confirmed = !before.confirmed)
                }
            },
        )
        CapacityLabel(capacityStatus(input, current), "subscription-capacity.status")
        CapacityLabel(
            if (current.recorded) "Capacity change recorded." else "No request recorded.",
            "subscription-capacity.receipt",
        )
        Button(
            onClick = {
                val before = local.reconciled(input)
                val plan = before.plan
                val term = before.term
                if (!before.recorded && before.confirmed && before.hasValidSelection(input) && plan != null && term != null) {
                    onEvent("capacity|${input.entityID}|${input.revision}|${plan.id}|${term.id}|${input.seatCount}")
                    local = before.copy(recorded = true)
                }
            },
            enabled = valid && current.confirmed && !current.recorded,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            shape = RoundedCornerShape(8.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = CapacityColors.Accent,
                contentColor = CapacityColors.Row,
                disabledContainerColor = CapacityColors.Disabled,
                disabledContentColor = CapacityColors.Muted,
            ),
            elevation = null,
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(
                "Record capacity change",
                modifier = Modifier.fillMaxWidth(),
                style = CapacitySectionStyle.copy(textAlign = TextAlign.Center),
            )
        }
    }
}

@Composable
private fun CapacityLabel(
    text: String,
    tag: String,
    color: Color = CapacityColors.Muted,
    style: TextStyle = CapacityBodyStyle,
) {
    Text(
        text = text,
        modifier = Modifier.fillMaxWidth().testTag(tag),
        color = color,
        style = style,
        softWrap = true,
    )
}

@Composable
private fun CapacityChoice(label: String, isSelected: Boolean, enabled: Boolean, onClick: () -> Unit) {
    val background = if (isSelected) CapacityColors.Selected else CapacityColors.Row
    val ink = if (enabled) CapacityColors.Ink else CapacityColors.Muted
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 48.dp)
            .semantics { selected = isSelected },
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = background,
            contentColor = ink,
            disabledContainerColor = background,
            disabledContentColor = CapacityColors.Muted,
        ),
        border = BorderStroke(
            if (isSelected) 2.dp else 1.dp,
            if (isSelected) CapacityColors.Accent else CapacityColors.Outline,
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
                color = ink,
                style = CapacityBodyStyle,
                softWrap = true,
            )
            if (isSelected) {
                Icon(
                    painter = painterResource(R.drawable.ic_check),
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = if (enabled) CapacityColors.Accent else CapacityColors.Muted,
                )
            }
        }
    }
}

private fun capacityStatus(input: SubscriptionCapacityInput, state: CapacitySelection): String = when {
    state.recorded -> "Recorded. Selections are locked for this request."
    !input.permits(CapacityPlan.Scale) && !input.permits(CapacityPlan.Team) -> "No plan is eligible for these request details."
    state.plan == null -> "Choose a plan."
    state.term == null -> "Choose a billing term for ${state.plan.label}."
    !state.confirmed -> "Confirm the capacity commitment to continue."
    else -> "Ready to record capacity change."
}
