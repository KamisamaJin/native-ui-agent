package com.example.reply.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTag
import androidx.compose.ui.semantics.text
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class MenuReplacementOption(
    val id: String,
    val title: String,
    val detail: String,
    val pricePerServingCents: Int,
    val minimumServings: Int,
    val maximumServings: Int,
    val available: Boolean,
)

data class MenuChangeModel(
    val requestID: String,
    val revision: Int,
    val orderReference: String,
    val venue: String,
    val occasion: String,
    val originalDish: String,
    val respondBy: String,
    val requestedServings: Int,
    val prepaidTotalCents: Int,
    val trayReturnCreditCents: Int,
    val notice: String,
    val options: List<MenuReplacementOption>,
    val kitchenNotes: List<String>,
)

data class MenuChangeSubmission(
    val requestID: String,
    val revision: Int,
    val optionID: String,
    val servings: Int,
    val useTrayCredit: Boolean,
    val balanceCents: Int,
) {
    val wireValue: String
        get() = "menu.submit|request=$requestID|revision=$revision|option=$optionID" +
            "|servings=$servings|trayCredit=$useTrayCredit|balanceCents=$balanceCents"
}

private data class MenuReviewDraft(
    val requestID: String,
    val revision: Int,
    val selectedID: String? = null,
    val servings: Int,
    val useTrayCredit: Boolean = false,
    val accepted: Boolean = false,
    val sent: Boolean = false,
) {
    fun reconciled(model: MenuChangeModel): MenuReviewDraft {
        if (requestID != model.requestID) return initial(model)
        if (revision == model.revision) return this
        val option = selectedOption(model)
        return copy(
            revision = model.revision,
            selectedID = option?.id,
            servings = option?.let { servings.coerceIn(it.minimumServings, it.maximumServings) } ?: servings,
            useTrayCredit = useTrayCredit && model.trayReturnCreditCents > 0,
            accepted = false,
            sent = false,
        )
    }

    fun selectedOption(model: MenuChangeModel): MenuReplacementOption? =
        model.options.firstOrNull { it.id == selectedID && it.available }

    fun appliedCredit(model: MenuChangeModel): Int =
        if (useTrayCredit) model.trayReturnCreditCents else 0

    fun balance(model: MenuChangeModel): Int? = selectedOption(model)?.let {
        it.pricePerServingCents * servings - model.prepaidTotalCents - appliedCredit(model)
    }

    val status: String
        get() = when {
            sent -> "Request sent. Waiting for the kitchen."
            selectedID == null -> "Choose a replacement to continue."
            !accepted -> "Review the balance and accept the updated menu."
            else -> "Ready to send to the kitchen."
        }

    companion object {
        fun initial(model: MenuChangeModel) = MenuReviewDraft(
            requestID = model.requestID,
            revision = model.revision,
            servings = model.requestedServings,
        )
    }
}

private class MenuReviewPalette(dark: Boolean) {
    val canvas = if (dark) Color(0xFF101A15) else Color(0xFFF5F2EA)
    val surface = if (dark) Color(0xFF19291F) else Color(0xFFFFFFFF)
    val ink = if (dark) Color(0xFFF2F7F3) else Color(0xFF1F2A25)
    val secondary = if (dark) Color(0xFFB8C8BC) else Color(0xFF59665E)
    val accent = if (dark) Color(0xFF8DDBAF) else Color(0xFF216B4A)
    val selection = if (dark) Color(0xFF254735) else Color(0xFFE9F3ED)
    val border = if (dark) Color(0xFF3D5848) else Color(0xFFCBD5CC)
    val noticeInk = if (dark) Color(0xFFFFCA80) else Color(0xFF975A16)
    val noticeFill = if (dark) Color(0xFF382A17) else Color(0xFFFFF0D9)
    val sendInk = if (dark) Color(0xFF102017) else Color(0xFFFFFFFF)
    val disabledFill = if (dark) Color(0xFF344A3C) else Color(0xFFD9E2DC)
    val disabledInk = if (dark) Color(0xFF93A99A) else Color(0xFF68756D)
}

