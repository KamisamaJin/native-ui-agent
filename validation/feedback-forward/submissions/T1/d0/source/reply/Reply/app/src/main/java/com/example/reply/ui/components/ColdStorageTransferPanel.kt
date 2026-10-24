/*
 * Copyright 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
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
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.reply.R

data class TransferHandlingNote(val id: String, val title: String, val body: String)

data class ColdStorageTransfer(
    val id: String,
    val title: String,
    val destination: String,
    val temperatureRange: String,
    val sealIntact: Boolean,
    val coolantReady: Boolean,
    val notes: List<TransferHandlingNote>,
)

/** Records a release request; its caller handles physical inventory and handoff. */
@Composable
fun ColdStorageTransferPanel(
    transfer: ColdStorageTransfer,
    onAcknowledgementChange: (Boolean) -> Unit,
    onRelease: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    // A different caller identity starts a new local interaction, with no callbacks.
    var handlingOpen by remember(transfer.id) { mutableStateOf(false) }
    var acknowledged by remember(transfer.id) { mutableStateOf(false) }
    var requested by remember(transfer.id) { mutableStateOf(false) }

    val canRelease = transfer.sealIntact && transfer.coolantReady && acknowledged && !requested
    val status = when {
        !transfer.sealIntact -> "Seal needs attention" to TransferPanelColors.Blocked
        !transfer.coolantReady -> "Coolant not ready" to TransferPanelColors.Blocked
        requested -> "Release requested" to TransferPanelColors.Requested
        acknowledged -> "Ready for release" to TransferPanelColors.Ready
        else -> "Awaiting check" to TransferPanelColors.Waiting
    }
    val disclosureLabel = if (handlingOpen) "Hide handling" else "Review handling"
    val choiceLabel = if (acknowledged) "Seal check confirmed" else "Confirm seal checked"

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(TransferPanelColors.Canvas)
            .testTag("transfer.canvas")
            .semantics(mergeDescendants = false) { }
            .padding(8.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.White)
                .testTag("transfer.surface")
                .semantics(mergeDescendants = false) { }
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Box(
                Modifier
                    .size(width = 6.dp, height = 40.dp)
                    .background(TransferPanelColors.Ink)
                    .testTag("transfer.inkMark")
                    .semantics { contentDescription = "Ink accent" },
            )
            Text(
                text = transfer.title,
                modifier = Modifier.testTag("transfer.title").semantics { heading() },
                color = TransferPanelColors.Ink,
                fontSize = 22.sp,
                lineHeight = 28.sp,
                fontWeight = FontWeight.SemiBold,
                fontFamily = FontFamily.SansSerif,
            )
            PanelText(
                text = transfer.destination + " · " + transfer.temperatureRange,
                modifier = Modifier.testTag("transfer.subtitle"),
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(status.second)
                    .testTag("transfer.status")
                    .semantics(mergeDescendants = false) { contentDescription = status.first }
                    .heightIn(min = 56.dp)
                    .padding(16.dp),
                contentAlignment = Alignment.CenterStart,
            ) {
                PanelText(
                    text = status.first,
                    modifier = Modifier.testTag("transfer.statusText"),
                    heading = true,
                )
            }

            Button(
                onClick = { handlingOpen = !handlingOpen },
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("transfer.disclosure"),
                shape = RectangleShape,
                colors = transparentButtonColors(),
                contentPadding = PaddingValues(vertical = 8.dp),
                elevation = null,
            ) {
                PanelText(
                    text = disclosureLabel,
                    heading = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }

            if (handlingOpen) {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    transfer.notes.forEachIndexed { index, note ->
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            PanelText(
                                text = note.title,
                                heading = true,
                                modifier = Modifier
                                    .testTag("transfer.section.$index.heading")
                                    .semantics { heading() },
                            )
                            PanelText(
                                text = note.body,
                                modifier = Modifier.testTag("transfer.section.$index.body"),
                            )
                        }
                    }
                }
            }

            Button(
                onClick = {
                    if (!requested) {
                        acknowledged = !acknowledged
                        onAcknowledgementChange(acknowledged)
                    }
                },
                enabled = !requested,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 48.dp)
                    .testTag("transfer.choice")
                    .semantics { selected = acknowledged },
                shape = RectangleShape,
                colors = transparentButtonColors(),
                contentPadding = PaddingValues(vertical = 8.dp),
                elevation = null,
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.Top,
                ) {
                    Box(
                        Modifier.size(24.dp).padding(3.dp)
                            .border(1.5.dp, TransferPanelColors.Ink, RectangleShape),
                    ) {
                        if (acknowledged) {
                            Icon(
                                painter = painterResource(R.drawable.ic_check),
                                contentDescription = null,
                                tint = TransferPanelColors.Ink,
                                modifier = Modifier.fillMaxSize(),
                            )
                        }
                    }
                    PanelText(text = choiceLabel, modifier = Modifier.weight(1f))
                }
            }

            Button(
                onClick = {
                    // Recheck inside the action as well as exposing native disabled state.
                    if (transfer.sealIntact && transfer.coolantReady && acknowledged && !requested) {
                        requested = true
                        onRelease(transfer.id)
                    }
                },
                enabled = canRelease,
                modifier = Modifier.fillMaxWidth().height(56.dp).testTag("transfer.primary"),
                shape = RectangleShape,
                colors = ButtonDefaults.buttonColors(
                    containerColor = TransferPanelColors.Enabled,
                    contentColor = Color.White,
                    disabledContainerColor = TransferPanelColors.Disabled,
                    disabledContentColor = TransferPanelColors.Ink,
                ),
                contentPadding = PaddingValues(0.dp),
                elevation = null,
            ) {
                Text(
                    text = if (requested) "Requested" else "Release transfer",
                    modifier = Modifier.fillMaxSize().wrapContentHeight(Alignment.CenterVertically),
                    fontSize = 17.sp,
                    lineHeight = 24.sp,
                    fontWeight = FontWeight.SemiBold,
                    fontFamily = FontFamily.SansSerif,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

@Composable
private fun PanelText(text: String, modifier: Modifier = Modifier, heading: Boolean = false) {
    Text(
        text = text,
        modifier = modifier,
        color = TransferPanelColors.Ink,
        fontSize = if (heading) 17.sp else 16.sp,
        lineHeight = 24.sp,
        fontWeight = if (heading) FontWeight.SemiBold else FontWeight.Normal,
        fontFamily = FontFamily.SansSerif,
    )
}

@Composable
private fun transparentButtonColors() = ButtonDefaults.buttonColors(
    containerColor = Color.Transparent,
    contentColor = TransferPanelColors.Ink,
    disabledContainerColor = Color.Transparent,
    disabledContentColor = TransferPanelColors.Ink,
)

private object TransferPanelColors {
    val Canvas = Color(0xFFF4F6FA)
    val Ink = Color(0xFF172B4D)
    val Waiting = Color(0xFFE9EFF8)
    val Ready = Color(0xFFDDF4EC)
    val Requested = Color(0xFFDDEBFF)
    val Blocked = Color(0xFFFFE5B3)
    val Enabled = Color(0xFF2463C5)
    val Disabled = Color(0xFFD8DEE8)
}
