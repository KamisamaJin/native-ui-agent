package com.example.reply.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private class ReturnColors(dark: Boolean) {
    val card = if (dark) Color(0xFF192224) else Color.White
    val panel = if (dark) Color(0xFF253033) else Color(0xFFF5F3EE)
    val text = if (dark) Color(0xFFF2F6F3) else Color(0xFF20282D)
    val secondary = if (dark) Color(0xFFB4C0BB) else Color(0xFF5D676C)
    val border = if (dark) Color(0xFF4A5A56) else Color(0xFFD7DDD9)
    val accent = if (dark) Color(0xFF8ED6BD) else Color(0xFF21645A)
    val onAccent = if (dark) Color(0xFF12382C) else Color.White
    val tint = if (dark) Color(0xFF223F36) else Color(0xFFEAF5EF)
    val disabled = if (dark) Color(0xFF34443C) else Color(0xFFDFE6E1)
    val onDisabled = if (dark) Color(0xFFBAC8C0) else Color(0xFF59655E)
    val urgent = if (dark) Color(0xFF4A3B1D) else Color(0xFFFFF0D2)
    val onUrgent = if (dark) Color(0xFFF7D58A) else Color(0xFF775004)
    val tiles = if (dark) listOf(Color(0xFF28483E), Color(0xFF52382F), Color(0xFF353951))
        else listOf(Color(0xFFDDEFE9), Color(0xFFF8E2D9), Color(0xFFE4E5F5))
}

@Composable
private fun RText(value: String, color: Color, size: Int = 15, strong: Boolean = false, modifier: Modifier = Modifier, textAlign: TextAlign? = null) {
    Text(text = value, modifier = modifier, color = color, fontSize = size.sp,
        fontFamily = FontFamily.Default, fontWeight = if (strong) FontWeight.SemiBold else FontWeight.Normal,
        softWrap = true, textAlign = textAlign)
}