private fun menuMoney(cents: Int): String {
    val magnitude = kotlin.math.abs(cents.toLong())
    return "\$${magnitude / 100}.${(magnitude % 100).toString().padStart(2, '0')}"
}

/** A non-scrolling panel; its caller supplies the width and owns scrolling and delivery. */
@Composable
fun MenuChangeReviewPanel(
    model: MenuChangeModel,
    onSubmit: (MenuChangeSubmission) -> Unit,
) {
    var draft by remember { mutableStateOf(MenuReviewDraft.initial(model)) }
    // Reconcile before emitting UI so every control and total uses the new snapshot.
    // The remember slot and the component keep their identity across revisions.
    val current = draft.reconciled(model)
    if (draft != current) draft = current

    val palette = MenuReviewPalette(MaterialTheme.colorScheme.background.luminance() < 0.5f)
    val option = current.selectedOption(model)
    val canSend = option != null && current.accepted && !current.sent

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .testTag("menu.canvas")
            .clip(RoundedCornerShape(20.dp))
            .background(palette.canvas)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        horizontalAlignment = Alignment.Start,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MenuText("MENU CHANGE", palette.secondary, 12.sp, FontWeight.Medium)
            MenuText(
                model.occasion, palette.ink, 28.sp, FontWeight.Bold,
                Modifier.testTag("menu.title").semantics { heading() },
            )
            MenuText(
                "Order ${model.orderReference} · ${model.venue} · revision ${model.revision}",
                palette.secondary, 13.sp, modifier = Modifier.testTag("menu.context"),
            )
            MenuText(
                "Replacing: ${model.originalDish} · ${model.requestedServings} servings",
                palette.ink, 13.sp, modifier = Modifier.testTag("menu.original"),
            )
            MenuText("Please respond by ${model.respondBy}", palette.secondary, 13.sp)
        }

        Column(
            modifier = menuCard(palette.noticeFill, palette.border),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            MenuText(model.notice, palette.noticeInk, modifier = Modifier.testTag("menu.notice"))
        }

        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MenuHeading("Choose a replacement", palette)
            model.options.forEach { replacement ->
                MenuOptionButton(replacement, current, palette) {
                    val next = draft.reconciled(model)
                    val chosen = model.options.firstOrNull { it.id == replacement.id && it.available }
                    if (!next.sent && chosen != null && next.selectedID != chosen.id) {
                        draft = next.copy(
                            selectedID = chosen.id,
                            servings = next.servings.coerceIn(chosen.minimumServings, chosen.maximumServings),
                            accepted = false,
                        )
                    }
                }
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MenuHeading("Servings", palette)
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                MenuQuantityButton(
                    "−", "Decrease servings", "menu.decrease", palette,
                    enabled = !current.sent && option != null && current.servings > option.minimumServings,
                ) {
                    val next = draft.reconciled(model)
                    val selected = next.selectedOption(model)
                    if (!next.sent && selected != null && next.servings > selected.minimumServings) {
                        draft = next.copy(servings = next.servings - 1, accepted = false)
                    }
                }
                MenuText(
                    "${current.servings} servings", palette.ink, 20.sp, FontWeight.SemiBold,
                    Modifier.weight(1f).testTag("menu.servings"),
                )
                MenuQuantityButton(
                    "+", "Increase servings", "menu.increase", palette,
                    enabled = !current.sent && option != null && current.servings < option.maximumServings,
                ) {
                    val next = draft.reconciled(model)
                    val selected = next.selectedOption(model)
                    if (!next.sent && selected != null && next.servings < selected.maximumServings) {
                        draft = next.copy(servings = next.servings + 1, accepted = false)
                    }
                }
            }
        }

        MenuSwitch(
            label = "Use tray return credit",
            supporting = "Offered credit ${menuMoney(model.trayReturnCreditCents)}",
            identifier = "menu.credit",
            checked = current.useTrayCredit,
            enabled = !current.sent && model.trayReturnCreditCents > 0,
            palette = palette,
        ) { value ->
            val next = draft.reconciled(model)
            if (!next.sent && model.trayReturnCreditCents > 0 && value != next.useTrayCredit) {
                draft = next.copy(useTrayCredit = value, accepted = false)
            }
        }

        Column(
            modifier = Modifier.testTag("menu.summary").then(menuCard(palette.surface, palette.border)),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            MenuHeading("Balance", palette)
            MenuText(
                option?.title ?: "No replacement selected", palette.ink, weight = FontWeight.SemiBold,
                modifier = Modifier.testTag("menu.selection"),
            )
            MenuMoneyLine(
                "Replacement total",
                option?.let { menuMoney(it.pricePerServingCents * current.servings) } ?: "—",
                "menu.replacementTotal", palette,
            )
            MenuMoneyLine("Already paid", menuMoney(model.prepaidTotalCents), "menu.prepaid", palette)
            MenuMoneyLine("Tray credit applied", menuMoney(current.appliedCredit(model)), "menu.creditApplied", palette)
            MenuBalance(current.balance(model), palette)
        }

        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MenuHeading("Kitchen notes", palette)
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                model.kitchenNotes.forEachIndexed { index, paragraph ->
                    MenuText(
                        paragraph, palette.ink,
                        modifier = if (index == model.kitchenNotes.lastIndex) {
                            Modifier.testTag("menu.notes.last")
                        } else Modifier,
                    )
                }
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                MenuHeading("Your confirmation", palette)
                MenuSwitch(
                    label = "I accept the replacement, serving count, and balance shown.",
                    identifier = "menu.ack",
                    checked = current.accepted,
                    enabled = option != null && !current.sent,
                    palette = palette,
                ) { value ->
                    val next = draft.reconciled(model)
                    if (!next.sent && next.selectedOption(model) != null) {
                        draft = next.copy(accepted = value)
                    }
                }
            }
            MenuText(current.status, palette.secondary, modifier = Modifier.testTag("menu.status"))
            Button(
                onClick = {
                    val next = draft.reconciled(model)
                    val selected = next.selectedOption(model)
                    val balance = next.balance(model)
                    if (!next.sent && next.accepted && selected != null && balance != null) {
                        onSubmit(
                            MenuChangeSubmission(
                                requestID = model.requestID,
                                revision = model.revision,
                                optionID = selected.id,
                                servings = next.servings,
                                useTrayCredit = next.useTrayCredit,
                                balanceCents = balance,
                            ),
                        )
                        draft = next.copy(sent = true)
                    }
                },
                enabled = canSend,
                modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp).testTag("menu.submit"),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = palette.accent,
                    contentColor = palette.sendInk,
                    disabledContainerColor = palette.disabledFill,
                    disabledContentColor = palette.disabledInk,
                ),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 14.dp),
            ) {
                Text(
                    text = if (current.sent) "Request sent" else "Send replacement request",
                    style = TextStyle(
                        fontFamily = FontFamily.Default, fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold, textAlign = TextAlign.Center,
                    ),
                )
            }
        }
    }
}

