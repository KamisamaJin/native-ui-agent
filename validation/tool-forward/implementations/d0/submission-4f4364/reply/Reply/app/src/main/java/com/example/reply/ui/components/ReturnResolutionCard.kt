package com.example.reply.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private data class RRColors(val card: Color, val panel: Color, val text: Color, val secondary: Color,
    val border: Color, val accent: Color, val foreground: Color, val tint: Color,
    val disabled: Color, val disabledText: Color, val urgent: Color, val urgentText: Color,
    val teal: Color, val coral: Color, val indigo: Color)

@Composable private fun rrColors(): RRColors = if (isSystemInDarkTheme()) RRColors(
    Color(0xFF192224),Color(0xFF253033),Color(0xFFF2F6F3),Color(0xFFB4C0BB),
    Color(0xFF4A5A56),Color(0xFF8ED6BD),Color(0xFF12382C),Color(0xFF223F36),
    Color(0xFF34443C),Color(0xFFBAC8C0),Color(0xFF4A3B1D),Color(0xFFF7D58A),
    Color(0xFF28483E),Color(0xFF52382F),Color(0xFF353951)) else RRColors(
    Color(0xFFFFFFFF),Color(0xFFF5F3EE),Color(0xFF20282D),Color(0xFF5D676C),
    Color(0xFFD7DDD9),Color(0xFF21645A),Color(0xFFFFFFFF),Color(0xFFEAF5EF),
    Color(0xFFDFE6E1),Color(0xFF59655E),Color(0xFFFFF0D2),Color(0xFF775004),
    Color(0xFFDDEFE9),Color(0xFFF8E2D9),Color(0xFFE4E5F5))

@Composable private fun RRText(value: String, color: Color, size: Int = 15,
    strong: Boolean = false, modifier: Modifier = Modifier) {
    Text(value, modifier, color = color, style = TextStyle(fontFamily = FontFamily.Default,
        fontSize = size.sp, lineHeight = (size * 1.35f).sp,
        fontWeight = if (strong) FontWeight.SemiBold else FontWeight.Normal))
}

@Composable private fun RRPill(value: String, c: RRColors, modifier: Modifier = Modifier) {
    RRText(value,c.accent,12,true,modifier.background(c.tint,RoundedCornerShape(16.dp))
        .padding(horizontal=10.dp,vertical=6.dp))
}

@Composable private fun RRIndicator(selected: Boolean, c: RRColors) {
    Canvas(Modifier.size(24.dp).clearAndSetSemantics {}) {
        drawCircle(if(selected)c.accent else c.border, radius=size.minDimension/2-2.dp.toPx(), style=Stroke(2.dp.toPx()))
        if(selected) drawCircle(c.accent, radius=6.dp.toPx())
    }
}

@Composable private fun RRButton(label: String, tag: String, c: RRColors, enabled: Boolean = true,
    primary: Boolean = true, onClick: () -> Unit) {
    val shape=RoundedCornerShape(12.dp)
    Box(Modifier.fillMaxWidth().heightIn(min=if(primary)48.dp else 44.dp).clip(shape)
        .background(if(primary) { if(enabled)c.accent else c.disabled } else Color.Transparent)
        .testTag(tag).clickable(enabled=enabled,role=Role.Button,onClick={if(enabled)onClick()})
        .padding(horizontal=16.dp,vertical=12.dp), contentAlignment=Alignment.Center) {
        RRText(label,if(primary){if(enabled)c.foreground else c.disabledText}else c.accent,15,true)
    }
}