/** A controlled, naturally sized card. The host owns scrolling and all business state. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ReturnResolutionCard(model: ReturnResolutionModel, onAction: (ReturnResolutionAction) -> Unit, modifier: Modifier = Modifier) {
    val c = ReturnColors(isSystemInDarkTheme())
    val option = model.options.firstOrNull { it.id == model.selectedOptionId && it.disabledReason == null }
    val size = model.sizes.firstOrNull { it.id == model.selectedSizeId && it.unavailableReason == null }
    val gate = when {
        model.options.none { it.disabledReason == null } -> model.strings.noOptions
        option == null -> model.strings.chooseOption
        option.kind == ReturnResolutionKind.EXCHANGE && size == null -> model.strings.chooseSize
        option.acknowledgementLabel != null && !model.acknowledgementAccepted -> model.strings.acceptTerms
        else -> model.strings.ready
    }
    val ready = model.options.any { it.disabledReason == null } && option != null &&
        (option.kind != ReturnResolutionKind.EXCHANGE || size != null) &&
        (option.acknowledgementLabel == null || model.acknowledgementAccepted)
    Column(modifier.fillMaxWidth().testTag("rr.card")
        .clip(RoundedCornerShape(20.dp)).background(c.card).border(1.dp, c.border, RoundedCornerShape(20.dp))
        .padding(16.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            RText(model.merchant, c.secondary, 12)
            RText(model.heading, c.text, 24, true, Modifier.testTag("rr.header.title").semantics { heading() })
            RText(model.orderReference, c.secondary, 13)
            RText(model.intro, c.text)
            RText(model.statusLabel, c.accent, 12, true, Modifier.testTag("rr.header.badge")
                .background(c.tint, RoundedCornerShape(20.dp)).padding(horizontal = 10.dp, vertical = 6.dp))
        }
        Row(Modifier.fillMaxWidth().testTag("rr.item").semantics(mergeDescendants = true) {}, horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            Canvas(Modifier.size(52.dp).background(c.tiles[model.item.accent.ordinal], RoundedCornerShape(12.dp)).padding(12.dp).clearAndSetSemantics {}) {
                val p = Path().apply { moveTo(this@Canvas.size.width * .5f, 0f); lineTo(this@Canvas.size.width, this@Canvas.size.height * .25f); lineTo(this@Canvas.size.width, this@Canvas.size.height * .75f); lineTo(this@Canvas.size.width * .5f, this@Canvas.size.height); lineTo(0f, this@Canvas.size.height * .75f); lineTo(0f, this@Canvas.size.height * .25f); close() }
                drawPath(p, c.accent, style = Stroke(1.6.dp.toPx()))
                drawLine(c.accent, Offset(0f, this.size.height * .25f), Offset(this.size.width * .5f, this.size.height * .5f), 1.6.dp.toPx())
                drawLine(c.accent, Offset(this.size.width, this.size.height * .25f), Offset(this.size.width * .5f, this.size.height * .5f), 1.6.dp.toPx())
                drawLine(c.accent, Offset(this.size.width * .5f, this.size.height * .5f), Offset(this.size.width * .5f, this.size.height), 1.6.dp.toPx())
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                RText(model.item.title, c.text, 17, true)
                RText(model.item.variant, c.secondary, 13)
                RText(model.item.quantityLabel, c.secondary, 13)
                RText(model.item.paidLabel, c.text, 13, true)
            }
        }
        when (model.status) {
            ReturnResolutionStatus.EDITING -> {
                model.deadline?.let { deadline ->
                    RText(deadline.text, if (deadline.urgent) c.onUrgent else c.secondary, 13, true,
                        Modifier.fillMaxWidth().testTag("rr.deadline").background(if (deadline.urgent) c.urgent else c.panel, RoundedCornerShape(10.dp)).padding(12.dp))
                }
                RText(model.contextMessage, c.secondary)
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    RText(model.optionsTitle, c.text, 17, true)
                    model.options.forEach { choice ->
                        val selected = choice.id == option?.id
                        Column(Modifier.fillMaxWidth().heightIn(min = 72.dp).testTag("rr.option.${choice.id}")
                            .clip(RoundedCornerShape(12.dp)).background(if (selected) c.tint else c.card)
                            .border(if (selected) 2.dp else 1.dp, if (selected) c.accent else c.border, RoundedCornerShape(12.dp))
                            .selectable(selected = selected, enabled = choice.disabledReason == null, role = Role.RadioButton,
                                onClick = { onAction(ReturnResolutionAction.SelectOption(choice.id)) }).padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.Top) {
                                RadioMark(selected, c)
                                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                    RText(choice.title, c.text, 17, true)
                                    RText(choice.description, c.secondary)
                                    RText(choice.amountLabel, c.text, 18, true)
                                    choice.tag?.let { RText(it, c.accent, 12, true, Modifier.background(c.tint, RoundedCornerShape(12.dp)).padding(horizontal = 8.dp, vertical = 4.dp)) }
                                    choice.disabledReason?.let { RText(it, c.secondary, 13, modifier = Modifier.testTag("rr.option.${choice.id}.reason")) }
                                }
                            }
                        }
                    }
                }
                option?.let { effective ->
                    Column(panelModifier("rr.detail", c), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        RText(effective.detailTitle, c.text, 17, true)
                        RText(effective.detailBody, c.secondary)
                    }
                    if (effective.kind == ReturnResolutionKind.EXCHANGE) {
                        Column(Modifier.fillMaxWidth().testTag("rr.sizes"), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            RText(model.sizesTitle, c.text, 17, true)
                            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                model.sizes.forEach { choice ->
                                    val selected = size?.id == choice.id
                                    Column(Modifier.widthIn(min = 48.dp).heightIn(min = 48.dp).testTag("rr.size.${choice.id}")
                                        .clip(RoundedCornerShape(12.dp)).background(if (selected) c.tint else c.card)
                                        .border(if (selected) 2.dp else 1.dp, if (selected) c.accent else c.border, RoundedCornerShape(12.dp))
                                        .selectable(selected, enabled = choice.unavailableReason == null, role = Role.Button,
                                            onClick = { onAction(ReturnResolutionAction.SelectSize(choice.id)) }).padding(12.dp),
                                        verticalArrangement = Arrangement.spacedBy(4.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                        RText(choice.label, c.text, 15, selected)
                                        choice.unavailableReason?.let { RText(it, c.secondary, 12, modifier = Modifier.testTag("rr.size.${choice.id}.reason")) }
                                    }
                                }
                            }
                        }
                    }
                    effective.acknowledgementLabel?.let { label ->
                        Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("rr.ack")
                            .toggleable(value = model.acknowledgementAccepted, role = Role.Checkbox,
                                onValueChange = { onAction(ReturnResolutionAction.SetAcknowledgement(!model.acknowledgementAccepted)) })
                            .padding(vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
                            CheckMark(model.acknowledgementAccepted, c)
                            RText(label, c.text, modifier = Modifier.weight(1f))
                        }
                    }
                }
                Column(panelModifier(null, c), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { onAction(ReturnResolutionAction.SetNotesExpanded(!model.notesExpanded)) },
                        modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp).testTag("rr.notes.toggle").semantics {
                            stateDescription = if (model.notesExpanded) model.strings.expandedValue else model.strings.collapsedValue
                        }, contentPadding = PaddingValues(0.dp), colors = ButtonDefaults.textButtonColors(contentColor = c.text)) {
                        RText(model.notes.title, c.text, 15, true, Modifier.weight(1f))
                        Chevron(model.notesExpanded, c)
                    }
                    if (model.notesExpanded) Column(Modifier.testTag("rr.notes.body"), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        RText(model.notes.body, c.secondary)
                        model.notes.bullets.forEach { bullet -> Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            RText("•", c.secondary, modifier = Modifier.clearAndSetSemantics {})
                            RText(bullet, c.secondary, modifier = Modifier.weight(1f))
                        } }
                    }
                }
                if (model.amountRows.isNotEmpty()) Column(Modifier.fillMaxWidth().testTag("rr.breakdown"), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    model.amountRows.forEach { AmountLine(it.label, it.value, it.emphasized, c) }
                }
                Summary(model, c)
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    RText(gate, c.secondary, 13, modifier = Modifier.testTag("rr.gate"))
                    ActionButton(option?.primaryLabel ?: model.idlePrimaryLabel, "rr.primary", ready, c) {
                        if (ready && option != null) onAction(ReturnResolutionAction.Submit(option.id,
                            if (option.kind == ReturnResolutionKind.EXCHANGE) size?.id else null,
                            if (option.acknowledgementLabel != null) model.acknowledgementAccepted else false))
                    }
                    TextButton(onClick = { onAction(ReturnResolutionAction.KeepPurchase) }, modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp).testTag("rr.keep"),
                        colors = ButtonDefaults.textButtonColors(contentColor = c.accent)) { RText(model.keepLabel, c.accent, 15, true) }
                }
            }
            ReturnResolutionStatus.SUBMITTING -> {
                Column(panelModifier("rr.progress", c).semantics(mergeDescendants = true) { stateDescription = model.strings.busyValue }, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    CircularProgressIndicator(Modifier.size(28.dp).clearAndSetSemantics {}, color = c.accent, strokeWidth = 3.dp)
                    RText(model.progressTitle, c.text, 17, true)
                    RText(model.progressBody, c.secondary)
                }
                Summary(model, c)
            }
            ReturnResolutionStatus.COMPLETE -> {
                Column(Modifier.fillMaxWidth().testTag("rr.result").background(c.tint, RoundedCornerShape(10.dp)).padding(12.dp).semantics(mergeDescendants = true) {}, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    CheckMark(true, c)
                    RText(model.resultTitle, c.accent, 17, true)
                    RText(model.resultBody, c.text)
                    RText(model.resultReference, c.secondary, 13)
                }
                Summary(model, c)
                ActionButton(model.doneLabel, "rr.done", true, c) { onAction(ReturnResolutionAction.Done) }
            }
        }
    }
}

private fun panelModifier(tag: String?, c: ReturnColors): Modifier = Modifier.fillMaxWidth()
    .then(if (tag != null) Modifier.testTag(tag) else Modifier).background(c.panel, RoundedCornerShape(10.dp)).padding(12.dp)

@Composable private fun Summary(m: ReturnResolutionModel, c: ReturnColors) {
    Column(Modifier.fillMaxWidth().testTag("rr.summary"), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        AmountLine(m.totalLabel, m.totalValue, true, c, true)
        RText(m.totalFootnote, c.secondary, 13)
    }
}
@Composable private fun AmountLine(label: String, value: String, strong: Boolean, c: ReturnColors, total: Boolean = false) {
    val scale = LocalDensity.current.fontScale
    if (scale > 1.2f) Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        RText(label, c.text, if (total) 18 else 15, strong)
        RText(value, c.text, if (total) 20 else 15, strong, Modifier.align(Alignment.End), TextAlign.End)
    } else Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
        RText(label, c.text, if (total) 18 else 15, strong, Modifier.weight(1f))
        RText(value, c.text, if (total) 20 else 15, strong, Modifier.weight(1f), TextAlign.End)
    }
}
@Composable private fun ActionButton(label: String, tag: String, enabled: Boolean, c: ReturnColors, action: () -> Unit) {
    Button(onClick = action, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag(tag),
        shape = RoundedCornerShape(12.dp), contentPadding = PaddingValues(12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = c.accent, contentColor = c.onAccent, disabledContainerColor = c.disabled, disabledContentColor = c.onDisabled)) {
        RText(label, if (enabled) c.onAccent else c.onDisabled, 15, true)
    }
}
@Composable private fun RadioMark(selected: Boolean, c: ReturnColors) {
    Canvas(Modifier.size(22.dp).clearAndSetSemantics {}) {
        drawCircle(if (selected) c.accent else c.border, style = Stroke(2.dp.toPx()))
        if (selected) drawCircle(c.accent, radius = this.size.minDimension * .25f)
    }
}
@Composable private fun CheckMark(checked: Boolean, c: ReturnColors) {
    Canvas(Modifier.size(24.dp).clearAndSetSemantics {}) {
        drawRoundRect(if (checked) c.accent else c.border, cornerRadius = androidx.compose.ui.geometry.CornerRadius(4.dp.toPx()), style = Stroke(2.dp.toPx()))
        if (checked) {
            val p = Path().apply { moveTo(this@Canvas.size.width * .2f, this@Canvas.size.height * .5f); lineTo(this@Canvas.size.width * .43f, this@Canvas.size.height * .73f); lineTo(this@Canvas.size.width * .8f, this@Canvas.size.height * .27f) }
            drawPath(p, c.accent, style = Stroke(2.5.dp.toPx()))
        }
    }
}
@Composable private fun Chevron(expanded: Boolean, c: ReturnColors) {
    val rtl = LocalLayoutDirection.current == LayoutDirection.Rtl
    Canvas(Modifier.padding(start = 8.dp).size(18.dp).clearAndSetSemantics {}) {
        val p = Path().apply {
            if (expanded) { moveTo(size.width * .2f, size.height * .35f); lineTo(size.width * .5f, size.height * .65f); lineTo(size.width * .8f, size.height * .35f) }
            else { val a = if (rtl) .65f else .35f; val b = 1f - a; moveTo(size.width * a, size.height * .2f); lineTo(size.width * b, size.height * .5f); lineTo(size.width * a, size.height * .8f) }
        }
        drawPath(p, c.secondary, style = Stroke(2.dp.toPx()))
    }
}
