package com.example.reply.ui.waterround

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
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
    val required = model.bedCount * (if (model.selectedMethod == WateringMethod.drip) model.dripLitresPerBed else model.soakLitresPerBed) +
        (if (model.selectedMethod == WateringMethod.drip) model.dripPrimeLitres else 0)
    val spendable = model.tankLitres - model.reserveLitres
    val reserveNeeded = maxOf(0, required - spendable)
    val remaining = maxOf(0, model.tankLitres - required)
    val shortfall = maxOf(0, required - model.tankLitres)
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

@Composable
public fun WaterRoundRelease(
    model: WaterRoundModel,
    onAction: (WaterRoundAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    val p = Palette(isSystemInDarkTheme())
    val values = Projection(model)
    val cardShape = RoundedCornerShape(20.dp)
    Column(
        modifier = modifier.fillMaxWidth().testTag("waterRound.root")
            .background(p.surface, cardShape).border(1.dp, p.border, cardShape).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(model.title, modifier = Modifier.fillMaxWidth().testTag("waterRound.title"),
            color = p.foreground, style = TextStyle(fontSize = 20.sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Default))
        Body(model.description, "waterRound.description", p.muted)
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Body("Beds: ${model.bedCount}", "waterRound.beds", p.foreground)
            Body("Tank: ${model.tankLitres} L", "waterRound.tank", p.foreground)
            Body("Protected reserve: ${model.reserveLitres} L", "waterRound.reserve", p.foreground)
            Body("Drip prime: ${model.dripPrimeLitres} L", "waterRound.dripPrime", p.foreground)
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MethodChoice(WateringMethod.drip, "Drip lines", model.dripLitresPerBed, model.selectedMethod == WateringMethod.drip,
                values.controlsEnabled, p) {
                if (values.controlsEnabled && model.selectedMethod != WateringMethod.drip) {
                    onAction(WaterRoundAction.methodRequested(model.roundId, WateringMethod.drip))
                }
            }
            MethodChoice(WateringMethod.soak, "Soak hoses", model.soakLitresPerBed, model.selectedMethod == WateringMethod.soak,
                values.controlsEnabled && model.soakAllowed, p) {
                if (values.controlsEnabled && model.soakAllowed && model.selectedMethod != WateringMethod.soak) {
                    onAction(WaterRoundAction.methodRequested(model.roundId, WateringMethod.soak))
                }
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Summary("Required", values.required, "waterRound.required", p.foreground)
            Summary("Outside reserve", values.spendable, "waterRound.spendable", p.foreground)
            Summary("Reserve needed", values.reserveNeeded, "waterRound.reserveNeeded", p.foreground)
            Summary("Remaining", values.remaining, "waterRound.remaining", p.foreground)
            if (values.shortfall > 0) Summary("Shortfall", values.shortfall, "waterRound.shortfall", p.foreground)
        }
        if (values.consentVisible) {
            Row(
                modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp).testTag("waterRound.reserveConsent")
                    .toggleable(value = model.reserveAcknowledged, enabled = values.controlsEnabled, role = Role.Checkbox) {
                        if (values.controlsEnabled && values.consentVisible) {
                            onAction(WaterRoundAction.reserveAcknowledgementRequested(model.roundId, !model.reserveAcknowledged))
                        }
                    },
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                val boxShape = RoundedCornerShape(3.dp)
                Box(Modifier.size(22.dp).background(if (model.reserveAcknowledged) p.accent else p.surface, boxShape)
                    .border(1.dp, p.accent, boxShape).clearAndSetSemantics {}, contentAlignment = Alignment.Center) {
                    if (model.reserveAcknowledged) Text("✓", color = p.accentOn, style = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.SemiBold))
                }
                Text("Use ${values.reserveNeeded} L from the protected reserve", color = p.foreground,
                    style = TextStyle(fontSize = 14.sp, fontFamily = FontFamily.Default), modifier = Modifier.weight(1f))
            }
        }
        if (model.notice.isNotEmpty()) Body(model.notice, "waterRound.notice", p.foreground)
        val ready = values.status == "Ready to release"
        Text(values.status,
            modifier = Modifier.fillMaxWidth().background(if (ready) p.selectedSurface else p.warningSurface, RoundedCornerShape(12.dp))
                .padding(12.dp).testTag("waterRound.status"),
            color = if (ready) p.foreground else p.warning,
            style = TextStyle(fontSize = 14.sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Default))
        val actionShape = RoundedCornerShape(12.dp)
        Row(
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("waterRound.submit")
                .clip(actionShape).background(if (values.releaseEnabled) p.accent else p.disabledSurface)
                .clickable(enabled = values.releaseEnabled, role = Role.Button) {
                    if (values.releaseEnabled) onAction(WaterRoundAction.releaseRequested(model.roundId, model.selectedMethod,
                        model.bedCount, values.required, values.remaining, values.reserveNeeded))
                }.semantics { contentDescription = "Release ${values.required} L" }.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (model.isEnabled && model.isSubmitting) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp).testTag("waterRound.progress"),
                    color = p.disabledText, strokeWidth = 2.dp)
            }
            Text("Release ${values.required} L", color = if (values.releaseEnabled) p.accentOn else p.disabledText,
                style = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Default))
        }
    }
}

@Composable
private fun Body(text: String, tag: String, color: Color) {
    Text(text, modifier = Modifier.fillMaxWidth().testTag(tag), color = color,
        style = TextStyle(fontSize = 14.sp, fontFamily = FontFamily.Default))
}

@Composable
private fun Summary(label: String, value: Int, tag: String, color: Color) {
    val text = buildAnnotatedString {
        withStyle(SpanStyle(fontSize = 13.sp, fontFamily = FontFamily.Default)) { append("$label: ") }
        withStyle(SpanStyle(fontSize = 17.sp, fontWeight = FontWeight.SemiBold, fontFeatureSettings = "tnum", fontFamily = FontFamily.Default)) { append("$value L") }
    }
    Text(text, modifier = Modifier.fillMaxWidth().testTag(tag), color = color,
        style = TextStyle(fontFamily = FontFamily.Default))
}

@Composable
private fun MethodChoice(method: WateringMethod, name: String, rate: Int, isSelected: Boolean,
                         enabled: Boolean, p: Palette, onClick: () -> Unit) {
    val shape = RoundedCornerShape(12.dp)
    Row(
        modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("waterRound.method.${method.name}")
            .clip(shape).background(if (isSelected) p.selectedSurface else p.surface)
            .border(BorderStroke(1.dp, if (isSelected) p.accent else p.border), shape)
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick)
            .semantics { selected = isSelected; contentDescription = "$name, $rate L per bed" }
            .padding(12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Box(Modifier.size(18.dp).border(1.dp, if (isSelected) p.accent else p.muted, CircleShape), contentAlignment = Alignment.Center) {
            if (isSelected) Box(Modifier.size(10.dp).background(p.accent, CircleShape))
        }
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(name, color = p.foreground, style = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Default))
            Text("$rate L per bed", color = p.muted, style = TextStyle(fontSize = 14.sp, fontFamily = FontFamily.Default))
        }
    }
}
