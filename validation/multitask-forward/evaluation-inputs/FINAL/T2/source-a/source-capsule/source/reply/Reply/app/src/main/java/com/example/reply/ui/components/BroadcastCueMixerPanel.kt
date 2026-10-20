package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.graphics.luminance
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

public data class BroadcastMixChannel(
    val id: String,
    val name: String,
    val caption: String,
    val level: Int,
    val muted: Boolean,
    val locked: Boolean,
)

public data class BroadcastCueMixerRequest(
    val id: String,
    val title: String,
    val context: String,
    val maxLiveUnits: Int,
    val maxLevel: Int,
    val mode: String,
    val stepperWidth: Double,
    val notes: List<String>,
    val channels: List<BroadcastMixChannel>,
)

@Composable
public fun BroadcastCueMixerPanel(
    request: BroadcastCueMixerRequest,
    onConfirm: (String, String, List<BroadcastMixChannel>) -> Unit,
) {
    var channels by remember(request.id) {
        mutableStateOf(request.channels.map { it.copy(level = it.level.coerceIn(0, request.maxLevel.coerceAtLeast(0))) })
    }
    var mode by remember(request.id) { mutableStateOf(request.mode) }
    val palette = MixerColors(MaterialTheme.colorScheme.background.luminance() < 0.5f)
    val load = channels.filterNot { it.muted }.sumOf { it.level }
    val audibleCount = channels.count { !it.muted && it.level > 0 }
    val headroom = request.maxLiveUnits - load
    val canApply = audibleCount > 0 && (mode == "preview" || load <= request.maxLiveUnits)

    fun changeChannel(index: Int, level: Int, muted: Boolean) {
        val current = channels[index]
        if (current.locked) return
        channels = channels.toMutableList().also {
            it[index] = current.copy(level = level.coerceIn(0, request.maxLevel.coerceAtLeast(0)), muted = muted)
        }
    }

    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MixerText(request.title, 22, FontWeight.Bold, palette.ink, Modifier.testTag("mixer.title"))
            MixerText(request.context, 14, FontWeight.Normal, palette.muted)
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            MixerControl(
                label = "Live", identifier = "mixer.live", palette = palette,
                modifier = Modifier.weight(1f), fontSize = 16, selected = mode == "live",
                onClick = { mode = "live" },
            )
            MixerControl(
                label = "Preview", identifier = "mixer.preview", palette = palette,
                modifier = Modifier.weight(1f), fontSize = 16, selected = mode == "preview",
                onClick = { mode = "preview" },
            )
        }
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            MixerText("Channels", 16, FontWeight.SemiBold, palette.ink)
            channels.forEachIndexed { index, channel ->
                Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    MixerText(channel.name + if (channel.locked) " • Locked" else "", 16, FontWeight.SemiBold, palette.ink)
                    MixerText(channel.caption, 13, FontWeight.Normal, palette.muted)
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        MixerControl(
                            label = "−", identifier = "mixer.${channel.id}Minus", palette = palette,
                            modifier = Modifier.width(request.stepperWidth.dp).semantics { contentDescription = "Decrease ${channel.name}" },
                            enabled = !channel.locked && channel.level > 0, fontSize = 16,
                            fixedHeight = 48.dp, centered = true,
                            onClick = { changeChannel(index, channel.level - 1, channel.muted) },
                        )
                        Box(Modifier.width(40.dp), contentAlignment = Alignment.Center) {
                            MixerText(channel.level.toString(), 16, FontWeight.SemiBold, palette.ink,
                                Modifier.testTag("mixer.${channel.id}Level"))
                        }
                        MixerControl(
                            label = "+", identifier = "mixer.${channel.id}Plus", palette = palette,
                            modifier = Modifier.width(request.stepperWidth.dp).semantics { contentDescription = "Increase ${channel.name}" },
                            enabled = !channel.locked && channel.level < request.maxLevel, fontSize = 16,
                            fixedHeight = 48.dp, centered = true,
                            onClick = { changeChannel(index, channel.level + 1, channel.muted) },
                        )
                        Spacer(Modifier.weight(1f))
                        MixerControl(
                            label = if (channel.muted) "Muted" else "Mute", identifier = "mixer.${channel.id}Mute",
                            palette = palette, modifier = Modifier.width(90.dp), enabled = !channel.locked,
                            selected = channel.muted, fontSize = 14, fixedHeight = 48.dp,
                            onClick = { changeChannel(index, channel.level, !channel.muted) },
                        )
                    }
                }
            }
        }
        Column(
            Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp))
                .background(palette.surface).border(1.dp, palette.border, RoundedCornerShape(10.dp)).padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            MixerText("$audibleCount audible • $load / ${request.maxLiveUnits} units", 18, FontWeight.SemiBold,
                palette.ink, Modifier.testTag("mixer.summary"))
            MixerText("Headroom: $headroom ${mixerUnit(headroom)}", 14, FontWeight.Normal,
                palette.muted, Modifier.testTag("mixer.headroom"))
            MixerText(if (mode == "preview") "Preview mode" else "Live mode", 14, FontWeight.SemiBold,
                palette.accent, Modifier.testTag("mixer.modeLabel"))
        }
        if (load > request.maxLiveUnits) {
            val excess = load - request.maxLiveUnits
            MixerText("Over live limit by $excess ${mixerUnit(excess)}", 14, FontWeight.SemiBold,
                palette.accent, Modifier.testTag("mixer.warning"))
        }
        Box(
            Modifier.fillMaxWidth().height(56.dp).clip(RoundedCornerShape(10.dp))
                .background(if (canApply) palette.accent else palette.border)
                .testTag("mixer.primary")
                .clickable(enabled = canApply, role = Role.Button) {
                    if (canApply) onConfirm(request.id, mode, channels.sortedBy { it.id })
                }.padding(horizontal = 12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            MixerText("Apply mix", 16, FontWeight.SemiBold, if (canApply) palette.primaryInk else palette.muted)
        }
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            MixerText("Operator notes", 16, FontWeight.SemiBold, palette.ink, Modifier.testTag("mixer.notes"))
            request.notes.forEach { note -> MixerText(note, 14, FontWeight.Normal, palette.muted) }
        }
    }
}

