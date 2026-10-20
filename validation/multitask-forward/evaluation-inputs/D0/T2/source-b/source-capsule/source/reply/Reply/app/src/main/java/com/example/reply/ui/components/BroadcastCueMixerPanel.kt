package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
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
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class BroadcastMixChannel(
    val id: String,
    val name: String,
    val caption: String,
    val level: Int,
    val muted: Boolean,
    val locked: Boolean,
)

data class BroadcastCueMixerRequest(
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
fun BroadcastCueMixerPanel(
    request: BroadcastCueMixerRequest,
    onConfirm: (String, String, List<BroadcastMixChannel>) -> Unit,
) {
    val palette = mixerPalette(isSystemInDarkTheme())
    var channels by remember(request.id) {
        mutableStateOf(request.channels.map { it.copy(level = it.level.coerceIn(0, request.maxLevel.coerceAtLeast(0))) })
    }
    var mode by remember(request.id) { mutableStateOf(request.mode) }
    val load = channels.filter { !it.muted }.sumOf { it.level }
    val audible = channels.count { !it.muted && it.level > 0 }
    val headroom = request.maxLiveUnits - load
    val canApply = audible > 0 && (mode == "preview" || load <= request.maxLiveUnits)
    val shape = RoundedCornerShape(10.dp)

    fun edit(id: String, delta: Int = 0, mute: Boolean? = null) {
        channels = channels.map { channel ->
            if (channel.id != id || channel.locked) channel
            else channel.copy(
                level = (channel.level + delta).coerceIn(0, request.maxLevel.coerceAtLeast(0)),
                muted = mute ?: channel.muted,
            )
        }
    }

    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MixerText(request.title, 22, FontWeight.Bold, palette.ink,
                Modifier.testTag("mixer.title").semantics { heading() })
            MixerText(request.context, 14, FontWeight.Normal, palette.muted)
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("live" to "Live", "preview" to "Preview").forEach { (value, label) ->
                val selected = mode == value
                Box(
                    Modifier.weight(1f).heightIn(min = 48.dp).clip(shape)
                        .background(palette.surface)
                        .border(1.dp, if (selected) palette.accent else palette.border, shape)
                        .testTag("mixer.$value")
                        .selectable(selected = selected, role = Role.Tab, onClick = { mode = value })
                        .padding(12.dp),
                ) {
                    MixerText(label, 16, FontWeight.SemiBold, palette.ink)
                    SelectionMarker(selected, palette.accent, Modifier.align(Alignment.TopEnd))
                }
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            MixerText("Channels", 16, FontWeight.SemiBold, palette.ink)
            channels.forEach { channel ->
                Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    MixerText(channel.name + if (channel.locked) " • Locked" else "", 16, FontWeight.SemiBold, palette.ink)
                    MixerText(channel.caption, 13, FontWeight.Normal, palette.muted)
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        MixerStepButton(
                            "−", "Decrease ${channel.name}", "mixer.${channel.id}Minus",
                            request.stepperWidth, !channel.locked && channel.level > 0, palette,
                        ) { edit(channel.id, delta = -1) }
                        Box(Modifier.width(40.dp), contentAlignment = Alignment.Center) {
                            MixerText(channel.level.toString(), 16, FontWeight.SemiBold, palette.ink,
                                Modifier.testTag("mixer.${channel.id}Level"))
                        }
                        MixerStepButton(
                            "+", "Increase ${channel.name}", "mixer.${channel.id}Plus",
                            request.stepperWidth, !channel.locked && channel.level < request.maxLevel, palette,
                        ) { edit(channel.id, delta = 1) }
                        Spacer(Modifier.weight(1f))
                        Box(
                            Modifier.width(90.dp).heightIn(min = 48.dp).clip(shape)
                                .background(if (channel.locked) palette.border else palette.surface)
                                .border(1.dp, if (channel.muted) palette.accent else palette.border, shape)
                                .testTag("mixer.${channel.id}Mute")
                                .selectable(
                                    selected = channel.muted,
                                    enabled = !channel.locked,
                                    role = Role.Button,
                                    onClick = { edit(channel.id, mute = !channel.muted) },
                                ).padding(12.dp),
                            contentAlignment = Alignment.CenterStart,
                        ) {
                            MixerText(if (channel.muted) "Muted" else "Mute", 14, FontWeight.SemiBold,
                                if (channel.locked) palette.muted else palette.ink)
                            SelectionMarker(channel.muted, palette.accent, Modifier.align(Alignment.TopEnd))
                        }
                    }
                }
            }
        }
        Column(
            Modifier.fillMaxWidth().clip(shape).background(palette.surface)
                .border(1.dp, palette.border, shape).padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            MixerText("$audible audible • $load / ${request.maxLiveUnits} units", 18, FontWeight.SemiBold,
                palette.ink, Modifier.testTag("mixer.summary"))
            MixerText("Headroom: $headroom ${if (headroom == 1) "unit" else "units"}", 14, FontWeight.Normal,
                palette.muted, Modifier.testTag("mixer.headroom"))
            MixerText(if (mode == "preview") "Preview mode" else "Live mode", 14, FontWeight.SemiBold,
                palette.accent, Modifier.testTag("mixer.modeLabel"))
        }
        if (load > request.maxLiveUnits) {
            val excess = load - request.maxLiveUnits
            MixerText("Over live limit by $excess ${if (excess == 1) "unit" else "units"}", 14,
                FontWeight.SemiBold, palette.accent, Modifier.testTag("mixer.warning"))
        }
        Box(
            Modifier.fillMaxWidth().height(56.dp).clip(shape)
                .background(if (canApply) palette.accent else palette.border)
                .testTag("mixer.primary")
                .clickable(enabled = canApply, role = Role.Button) {
                    if (canApply) onConfirm(request.id, mode, channels.sortedBy { it.id })
                }.padding(horizontal = 12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            MixerText("Apply mix", 16, FontWeight.SemiBold, if (canApply) palette.primaryInk else palette.muted)
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            MixerText("Operator notes", 16, FontWeight.SemiBold, palette.ink,
                Modifier.testTag("mixer.notes").semantics { heading() })
            request.notes.forEach { note -> MixerText(note, 14, FontWeight.Normal, palette.muted) }
        }
    }
}