/** A controlled return decision. All changes are requests delivered to the caller. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ReturnResolutionCard(model: ReturnResolutionModel, onAction: (ReturnResolutionAction) -> Unit,
    modifier: Modifier = Modifier) {
    val c=rrColors()
    val option=model.options.firstOrNull { it.id==model.selectedOptionId && it.disabledReason==null }
    val effectiveSize=model.sizes.firstOrNull { it.id==model.selectedSizeId && it.unavailableReason==null }
    val gate=when {
        model.options.none { it.disabledReason==null } -> model.strings.noOptions
        option==null -> model.strings.chooseOption
        option.kind==ReturnResolutionKind.EXCHANGE && effectiveSize==null -> model.strings.chooseSize
        option.acknowledgementLabel!=null && !model.acknowledgementAccepted -> model.strings.acceptTerms
        else -> model.strings.ready
    }
    val canSubmit=option!=null && (option.kind!=ReturnResolutionKind.EXCHANGE || effectiveSize!=null) &&
        (option.acknowledgementLabel==null || model.acknowledgementAccepted)
    Column(modifier.fillMaxWidth().testTag("rr.card").background(c.card,RoundedCornerShape(20.dp))
        .border(1.dp,c.border,RoundedCornerShape(20.dp)).padding(16.dp),
        verticalArrangement=Arrangement.spacedBy(20.dp)) {
        Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
            RRText(model.merchant,c.secondary,12)
            RRText(model.heading,c.text,24,true,Modifier.testTag("rr.header.title").semantics { heading() })
            RRText(model.orderReference,c.secondary,13)
            RRText(model.intro,c.secondary)
            RRPill(model.statusLabel,c,Modifier.testTag("rr.header.badge"))
        }
        Row(Modifier.fillMaxWidth().testTag("rr.item").semantics(mergeDescendants=true) {},
            horizontalArrangement=Arrangement.spacedBy(12.dp),verticalAlignment=Alignment.Top) {
            val tile=when(model.item.accent) { ReturnResolutionAccent.TEAL->c.teal;ReturnResolutionAccent.CORAL->c.coral;ReturnResolutionAccent.INDIGO->c.indigo }
            Canvas(Modifier.size(52.dp).background(tile,RoundedCornerShape(12.dp)).clearAndSetSemantics {}) {
                val x=size.width; val y=size.height
                drawRect(c.accent,Offset(x*.25f,y*.28f),Size(x*.5f,y*.46f),style=Stroke(1.7.dp.toPx()))
                drawLine(c.accent,Offset(x*.25f,y*.43f),Offset(x*.75f,y*.43f),1.7.dp.toPx())
                drawLine(c.accent,Offset(x*.5f,y*.28f),Offset(x*.5f,y*.74f),1.7.dp.toPx())
            }
            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(4.dp)) {
                RRText(model.item.title,c.text,17,true)
                RRText(model.item.variant,c.secondary,13)
                RRText(model.item.quantityLabel,c.secondary,13)
                RRText(model.item.paidLabel,c.text,15,true)
            }
        }
        when(model.status) {
            ReturnResolutionStatus.EDITING -> {
                model.deadline?.let { d -> RRText(d.text,if(d.urgent)c.urgentText else c.secondary,13,true,
                    Modifier.fillMaxWidth().testTag("rr.deadline").background(if(d.urgent)c.urgent else c.panel,RoundedCornerShape(10.dp)).padding(12.dp)) }
                RRText(model.contextMessage,c.secondary)
                Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    RRText(model.optionsTitle,c.text,17,true)
                    model.options.forEach { o ->
                        val chosen=option?.id==o.id
                        Row(Modifier.fillMaxWidth().heightIn(min=72.dp).testTag("rr.option.${o.id}")
                            .clip(RoundedCornerShape(12.dp)).background(if(chosen)c.tint else c.card)
                            .border(if(chosen)2.dp else 1.dp,if(chosen)c.accent else c.border,RoundedCornerShape(12.dp))
                            .selectable(selected=chosen,enabled=o.disabledReason==null,role=Role.RadioButton,
                                onClick={if(o.disabledReason==null)onAction(ReturnResolutionAction.SelectOption(o.id))})
                            .padding(12.dp),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                            RRIndicator(chosen,c)
                            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                                RRText(o.title,c.text,17,true)
                                RRText(o.description,c.secondary)
                                RRText(o.amountLabel,c.text,18,true,Modifier.align(Alignment.End))
                                o.tag?.let { RRPill(it,c) }
                                o.disabledReason?.let { RRText(it,c.secondary,13,false,Modifier.testTag("rr.option.${o.id}.reason")) }
                            }
                        }
                    }
                }
                option?.let { o ->
                    Column(Modifier.fillMaxWidth().testTag("rr.detail").background(c.panel,RoundedCornerShape(10.dp)).padding(12.dp),
                        verticalArrangement=Arrangement.spacedBy(8.dp)) {
                        RRText(o.detailTitle,c.text,17,true)
                        RRText(o.detailBody,c.secondary)
                    }
                    if(o.kind==ReturnResolutionKind.EXCHANGE) {
                        Column(Modifier.fillMaxWidth().testTag("rr.sizes"),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                            RRText(model.sizesTitle,c.text,17,true)
                            FlowRow(horizontalArrangement=Arrangement.spacedBy(12.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                                model.sizes.forEach { s ->
                                    val chosen=effectiveSize?.id==s.id
                                    Column(Modifier.widthIn(min=48.dp).heightIn(min=48.dp).testTag("rr.size.${s.id}")
                                        .clip(RoundedCornerShape(12.dp)).background(if(chosen)c.tint else c.card)
                                        .border(if(chosen)2.dp else 1.dp,if(chosen)c.accent else c.border,RoundedCornerShape(12.dp))
                                        .selectable(chosen,enabled=s.unavailableReason==null,role=Role.RadioButton,
                                            onClick={if(s.unavailableReason==null)onAction(ReturnResolutionAction.SelectSize(s.id))})
                                        .padding(12.dp),verticalArrangement=Arrangement.spacedBy(4.dp),horizontalAlignment=Alignment.CenterHorizontally) {
                                        RRText(s.label,if(s.unavailableReason==null)c.text else c.secondary,15,chosen)
                                        s.unavailableReason?.let { RRText(it,c.secondary,12,false,Modifier.testTag("rr.size.${s.id}.reason")) }
                                    }
                                }
                            }
                        }
                    }
                    o.acknowledgementLabel?.let { label ->
                        Row(Modifier.fillMaxWidth().heightIn(min=48.dp).testTag("rr.ack")
                            .toggleable(model.acknowledgementAccepted,role=Role.Checkbox,
                                onValueChange={onAction(ReturnResolutionAction.SetAcknowledgement(!model.acknowledgementAccepted))})
                            .padding(vertical=8.dp),horizontalArrangement=Arrangement.spacedBy(12.dp),verticalAlignment=Alignment.Top) {
                            Canvas(Modifier.size(24.dp).clearAndSetSemantics {}) {
                                drawRect(c.accent,Offset(2.dp.toPx(),2.dp.toPx()),Size(size.width-4.dp.toPx(),size.height-4.dp.toPx()),style=Stroke(2.dp.toPx()))
                                if(model.acknowledgementAccepted) {
                                    drawLine(c.accent,Offset(size.width*.25f,size.height*.5f),Offset(size.width*.44f,size.height*.7f),2.dp.toPx())
                                    drawLine(c.accent,Offset(size.width*.44f,size.height*.7f),Offset(size.width*.8f,size.height*.28f),2.dp.toPx())
                                }
                            }
                            RRText(label,c.text,15,false,Modifier.weight(1f))
                        }
                    }
                }
                Column(Modifier.fillMaxWidth().background(c.panel,RoundedCornerShape(10.dp)).padding(12.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth().heightIn(min=44.dp).testTag("rr.notes.toggle")
                        .semantics { stateDescription=if(model.notesExpanded)model.strings.expandedValue else model.strings.collapsedValue }
                        .clickable(role=Role.Button){onAction(ReturnResolutionAction.SetNotesExpanded(!model.notesExpanded))},
                        horizontalArrangement=Arrangement.spacedBy(12.dp),verticalAlignment=Alignment.CenterVertically) {
                        RRText(model.notes.title,c.text,15,true,Modifier.weight(1f))
                        RRText(if(model.notesExpanded)"⌃" else "⌄",c.accent,18,true,Modifier.clearAndSetSemantics {})
                    }
                    if(model.notesExpanded) Column(Modifier.testTag("rr.notes.body"),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                        RRText(model.notes.body,c.secondary)
                        model.notes.bullets.forEach { bullet ->
                            Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                                RRText("•",c.secondary,15,false,Modifier.clearAndSetSemantics {})
                                RRText(bullet,c.secondary,15,false,Modifier.weight(1f))
                            }
                        }
                    }
                }
                if(model.amountRows.isNotEmpty()) Column(Modifier.fillMaxWidth().testTag("rr.breakdown"),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    model.amountRows.forEach { r ->
                        Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(4.dp)) {
                            RRText(r.label,c.secondary,15,r.emphasized)
                            RRText(r.value,c.text,15,r.emphasized,Modifier.align(Alignment.End))
                        }
                    }
                }
            }
            ReturnResolutionStatus.SUBMITTING -> Row(Modifier.fillMaxWidth().testTag("rr.progress")
                .semantics(mergeDescendants=true) { stateDescription=model.strings.busyValue }
                .background(c.panel,RoundedCornerShape(10.dp)).padding(12.dp),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                CircularProgressIndicator(Modifier.size(24.dp).clearAndSetSemantics {},color=c.accent,strokeWidth=2.dp)
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    RRText(model.progressTitle,c.text,17,true)
                    RRText(model.progressBody,c.secondary)
                }
            }
            ReturnResolutionStatus.COMPLETE -> Row(Modifier.fillMaxWidth().testTag("rr.result").semantics(mergeDescendants=true) {}
                .background(c.tint,RoundedCornerShape(10.dp)).padding(12.dp),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                RRText("✓",c.accent,24,true,Modifier.clearAndSetSemantics {})
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    RRText(model.resultTitle,c.accent,17,true)
                    RRText(model.resultBody,c.accent)
                    RRText(model.resultReference,c.accent,13)
                }
            }
        }
        Column(Modifier.fillMaxWidth().testTag("rr.summary"),verticalArrangement=Arrangement.spacedBy(8.dp)) {
            RRText(model.totalLabel,c.text,18,true)
            RRText(model.totalValue,c.text,24,true,Modifier.align(Alignment.End))
            RRText(model.totalFootnote,c.secondary,12)
        }
        if(model.status==ReturnResolutionStatus.EDITING) {
            Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
                RRText(gate,c.secondary,13,false,Modifier.testTag("rr.gate"))
                RRButton(option?.primaryLabel?:model.idlePrimaryLabel,"rr.primary",c,canSubmit) {
                    if(canSubmit && option!=null) onAction(ReturnResolutionAction.Submit(option.id,
                        if(option.kind==ReturnResolutionKind.EXCHANGE)effectiveSize?.id else null,
                        if(option.acknowledgementLabel!=null)model.acknowledgementAccepted else false))
                }
                RRButton(model.keepLabel,"rr.keep",c,primary=false){onAction(ReturnResolutionAction.KeepPurchase)}
            }
        } else if(model.status==ReturnResolutionStatus.COMPLETE) {
            RRButton(model.doneLabel,"rr.done",c){onAction(ReturnResolutionAction.Done)}
        }
    }
}