private fun mixerUnit(value: Int): String = if (value == 1) "unit" else "units"

@Composable
private fun MixerText(text: String, size: Int, weight: FontWeight, color: Color, modifier: Modifier = Modifier) {
    Text(
        text = text, modifier = modifier,
        style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = size.sp,
            fontWeight = weight, color = color, letterSpacing = 0.sp),
        softWrap = true,
    )
}

@Composable
private fun MixerControl(
    label: String,
    identifier: String,
    palette: MixerColors,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    selected: Boolean? = null,
    fontSize: Int,
    fixedHeight: Dp? = null,
    centered: Boolean = false,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(10.dp)
    val heightModifier = if (fixedHeight != null) Modifier.height(fixedHeight) else Modifier.heightIn(min = 48.dp)
    val interactionModifier = if (selected != null) {
        Modifier.selectable(selected = selected, enabled = enabled, role = Role.Button, onClick = onClick)
    } else Modifier.clickable(enabled = enabled, role = Role.Button, onClick = onClick)
    Box(
        modifier.then(heightModifier).clip(shape)
            .background(if (enabled) palette.surface else palette.border)
            .border(1.dp, if (selected == true) palette.accent else palette.border, shape)
            .testTag(identifier).then(interactionModifier),
        contentAlignment = if (centered) Alignment.Center else Alignment.CenterStart,
    ) {
        MixerText(label, fontSize, FontWeight.SemiBold, if (enabled) palette.ink else palette.muted,
            if (centered) Modifier else Modifier.padding(horizontal = 12.dp, vertical = if (fixedHeight == null) 12.dp else 0.dp))
        if (selected == true) {
            Box(Modifier.align(Alignment.TopEnd).padding(5.dp).size(5.dp).background(palette.accent, CircleShape))
        }
    }
}

private class MixerColors(dark: Boolean) {
    val surface = Color(if (dark) 0xFF17283C else 0xFFF0F5FA)
    val ink = Color(if (dark) 0xFFE1EDFA else 0xFF1E3652)
    val muted = Color(if (dark) 0xFFB4C7DD else 0xFF556B82)
    val accent = Color(if (dark) 0xFFA0CCFA else 0xFF245F9A)
    val border = Color(if (dark) 0xFF405971 else 0xFFC8D7E5)
    val primaryInk = Color(if (dark) 0xFF101B29 else 0xFFFFFFFF)
}