@Composable
private fun MenuText(
    value: String,
    color: Color,
    size: TextUnit = 15.sp,
    weight: FontWeight = FontWeight.Normal,
    modifier: Modifier = Modifier,
) {
    Text(
        text = value,
        modifier = modifier.fillMaxWidth(),
        color = color,
        style = TextStyle(
            fontFamily = FontFamily.Default, fontSize = size,
            fontWeight = weight, textAlign = TextAlign.Start,
        ),
    )
}

@Composable
private fun MenuHeading(value: String, palette: MenuReviewPalette) {
    MenuText(value, palette.ink, 18.sp, FontWeight.SemiBold, Modifier.semantics { heading() })
}

private fun menuCard(fill: Color, border: Color): Modifier = Modifier
    .fillMaxWidth()
    .clip(RoundedCornerShape(16.dp))
    .background(fill)
    .border(1.dp, border, RoundedCornerShape(16.dp))
    .padding(12.dp)

@Composable
private fun MenuOptionButton(
    option: MenuReplacementOption,
    current: MenuReviewDraft,
    palette: MenuReviewPalette,
    onClick: () -> Unit,
) {
    val isSelected = current.selectedID == option.id
    val enabled = option.available && !current.sent
    val fill = if (isSelected) palette.selection else palette.surface
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp)
            .testTag("menu.option.${option.id}")
            .semantics { contentDescription = option.title; selected = isSelected },
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, if (isSelected) palette.accent else palette.border),
        colors = ButtonDefaults.buttonColors(
            containerColor = fill, contentColor = palette.ink,
            disabledContainerColor = fill, disabledContentColor = palette.secondary,
        ),
        contentPadding = PaddingValues(12.dp),
    ) {
        // The native button exposes exactly its title; supporting copy stays in the visual flow.
        Column(
            modifier = Modifier.fillMaxWidth().clearAndSetSemantics { },
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            MenuText(option.title, if (enabled) palette.ink else palette.secondary, weight = FontWeight.SemiBold)
            MenuText(option.detail, palette.secondary, 13.sp)
            MenuText("${menuMoney(option.pricePerServingCents)} per serving", palette.secondary, 13.sp)
            MenuText("${option.minimumServings}–${option.maximumServings} servings", palette.secondary, 13.sp)
            if (!option.available) MenuText("Unavailable", palette.secondary, 13.sp)
        }
    }
}

