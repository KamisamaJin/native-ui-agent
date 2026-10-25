package com.example.reply.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class ListeningBreakOption(
    val id: String,
    val title: String,
    val detail: String,
    val isAvailable: Boolean,
)

data class ListeningBreakInput(
    val sessionID: String,
    val title: String,
    val introduction: String,
    val options: List<ListeningBreakOption>,
    val quietNote: String,
    val footer: String,
)

@Composable
fun ListeningBreakPanel(
    input: ListeningBreakInput,
    onStart: (String, String) -> Unit,
    onCancel: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    // A full value change replaces local state during composition, before the
    // replacement is drawn. Equal values keep their existing local choices.
    var state by remember(input) { mutableStateOf(ListeningBreakState()) }
    val selectedOption = input.options.firstOrNull {
        it.id == state.selectedID && it.isAvailable
    }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .testTag("listening.canvas")
            .background(ListeningBreakColors.Canvas)
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        ListeningBreakText(
            input.title, 24.sp, ListeningBreakColors.Title,
            Modifier.testTag("listening.title"), FontWeight.SemiBold,
        )
        ListeningBreakText(
            input.introduction, 16.sp, ListeningBreakColors.Body,
            Modifier.testTag("listening.introduction"),
        )

        input.options.forEach { option ->
            val isSelected = state.selectedID == option.id
            val fill = when {
                !option.isAvailable -> ListeningBreakColors.UnavailableOption
                isSelected -> ListeningBreakColors.SelectedOption
                else -> ListeningBreakColors.Option
            }
            Button(
                onClick = {
                    if (!state.started && option.isAvailable) {
                        state = state.copy(selectedID = option.id, error = null)
                    }
                },
                enabled = option.isAvailable && !state.started,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 64.dp)
                    .testTag("listening.option.${option.id}")
                    .semantics {
                        contentDescription = option.title + " — " + option.detail
                        selected = isSelected
                    },
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, ListeningBreakColors.Border),
                colors = ButtonDefaults.buttonColors(
                    containerColor = fill,
                    contentColor = ListeningBreakColors.Body,
                    disabledContainerColor = fill,
                    disabledContentColor = ListeningBreakColors.Body,
                ),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                    horizontalAlignment = Alignment.Start,
                ) {
                    ListeningBreakText(
                        option.title, 16.sp,
                        if (option.isAvailable) ListeningBreakColors.Body else ListeningBreakColors.Muted,
                        weight = FontWeight.SemiBold,
                    )
                    ListeningBreakText(option.detail, 14.sp, ListeningBreakColors.Muted)
                }
            }
        }

        ListeningBreakText(
            input.quietNote, 16.sp, ListeningBreakColors.Body,
            Modifier.testTag("listening.note"),
        )

        // The row is the single labeled switch control; its Switch supplies the
        // native visual while the row owns the real toggle semantics and action.
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .testTag("listening.acknowledge")
                .toggleable(
                    value = state.acknowledged,
                    enabled = !state.started,
                    role = Role.Switch,
                    onValueChange = { value ->
                        state = state.copy(acknowledged = value, error = null)
                    },
                ),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            ListeningBreakText(
                "I have read the quiet-space note", 16.sp, ListeningBreakColors.Body,
                Modifier.weight(1f),
            )
            Switch(
                checked = state.acknowledged,
                onCheckedChange = null,
                enabled = !state.started,
                modifier = Modifier.clearAndSetSemantics { },
                colors = SwitchDefaults.colors(
                    checkedThumbColor = ListeningBreakColors.PrimaryInk,
                    checkedTrackColor = ListeningBreakColors.Primary,
                    checkedBorderColor = ListeningBreakColors.Primary,
                    uncheckedThumbColor = ListeningBreakColors.Muted,
                    uncheckedTrackColor = ListeningBreakColors.Option,
                    uncheckedBorderColor = ListeningBreakColors.Border,
                    disabledCheckedThumbColor = ListeningBreakColors.PrimaryInk,
                    disabledCheckedTrackColor = ListeningBreakColors.Primary,
                    disabledCheckedBorderColor = ListeningBreakColors.Primary,
                    disabledUncheckedThumbColor = ListeningBreakColors.Muted,
                    disabledUncheckedTrackColor = ListeningBreakColors.Option,
                    disabledUncheckedBorderColor = ListeningBreakColors.Border,
                ),
            )
        }

        ListeningBreakText(
            if (state.started) "Your listening break is ready." else "Choose a soundscape for your break.",
            16.sp, ListeningBreakColors.Body, Modifier.testTag("listening.status"),
        )
        state.error?.let { error ->
            ListeningBreakText(error, 16.sp, ListeningBreakColors.Error, Modifier.testTag("listening.error"))
        }
        if (state.started && selectedOption != null) {
            ListeningBreakText(
                "Ready to begin: " + selectedOption.title, 16.sp, ListeningBreakColors.Body,
                Modifier.testTag("listening.summary"),
            )
        }

        ListeningBreakAction(
            label = if (state.started) "Choose again" else "Start listening",
            identifier = "listening.primary",
            fill = ListeningBreakColors.Primary,
            ink = ListeningBreakColors.PrimaryInk,
            onClick = {
                val chosenOption = input.options.firstOrNull {
                    it.id == state.selectedID && it.isAvailable
                }
                if (state.started) {
                    state = ListeningBreakState()
                } else if (chosenOption == null || !state.acknowledged) {
                    state = state.copy(error = when {
                        chosenOption == null && !state.acknowledged ->
                            "Choose a soundscape and confirm the quiet-space note."
                        chosenOption == null -> "Choose an available soundscape."
                        else -> "Confirm the quiet-space note before starting."
                    })
                } else {
                    state = state.copy(started = true, error = null)
                    onStart(input.sessionID, chosenOption.id)
                }
            },
        )
        ListeningBreakAction(
            label = "Cancel",
            identifier = "listening.cancel",
            fill = ListeningBreakColors.Canvas,
            ink = ListeningBreakColors.Body,
            onClick = {
                state = ListeningBreakState()
                onCancel(input.sessionID)
            },
        )
        ListeningBreakText(
            input.footer, 14.sp, ListeningBreakColors.Muted,
            Modifier.testTag("listening.footer"),
        )
    }
}

