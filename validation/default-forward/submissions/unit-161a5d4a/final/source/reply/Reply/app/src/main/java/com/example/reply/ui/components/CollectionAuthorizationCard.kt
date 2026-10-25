package com.example.reply.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
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
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.isTraversalGroup
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class CollectionAuthorizationData(
    val requestID: String,
    val title: String,
    val jobSummary: String,
    val pickupWindow: String,
    val notesClosedTitle: String,
    val notesOpenTitle: String,
    val notesBody: String,
    val selfTitle: String,
    val selfDetail: String,
    val delegateTitle: String,
    val delegateDetail: String,
    val acknowledgement: String,
    val confirmTitle: String,
    val sentTitle: String,
    val readyMessage: String,
    val needsAcknowledgementMessage: String,
    val sentMessage: String,
    val delegateUnavailableMessage: String,
    val delegateAvailable: Boolean,
)

/** Intrinsic content only: scrolling belongs to the caller. */
@Composable
fun CollectionAuthorizationCard(
    data: CollectionAuthorizationData,
    onEvent: (String) -> Unit,
) {
    var state by remember(data.requestID) { mutableStateOf(CollectionAuthorizationState()) }
    val palette = if (isSystemInDarkTheme()) CollectionPalette.Dark else CollectionPalette.Light
    val valid = state.collector == Collector.Self ||
        (data.delegateAvailable && state.acknowledged)
    val primaryEnabled = !state.submitted && valid

    fun choose(collector: Collector) {
        if (state.submitted || state.collector == collector ||
            (collector == Collector.Delegate && !data.delegateAvailable)
        ) return
        state = state.copy(collector = collector, acknowledged = false)
        onEvent("collector:${data.requestID}:${collector.eventValue}")
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(palette.surface, RoundedCornerShape(CollectionLayout.cardRadius))
            .testTag("collection.card")
            .semantics { isTraversalGroup = true }
            .padding(CollectionLayout.cardPadding),
        verticalArrangement = Arrangement.spacedBy(CollectionLayout.sectionGap),
        horizontalAlignment = Alignment.Start,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(CollectionLayout.textGap)) {
            CollectionText(
                data.title, CollectionTypography.titleSize, FontWeight.SemiBold, palette.ink,
                Modifier.fillMaxWidth().testTag("collection.title"),
            )
            CollectionText(
                data.jobSummary, CollectionTypography.metadataSize, FontWeight.Normal,
                palette.secondary, Modifier.fillMaxWidth().testTag("collection.summary"),
            )
            CollectionText(
                data.pickupWindow, CollectionTypography.metadataSize, FontWeight.Normal,
                palette.secondary, Modifier.fillMaxWidth().testTag("collection.window"),
            )
        }

        CollectionChoice(
            title = data.selfTitle,
            detail = data.selfDetail,
            selected = state.collector == Collector.Self,
            enabled = !state.submitted,
            identifier = "collection.self",
            palette = palette,
            onClick = { choose(Collector.Self) },
        )
        CollectionChoice(
            title = data.delegateTitle,
            detail = data.delegateDetail,
            selected = state.collector == Collector.Delegate,
            enabled = !state.submitted && data.delegateAvailable,
            identifier = "collection.delegate",
            palette = palette,
            onClick = { choose(Collector.Delegate) },
        )

        if (!data.delegateAvailable) {
            CollectionText(
                data.delegateUnavailableMessage, CollectionTypography.metadataSize, FontWeight.Normal,
                palette.secondary, Modifier.fillMaxWidth().testTag("collection.unavailable"),
            )
        }

        if (state.collector == Collector.Delegate) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(CollectionLayout.textGap),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CollectionText(
                    data.acknowledgement, CollectionTypography.bodySize, FontWeight.Normal,
                    palette.ink, Modifier.weight(1f),
                )
                Switch(
                    checked = state.acknowledged,
                    onCheckedChange = { acknowledged ->
                        if (!state.submitted && state.collector == Collector.Delegate &&
                            data.delegateAvailable && state.acknowledged != acknowledged
                        ) {
                            state = state.copy(acknowledged = acknowledged)
                            onEvent("ack:${data.requestID}:$acknowledged")
                        }
                    },
                    enabled = !state.submitted && data.delegateAvailable,
                    modifier = Modifier
                        .testTag("collection.ack")
                        .semantics { contentDescription = data.acknowledgement },
                    colors = SwitchDefaults.colors(
                        checkedTrackColor = palette.accent,
                        checkedThumbColor = palette.primaryInk,
                        checkedBorderColor = palette.accent,
                        uncheckedTrackColor = palette.neutralRow,
                        uncheckedThumbColor = palette.secondary,
                        uncheckedBorderColor = palette.secondary,
                        disabledCheckedTrackColor = palette.accent,
                        disabledCheckedThumbColor = palette.primaryInk,
                        disabledCheckedBorderColor = palette.accent,
                        disabledUncheckedTrackColor = palette.neutralRow,
                        disabledUncheckedThumbColor = palette.disabledInk,
                        disabledUncheckedBorderColor = palette.disabledInk,
                    ),
                )
            }
        }

        CollectionText(
            text = if (state.submitted) data.sentMessage else if (valid) data.readyMessage
                else data.needsAcknowledgementMessage,
            size = CollectionTypography.bodySize,
            weight = FontWeight.Normal,
            color = palette.secondary,
            modifier = Modifier.fillMaxWidth().testTag("collection.status")
                .semantics { liveRegion = LiveRegionMode.Polite },
        )

        TextButton(
            onClick = {
                val expanded = !state.notesExpanded
                state = state.copy(notesExpanded = expanded)
                onEvent("notes:${data.requestID}:${if (expanded) "open" else "closed"}")
            },
            modifier = Modifier.fillMaxWidth()
                .heightIn(min = CollectionLayout.disclosureMinHeight)
                .testTag("collection.notes"),
            colors = ButtonDefaults.textButtonColors(contentColor = palette.accent),
            contentPadding = PaddingValues(vertical = CollectionLayout.textGap),
            shape = RoundedCornerShape(CollectionLayout.controlRadius),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(CollectionLayout.textGap),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CollectionText(
                    if (state.notesExpanded) data.notesOpenTitle else data.notesClosedTitle,
                    CollectionTypography.bodySize, FontWeight.SemiBold, palette.accent,
                    Modifier.weight(1f),
                )
                CollectionText(
                    if (state.notesExpanded) "⌃" else "⌄",
                    CollectionTypography.bodySize, FontWeight.SemiBold, palette.accent,
                    Modifier.clearAndSetSemantics { },
                )
            }
        }

        if (state.notesExpanded) {
            CollectionText(
                data.notesBody, CollectionTypography.bodySize, FontWeight.Normal, palette.ink,
                Modifier.fillMaxWidth().testTag("collection.notesBody"),
            )
        }

        Button(
            onClick = {
                val currentlyValid = state.collector == Collector.Self ||
                    (data.delegateAvailable && state.acknowledged)
                if (!state.submitted && currentlyValid) {
                    val collector = state.collector
                    state = state.copy(submitted = true)
                    onEvent("submit:${data.requestID}:${collector.eventValue}")
                }
            },
            enabled = primaryEnabled,
            modifier = Modifier.fillMaxWidth()
                .heightIn(min = CollectionLayout.primaryMinHeight)
                .testTag("collection.confirm"),
            shape = RoundedCornerShape(CollectionLayout.controlRadius),
            colors = ButtonDefaults.buttonColors(
                containerColor = palette.accent,
                contentColor = palette.primaryInk,
                disabledContainerColor = palette.neutralRow,
                disabledContentColor = palette.disabledInk,
            ),
            elevation = null,
            contentPadding = PaddingValues(
                horizontal = CollectionLayout.rowPadding,
                vertical = CollectionLayout.sectionGap,
            ),
        ) {
            CollectionText(
                if (state.submitted) data.sentTitle else data.confirmTitle,
                CollectionTypography.bodySize, FontWeight.SemiBold,
                if (primaryEnabled) palette.primaryInk else palette.disabledInk,
                Modifier.fillMaxWidth(), TextAlign.Center,
            )
        }
    }
}

