/*
 * Copyright 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 */

package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class AudioTourChapter(val id: String, val title: String, val body: String)

data class OfflineAudioTour(
    val id: String,
    val title: String,
    val language: String,
    val downloadSizeMB: Int,
    val availableMB: Int,
    val meteredConnection: Boolean,
    val chapters: List<AudioTourChapter>,
)

/** Records a request; the caller supplies capacity and owns scrolling and audio transfer. */
@Composable
fun OfflineAudioTourPanel(
    tour: OfflineAudioTour,
    onWifiOnlyChange: (Boolean) -> Unit,
    onDownload: (String, Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    // Model identity resets all local state during the replacement composition.
    var chaptersOpen by remember(tour.id) { mutableStateOf(false) }
    var wifiOnly by remember(tour.id) { mutableStateOf(true) }
    var requested by remember(tour.id) { mutableStateOf(false) }

    val canDownload = tour.availableMB >= tour.downloadSizeMB &&
        !(tour.meteredConnection && wifiOnly) && !requested
    val status = when {
        tour.availableMB < tour.downloadSizeMB -> AudioTourStatus.Storage
        requested -> AudioTourStatus.Requested
        tour.meteredConnection && wifiOnly -> AudioTourStatus.Waiting
        else -> AudioTourStatus.Ready
    }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(AudioTourColors.Canvas)
            .testTag("audio.canvas")
            .semantics(mergeDescendants = false) {}
            .padding(8.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(AudioTourColors.Surface)
                .testTag("audio.surface")
                .semantics(mergeDescendants = false) {}
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Box(
                Modifier
                    .size(width = 6.dp, height = 40.dp)
                    .background(AudioTourColors.Ink)
                    .testTag("audio.inkMark")
                    .semantics { contentDescription = "Ink accent" },
            )

            Text(
                text = tour.title,
                modifier = Modifier.fillMaxWidth().testTag("audio.title"),
                color = AudioTourColors.Ink,
                fontSize = 22.sp,
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                text = "${tour.language} · ${tour.downloadSizeMB} MB",
                modifier = Modifier.fillMaxWidth().testTag("audio.subtitle"),
                color = AudioTourColors.Ink,
                fontSize = 16.sp,
            )

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 56.dp)
                    .background(status.fill)
                    .testTag("audio.status")
                    .semantics(mergeDescendants = false) { contentDescription = status.label }
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                contentAlignment = Alignment.CenterStart,
            ) {
                Text(
                    text = status.label,
                    modifier = Modifier.fillMaxWidth().testTag("audio.statusText"),
                    color = AudioTourColors.Ink,
                    fontSize = 16.sp,
                )
            }

            TextButton(
                onClick = { chaptersOpen = !chaptersOpen },
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                    .testTag("audio.disclosure"),
                shape = RectangleShape,
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.textButtonColors(contentColor = AudioTourColors.Ink),
            ) {
                Text(
                    text = if (chaptersOpen) "Hide chapters" else "Review chapters",
                    modifier = Modifier.fillMaxWidth(),
                    fontSize = 16.sp,
                )
            }

            if (chaptersOpen) {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    tour.chapters.forEachIndexed { index, chapter ->
                        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Text(
                                text = chapter.title,
                                modifier = Modifier.fillMaxWidth()
                                    .testTag("audio.section.$index.heading"),
                                color = AudioTourColors.Ink,
                                fontSize = 17.sp,
                                fontWeight = FontWeight.SemiBold,
                            )
                            Text(
                                text = chapter.body,
                                modifier = Modifier.fillMaxWidth()
                                    .testTag("audio.section.$index.body"),
                                color = AudioTourColors.Ink,
                                fontSize = 16.sp,
                            )
                        }
                    }
                }
            }

            TextButton(
                onClick = {
                    if (!requested) {
                        wifiOnly = !wifiOnly
                        onWifiOnlyChange(wifiOnly)
                    }
                },
                enabled = !requested,
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                    .testTag("audio.choice")
                    .semantics {
                        selected = wifiOnly
                        contentDescription = "Wi-Fi only"
                    },
                shape = RectangleShape,
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.textButtonColors(
                    contentColor = AudioTourColors.Ink,
                    disabledContentColor = AudioTourColors.Ink,
                ),
            ) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier.size(20.dp).border(1.dp, AudioTourColors.Ink, RectangleShape)
                            .clearAndSetSemantics {},
                        contentAlignment = Alignment.Center,
                    ) {
                        if (wifiOnly) Text(
                            "✓", modifier = Modifier.clearAndSetSemantics {},
                            color = AudioTourColors.Ink, fontSize = 16.sp,
                        )
                    }
                    Spacer(Modifier.width(8.dp))
                    Text("Wi-Fi only", modifier = Modifier.weight(1f), fontSize = 16.sp)
                }
            }

            Button(
                onClick = {
                    // Read current state as well as the native enabled state to
                    // keep repeated actions from dispatching a second request.
                    if (tour.availableMB >= tour.downloadSizeMB &&
                        !(tour.meteredConnection && wifiOnly) && !requested
                    ) {
                        requested = true
                        onDownload(tour.id, wifiOnly)
                    }
                },
                enabled = canDownload,
                modifier = Modifier.fillMaxWidth().height(56.dp).testTag("audio.primary"),
                shape = RectangleShape,
                border = null,
                elevation = null,
                contentPadding = PaddingValues(0.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AudioTourColors.Enabled,
                    contentColor = Color.White,
                    disabledContainerColor = AudioTourColors.Disabled,
                    disabledContentColor = AudioTourColors.Ink,
                ),
            ) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        text = if (requested) "Requested" else "Get audio",
                        modifier = Modifier.fillMaxWidth(),
                        textAlign = TextAlign.Center,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }
        }
    }
}

private enum class AudioTourStatus(val label: String, val fill: Color) {
    Storage("Storage needed", AudioTourColors.Blocked),
    Requested("Download requested", AudioTourColors.Requested),
    Waiting("Wi-Fi required", AudioTourColors.Waiting),
    Ready("Ready to download", AudioTourColors.Ready),
}

private object AudioTourColors {
    val Canvas = Color(0xFFF4F6FA)
    val Surface = Color(0xFFFFFFFF)
    val Ink = Color(0xFF172B4D)
    val Waiting = Color(0xFFE9EFF8)
    val Ready = Color(0xFFDDF4EC)
    val Requested = Color(0xFFDDEBFF)
    val Blocked = Color(0xFFFFE5B3)
    val Enabled = Color(0xFF2463C5)
    val Disabled = Color(0xFFD8DEE8)
}