private data class ListeningBreakState(
    val selectedID: String? = null,
    val acknowledged: Boolean = false,
    val started: Boolean = false,
    val error: String? = null,
)

@Composable
private fun ListeningBreakText(
    value: String,
    size: TextUnit,
    color: Color,
    modifier: Modifier = Modifier,
    weight: FontWeight = FontWeight.Normal,
) {
    Text(
        text = value,
        modifier = modifier.fillMaxWidth(),
        color = color,
        fontSize = size,
        fontWeight = weight,
        fontFamily = FontFamily.Default,
        textAlign = TextAlign.Start,
        softWrap = true,
        maxLines = Int.MAX_VALUE,
    )
}

@Composable
private fun ListeningBreakAction(
    label: String,
    identifier: String,
    fill: Color,
    ink: Color,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .widthIn(min = 120.dp)
            .heightIn(min = 48.dp)
            .testTag(identifier),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = fill, contentColor = ink),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        ListeningBreakText(label, 16.sp, ink, weight = FontWeight.SemiBold)
    }
}

private object ListeningBreakColors {
    val Canvas = Color(0xFFF2F6F4)
    val Option = Color(0xFFFFFFFF)
    val SelectedOption = Color(0xFFE8F3EF)
    val UnavailableOption = Color(0xFFF0F2F1)
    val Primary = Color(0xFF176B58)
    val PrimaryInk = Color(0xFFFFFFFF)
    val Title = Color(0xFF172F2A)
    val Body = Color(0xFF38564E)
    val Muted = Color(0xFF687A75)
    val Error = Color(0xFFB0382C)
    val Border = Color(0xFFABC6BC)
}