@Composable
private fun MixerText(
    text: String,
    size: Int,
    weight: FontWeight,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Text(text = text, modifier = modifier, color = color,
        style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = size.sp, fontWeight = weight),
        softWrap = true)
}

@Composable
private fun MixerStepButton(
    label: String,
    description: String,
    tag: String,
    width: Double,
    enabled: Boolean,
    palette: MixerColors,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(10.dp)
    Box(
        Modifier.width(width.dp).height(48.dp).clip(shape)
            .background(if (enabled) palette.surface else palette.border)
            .border(1.dp, palette.border, shape)
            .testTag(tag).semantics { contentDescription = description }
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) { MixerText(label, 16, FontWeight.SemiBold, if (enabled) palette.ink else palette.muted) }
}

@Composable
private fun SelectionMarker(selected: Boolean, color: Color, modifier: Modifier) {
    if (selected) Box(modifier.size(4.dp).background(color, CircleShape))
}

private data class MixerColors(
    val surface: Color,
    val ink: Color,
    val muted: Color,
    val accent: Color,
    val border: Color,
    val primaryInk: Color,
)

private fun mixerPalette(dark: Boolean) = if (dark) MixerColors(
    Color(0xFF17283C), Color(0xFFE1EDFA), Color(0xFFB4C7DD),
    Color(0xFFA0CCFA), Color(0xFF405971), Color(0xFF101B29),
) else MixerColors(
    Color(0xFFF0F5FA), Color(0xFF1E3652), Color(0xFF556B82),
    Color(0xFF245F9A), Color(0xFFC8D7E5), Color(0xFFFFFFFF),
)
