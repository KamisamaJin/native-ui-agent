package com.example.reply.ui.waterround

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

public enum class WateringMethod { drip, soak }

public data class WaterRoundModel(
    val roundId: String,
    val title: String,
    val description: String,
    val notice: String,
    val bedCount: Int,
    val dripLitresPerBed: Int,
    val soakLitresPerBed: Int,
    val dripPrimeLitres: Int,
    val tankLitres: Int,
    val reserveLitres: Int,
    val soakAllowed: Boolean,
    val selectedMethod: WateringMethod,
    val reserveAcknowledged: Boolean,
    val isEnabled: Boolean,
    val isSubmitting: Boolean,
)

public sealed interface WaterRoundAction {
    public data class methodRequested(val roundId: String, val method: WateringMethod) : WaterRoundAction
    public data class reserveAcknowledgementRequested(val roundId: String, val acknowledged: Boolean) : WaterRoundAction
    public data class releaseRequested(
        val roundId: String,
        val method: WateringMethod,
        val bedCount: Int,
        val requestedLitres: Int,
        val remainingLitres: Int,
        val reserveUsedLitres: Int,
    ) : WaterRoundAction
}

private class Projection(model: WaterRoundModel) {
    val required = model.bedCount * when (model.selectedMethod) {
        WateringMethod.drip -> model.dripLitresPerBed
        WateringMethod.soak -> model.soakLitresPerBed
    } + if (model.selectedMethod == WateringMethod.drip) model.dripPrimeLitres else 0
    val spendable = model.tankLitres - model.reserveLitres
    val reserveNeeded = (required - spendable).coerceAtLeast(0)
    val remaining = (model.tankLitres - required).coerceAtLeast(0)
    val shortfall = (required - model.tankLitres).coerceAtLeast(0)
    val consentVisible = reserveNeeded > 0 && shortfall == 0
    val controlsEnabled = model.isEnabled && !model.isSubmitting
    val releaseEnabled = controlsEnabled && shortfall == 0 && (reserveNeeded == 0 || model.reserveAcknowledged)
    val status = when {
        !model.isEnabled -> "Round paused"
        model.isSubmitting -> "Preparing release…"
        shortfall > 0 -> "Not enough water"
        reserveNeeded > 0 && !model.reserveAcknowledged -> "Approve reserve use"
        else -> "Ready to release"
    }
}

private class Palette(dark: Boolean) {
    val surface = if (dark) Color(0xFF15251C) else Color(0xFFFFFFFF)
    val border = if (dark) Color(0xFF3B5242) else Color(0xFFD7E3D8)
    val foreground = if (dark) Color(0xFFE7F3E9) else Color(0xFF183A25)
    val muted = if (dark) Color(0xFFB2C8B8) else Color(0xFF526B59)
    val accent = if (dark) Color(0xFF81D89B) else Color(0xFF216B3B)
    val accentOn = if (dark) Color(0xFF102C19) else Color(0xFFFFFFFF)
    val selectedSurface = if (dark) Color(0xFF244F33) else Color(0xFFE5F2E8)
    val warning = if (dark) Color(0xFFFFD28A) else Color(0xFF865400)
    val warningSurface = if (dark) Color(0xFF493715) else Color(0xFFFFF1D5)
    val disabledSurface = if (dark) Color(0xFF293C2F) else Color(0xFFE5EBE6)
    val disabledText = if (dark) Color(0xFF92A396) else Color(0xFF65756A)
}

private fun tag(id: String) = Modifier.testTag("waterRound.$id")
private val regular = TextStyle(fontFamily = FontFamily.Default, fontSize = 14.sp, fontWeight = FontWeight.Normal)
private val control = TextStyle(fontFamily = FontFamily.Default, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)