@Composable
private fun CollectionChoice(
    title: String,
    detail: String,
    selected: Boolean,
    enabled: Boolean,
    identifier: String,
    palette: CollectionPalette,
    onClick: () -> Unit,
) {
    val fill = if (selected) palette.selectedRow else palette.neutralRow
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth()
            .heightIn(min = CollectionLayout.rowMinHeight)
            .testTag(identifier)
            .semantics { this.selected = selected },
        shape = RoundedCornerShape(CollectionLayout.controlRadius),
        colors = ButtonDefaults.buttonColors(
            containerColor = fill,
            contentColor = palette.ink,
            disabledContainerColor = fill,
            disabledContentColor = palette.disabledInk,
        ),
        border = if (selected) BorderStroke(CollectionLayout.selectedBorderWidth, palette.accent)
            else null,
        elevation = null,
        contentPadding = PaddingValues(CollectionLayout.rowPadding),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(CollectionLayout.textGap),
            verticalAlignment = Alignment.Top,
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(CollectionLayout.textGap),
            ) {
                CollectionText(
                    title, CollectionTypography.rowTitleSize, FontWeight.SemiBold,
                    if (enabled) palette.ink else palette.disabledInk,
                )
                CollectionText(
                    detail, CollectionTypography.metadataSize, FontWeight.Normal,
                    if (enabled) palette.secondary else palette.disabledInk,
                )
            }
            CollectionText(
                if (selected) "●" else "○", 20.sp, FontWeight.Normal,
                if (enabled) palette.accent else palette.disabledInk,
                Modifier.clearAndSetSemantics { },
            )
        }
    }
}