@Composable
private fun MenuQuantityButton(
    symbol: String,
    label: String,
    identifier: String,
    palette: MenuReviewPalette,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.sizeIn(minWidth = 44.dp, minHeight = 44.dp)
            .testTag(identifier).semantics { contentDescription = label },
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, palette.border),
        colors = ButtonDefaults.buttonColors(
            containerColor = palette.surface, contentColor = palette.accent,
            disabledContainerColor = palette.disabledFill, disabledContentColor = palette.disabledInk,
        ),
        contentPadding = PaddingValues(8.dp),
    ) {
        Text(
            symbol, modifier = Modifier.clearAndSetSemantics { },
            style = TextStyle(fontFamily = FontFamily.Default, fontSize = 20.sp, fontWeight = FontWeight.SemiBold),
        )
    }
}

@Composable
private fun MenuSwitch(
    label: String,
    identifier: String,
    checked: Boolean,
    enabled: Boolean,
    palette: MenuReviewPalette,
    supporting: String? = null,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            MenuText(label, palette.ink)
            if (supporting != null) MenuText(supporting, palette.secondary, 13.sp)
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            enabled = enabled,
            modifier = Modifier.testTag(identifier).semantics { contentDescription = label },
            colors = SwitchDefaults.colors(
                checkedThumbColor = palette.sendInk,
                checkedTrackColor = palette.accent,
                checkedBorderColor = palette.accent,
                uncheckedThumbColor = palette.secondary,
                uncheckedTrackColor = palette.surface,
                uncheckedBorderColor = palette.border,
                disabledCheckedThumbColor = palette.disabledInk,
                disabledCheckedTrackColor = palette.disabledFill,
                disabledCheckedBorderColor = palette.border,
                disabledUncheckedThumbColor = palette.disabledInk,
                disabledUncheckedTrackColor = palette.disabledFill,
                disabledUncheckedBorderColor = palette.border,
            ),
        )
    }
}

@Composable
private fun MenuMoneyLine(label: String, value: String, identifier: String, palette: MenuReviewPalette) {
    Column(
        modifier = Modifier.fillMaxWidth().clearAndSetSemantics {
            testTag = identifier
            text = AnnotatedString("$label $value")
        },
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        MenuText(label, palette.secondary, 13.sp)
        MenuText(value, palette.ink)
    }
}

@Composable
private fun MenuBalance(cents: Int?, palette: MenuReviewPalette) {
    when {
        cents == null -> MenuText(
            "Select a dish to calculate the balance", palette.ink, modifier = Modifier.testTag("menu.balance"),
        )
        cents == 0 -> MenuText(
            "No balance due", palette.ink, 26.sp, FontWeight.Bold, Modifier.testTag("menu.balance"),
        )
        else -> {
            val label = if (cents < 0) "Refund" else "Additional payment"
            val color = if (cents < 0) palette.accent else palette.ink
            val value = menuMoney(cents)
            Column(
                modifier = Modifier.fillMaxWidth().clearAndSetSemantics {
                    testTag = "menu.balance"
                    text = AnnotatedString("$label $value")
                },
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                MenuText(label, color)
                MenuText(value, color, 26.sp, FontWeight.Bold)
            }
        }
    }
}