@Composable
public fun WaterRoundRelease(
    model: WaterRoundModel,
    onAction: (WaterRoundAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    val p = Projection(model)
    val palette = Palette(isSystemInDarkTheme())
    val shape = RoundedCornerShape(20.dp)
    Column(
        modifier = modifier.fillMaxWidth().testTag("waterRound.root")
            .background(palette.surface, shape).border(1.dp, palette.border, shape).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        Text(model.title, tag("title").fillMaxWidth(), color = palette.foreground,
            style = regular.copy(fontSize = 20.sp, fontWeight = FontWeight.SemiBold))
        Body(model.description, "description", palette.muted)
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Body("Beds: ${model.bedCount}", "beds", palette.foreground)
            Body("Tank: ${model.tankLitres} L", "tank", palette.foreground)
            Body("Protected reserve: ${model.reserveLitres} L", "reserve", palette.foreground)
            Body("Drip prime: ${model.dripPrimeLitres} L", "dripPrime", palette.foreground)
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Method(model, WateringMethod.drip, "Drip lines", model.dripLitresPerBed, p.controlsEnabled, palette, onAction)
            Method(model, WateringMethod.soak, "Soak hoses", model.soakLitresPerBed, p.controlsEnabled && model.soakAllowed, palette, onAction)
        }
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Summary("Required", p.required, "required", palette)
            Summary("Outside reserve", p.spendable, "spendable", palette)
            Summary("Reserve needed", p.reserveNeeded, "reserveNeeded", palette)
            Summary("Remaining", p.remaining, "remaining", palette)
            if (p.shortfall > 0) Summary("Shortfall", p.shortfall, "shortfall", palette)
        }
        if (p.consentVisible) {
            val consentLabel = "Use ${p.reserveNeeded} L from the protected reserve"
            Row(
                tag("reserveConsent").fillMaxWidth().heightIn(min = 44.dp)
                    .clip(RoundedCornerShape(12.dp)).background(palette.warningSurface)
                    .toggleable(value = model.reserveAcknowledged, enabled = p.controlsEnabled, role = Role.Checkbox) {
                        if (p.controlsEnabled && p.consentVisible) {
                            onAction(WaterRoundAction.reserveAcknowledgementRequested(model.roundId, !model.reserveAcknowledged))
                        }
                    }
                    .semantics(mergeDescendants = true) { contentDescription = consentLabel }
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Checkbox(
                    checked = model.reserveAcknowledged, onCheckedChange = null, enabled = p.controlsEnabled,
                    modifier = Modifier.size(22.dp),
                    colors = CheckboxDefaults.colors(
                        checkedColor = palette.accent, uncheckedColor = palette.warning,
                        checkmarkColor = palette.accentOn, disabledCheckedColor = palette.disabledText,
                        disabledUncheckedColor = palette.disabledText,
                    ),
                )
                Text(consentLabel, Modifier.weight(1f), color = palette.foreground, style = regular)
            }
        }
        if (model.notice.isNotEmpty()) Body(model.notice, "notice", palette.foreground)
        val ready = p.status == "Ready to release"
        Text(
            p.status,
            tag("status").fillMaxWidth().background(if (ready) palette.selectedSurface else palette.warningSurface, RoundedCornerShape(12.dp)).padding(12.dp),
            color = if (ready) palette.foreground else palette.warning,
            style = regular.copy(fontWeight = FontWeight.SemiBold),
        )
        Button(
            onClick = {
                if (p.releaseEnabled) onAction(WaterRoundAction.releaseRequested(
                    model.roundId, model.selectedMethod, model.bedCount, p.required, p.remaining, p.reserveNeeded,
                ))
            },
            enabled = p.releaseEnabled,
            modifier = tag("submit").fillMaxWidth().heightIn(min = 48.dp)
                .semantics { contentDescription = "Release ${p.required} L" },
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = palette.accent, contentColor = palette.accentOn,
                disabledContainerColor = palette.disabledSurface, disabledContentColor = palette.disabledText,
            ),
            contentPadding = PaddingValues(12.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                if (model.isEnabled && model.isSubmitting) CircularProgressIndicator(
                    modifier = tag("progress").size(20.dp), color = palette.disabledText, strokeWidth = 2.dp,
                )
                Text("Release ${p.required} L", style = control)
            }
        }
    }
}

@Composable
private fun Body(value: String, id: String, color: Color) {
    Text(value, tag(id).fillMaxWidth(), color = color, style = regular)
}

@Composable
private fun Method(
    model: WaterRoundModel,
    method: WateringMethod,
    name: String,
    rate: Int,
    enabled: Boolean,
    palette: Palette,
    onAction: (WaterRoundAction) -> Unit,
) {
    val isSelected = model.selectedMethod == method
    val shape = RoundedCornerShape(12.dp)
    val surface = if (isSelected) palette.selectedSurface else palette.surface
    Button(
        onClick = { if (enabled && model.selectedMethod != method) onAction(WaterRoundAction.methodRequested(model.roundId, method)) },
        enabled = enabled,
        modifier = tag("method.${method.name}").fillMaxWidth().heightIn(min = 56.dp)
            .semantics { selected = isSelected; contentDescription = "$name, $rate L per bed" }
            .border(1.dp, if (isSelected) palette.accent else palette.border, shape),
        shape = shape,
        colors = ButtonDefaults.buttonColors(
            containerColor = surface, contentColor = palette.foreground,
            disabledContainerColor = surface, disabledContentColor = palette.foreground,
        ),
        contentPadding = PaddingValues(12.dp),
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            Canvas(Modifier.padding(top = 2.dp).size(18.dp)) {
                drawCircle(if (isSelected) palette.accent else palette.muted, style = Stroke(width = 1.5.dp.toPx()))
                if (isSelected) drawCircle(palette.accent, radius = size.minDimension * .28f)
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(name, color = palette.foreground, style = control)
                Text("$rate L per bed", color = palette.muted, style = regular)
            }
        }
    }
}

@Composable
private fun Summary(label: String, value: Int, id: String, palette: Palette) {
    val numeric = regular.copy(fontSize = 17.sp, fontWeight = FontWeight.SemiBold, fontFeatureSettings = "tnum")
    val labels = regular.copy(fontSize = 13.sp)
    val scale = LocalDensity.current.fontScale
    BoxWithConstraints(tag(id).fillMaxWidth().semantics(mergeDescendants = true) { contentDescription = "$label: $value L" }) {
        if (maxWidth < 280.dp || scale > 1.3f) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("$label:", color = palette.foreground, style = labels)
                Text("$value L", color = palette.foreground, style = numeric)
            }
        } else {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("$label:", Modifier.weight(1f), color = palette.foreground, style = labels)
                Text("$value L", color = palette.foreground, style = numeric)
            }
        }
    }
}