@Composable
private fun CollectionText(
    text: String,
    size: TextUnit,
    weight: FontWeight,
    color: Color,
    modifier: Modifier = Modifier,
    alignment: TextAlign = TextAlign.Start,
) {
    Text(
        text = text,
        modifier = modifier,
        color = color,
        style = TextStyle(
            fontFamily = FontFamily.SansSerif,
            fontSize = size,
            fontWeight = weight,
            textAlign = alignment,
        ),
    )
}

private enum class Collector(val eventValue: String) {
    Self("self"), Delegate("delegate"),
}

private data class CollectionAuthorizationState(
    val collector: Collector = Collector.Self,
    val acknowledged: Boolean = false,
    val submitted: Boolean = false,
    val notesExpanded: Boolean = false,
)

private object CollectionTypography {
    val titleSize = 22.sp
    val rowTitleSize = 16.sp
    val bodySize = 15.sp
    val metadataSize = 13.sp
}

private object CollectionLayout {
    val cardPadding = 20.dp
    val rowPadding = 16.dp
    val sectionGap = 12.dp
    val textGap = 8.dp
    val cardRadius = 20.dp
    val controlRadius = 12.dp
    val selectedBorderWidth = 1.dp
    val rowMinHeight = 80.dp
    val primaryMinHeight = 48.dp
    val disclosureMinHeight = 48.dp
}

private data class CollectionPalette(
    val surface: Color,
    val ink: Color,
    val secondary: Color,
    val neutralRow: Color,
    val selectedRow: Color,
    val accent: Color,
    val disabledInk: Color,
    val primaryInk: Color,
) {
    companion object {
        val Light = CollectionPalette(
            surface = Color(0xFFFFFFFF), ink = Color(0xFF172B3A),
            secondary = Color(0xFF526675), neutralRow = Color(0xFFF1F5F8),
            selectedRow = Color(0xFFDFF3EE), accent = Color(0xFF007F78),
            disabledInk = Color(0xFF687C8A), primaryInk = Color(0xFFFFFFFF),
        )
        val Dark = CollectionPalette(
            surface = Color(0xFF142232), ink = Color(0xFFF3F6FA),
            secondary = Color(0xFFB6C7D5), neutralRow = Color(0xFF223548),
            selectedRow = Color(0xFF164C50), accent = Color(0xFF4FD1C5),
            disabledInk = Color(0xFF8DA4B5), primaryInk = Color(0xFF102C30),
        )
    }
}
