package com.example.reply.ui.printbatch

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class PrintBatchJob(val id: String, val title: String, val pages: Int, val copies: Int, val isColor: Boolean, val selected: Boolean, val locked: Boolean)
data class PrintBatchModel(val modelID: String, val budgetCredits: Int, val allowPriority: Boolean, val initialPaperMode: String, val initialPriority: Boolean, val initialExpanded: Boolean, val jobs: List<PrintBatchJob>)
data class PrintBatchPresentation(val isDark: Boolean, val textScale: Double, val isRTL: Boolean)

private data class BatchPalette(val surface: Color, val text: Color, val muted: Color, val accent: Color, val ready: Color, val error: Color, val background: Color, val onAccent: Color)
private fun batchPalette(dark: Boolean) = if (dark) BatchPalette(Color(0xFF1B2532),Color(0xFFF2F5FA),Color(0xFFB7C4D5),Color(0xFF8BB0FF),Color(0xFF75D6AA),Color(0xFFFF9A96),Color(0xFF10161F),Color(0xFF14243A)) else BatchPalette(Color.White,Color(0xFF14243A),Color(0xFF53657A),Color(0xFF265FE4),Color(0xFF167650),Color(0xFFB63835),Color(0xFFF5F7FA),Color.White)

@Composable
fun PrintBatchApprovalCard(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: (String, Map<String, Any>) -> Unit, modifier: Modifier = Modifier) {
    var selection by remember(model.modelID) { mutableStateOf(model.jobs.filter { it.selected }.map { it.id }.toSet()) }
    var paperMode by remember(model.modelID) { mutableStateOf(model.initialPaperMode) }
    var priority by remember(model.modelID) { mutableStateOf(model.initialPriority) }
    var expanded by remember(model.modelID) { mutableStateOf(model.initialExpanded) }
    val p = batchPalette(presentation.isDark)
    val chosen = model.jobs.filter { it.id in selection }
    fun sheets(job: PrintBatchJob) = (if (paperMode == "duplex") (job.pages + 1) / 2 else job.pages) * job.copies
    fun ink(job: PrintBatchJob) = job.pages * job.copies * if (job.isColor) 3 else 1
    val printed = chosen.sumOf { it.pages * it.copies }
    val sheetCount = chosen.sumOf { sheets(it) }
    val inkCost = chosen.sumOf { ink(it) }
    val surcharge = if (chosen.isNotEmpty() && priority) 6 else 0
    val total = inkCost + sheetCount + surcharge
    val count = chosen.size
    val over = total > model.budgetCredits
    val approvalEnabled = count > 0 && !over
    val priorityEnabled = model.allowPriority && count > 0
    val status = if (count == 0) "No jobs" else if (over) "Over budget" else "Ready"
    val statusColor = if (count == 0) p.muted else if (over) p.error else p.ready
    val balance = if (count == 0) "No charge selected" else if (over) "Short by ${total - model.budgetCredits} cr" else "Balance after approval: ${model.budgetCredits - total} cr"
    val approval = if (count == 0) "Select a job to approve" else if (over) "Over budget by ${total-model.budgetCredits} cr" else "Approve $count jobs · $total cr"
    val scale = presentation.textScale
    CompositionLocalProvider(LocalLayoutDirection provides if (presentation.isRTL) LayoutDirection.Rtl else LayoutDirection.Ltr) {
        Column(modifier.fillMaxWidth().background(p.surface, RoundedCornerShape(16.dp)).testTag("printbatch.card").semantics { testTagsAsResourceId = true }.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.Top) {
                BatchText("Print budget check", "printbatch.title", 20, scale, p.text, FontWeight.SemiBold, Modifier.weight(1f))
                BatchText(status, "printbatch.status", 12, scale, statusColor, FontWeight.SemiBold, Modifier.widthIn(max=104.dp).background(statusColor.copy(alpha=0.13f),RoundedCornerShape(12.dp)).padding(horizontal=10.dp,vertical=4.dp))
            }
            Column(verticalArrangement=Arrangement.spacedBy(6.dp)) {
                BatchText("Estimated charge", "printbatch.charge.caption",12,scale,p.muted)
                BatchText("$total cr", "printbatch.charge.value",28,scale,p.text,FontWeight.Bold)
                BatchText("$count jobs • $printed pages • $sheetCount sheets", "printbatch.summary",14,scale,p.muted)
            }
            Column {
                model.jobs.forEachIndexed { index, job ->
                    Row(Modifier.fillMaxWidth().padding(vertical=12.dp),horizontalArrangement=Arrangement.spacedBy(8.dp),verticalAlignment=Alignment.Top) {
                        Checkbox(checked=job.id in selection,onCheckedChange={ checked ->
                            selection = if (checked) selection + job.id else selection - job.id
                            onEvent("selectionChanged", mapOf("jobIDs" to model.jobs.filter { it.id in selection }.map { it.id }))
                        },enabled=!job.locked,modifier=Modifier.size(48.dp).testTag("printbatch.job.${job.id}.toggle").semantics { contentDescription = (if (job.id in selection) "Deselect " else "Select ") + job.title; selected = job.id in selection },colors=CheckboxDefaults.colors(checkedColor=p.accent,uncheckedColor=p.muted,checkmarkColor=p.onAccent,disabledCheckedColor=p.muted,disabledUncheckedColor=p.muted.copy(alpha=.5f)))
                        Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(6.dp)) {
                            BatchText(job.title,"printbatch.job.${job.id}.title",14,scale,p.text,FontWeight.SemiBold)
                            val subtitle="${job.pages} pages × ${job.copies} copies • ${if(job.isColor) "Color" else "Mono"}${if(job.locked) " • Locked" else ""}"
                            BatchText(subtitle,"printbatch.job.${job.id}.subtitle",12,scale,p.muted)
                        }
                        BatchText("${ink(job)+sheets(job)} cr","printbatch.job.${job.id}.price",14,scale,p.text,modifier=Modifier.widthIn(max=62.dp))
                    }
                    if(index<model.jobs.lastIndex) Box(Modifier.fillMaxWidth().height(1.dp).background(p.muted.copy(alpha=.25f)))
                }
            }
            Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
                BatchText("Paper mode","printbatch.mode.title",14,scale,p.text,FontWeight.SemiBold)
                Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                    listOf("single" to "Single-sided", "duplex" to "Duplex").forEach { (mode,label) ->
                        val isSelected=mode==paperMode
                        BatchAction(label,"printbatch.mode.$mode",scale,if(isSelected)p.accent else p.surface,if(isSelected)p.onAccent else p.text,Modifier.weight(1f),isSelected=isSelected) {
                            if(mode!=paperMode) { paperMode=mode;onEvent("paperModeChanged",mapOf("paperMode" to mode)) }
                        }
                    }
                }
            }
            Column(verticalArrangement=Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp),verticalAlignment=Alignment.CenterVertically) {
                    Text("Priority handling",fontSize=(14*scale).sp,fontFamily=FontFamily.SansSerif,fontWeight=FontWeight.SemiBold,color=if(priorityEnabled)p.text else p.muted,modifier=Modifier.weight(1f))
                    Switch(checked=priority,onCheckedChange={ priority=it;onEvent("priorityChanged",mapOf("priority" to it)) },enabled=priorityEnabled,modifier=Modifier.heightIn(min=48.dp).widthIn(min=48.dp).testTag("printbatch.priority").semantics { contentDescription="Priority handling" },colors=SwitchDefaults.colors(checkedTrackColor=p.accent,checkedThumbColor=p.onAccent,uncheckedTrackColor=p.background,uncheckedThumbColor=p.muted,uncheckedBorderColor=p.muted,disabledCheckedTrackColor=p.muted.copy(alpha=.35f),disabledCheckedThumbColor=p.muted,disabledUncheckedTrackColor=p.background,disabledUncheckedThumbColor=p.muted.copy(alpha=.5f),disabledUncheckedBorderColor=p.muted.copy(alpha=.4f)))
                }
                BatchText(if(!model.allowPriority) "Priority unavailable for this batch." else if(priority) "Adds 6 cr to this batch." else "Add 6 cr for priority handling.","printbatch.priority.helper",12,scale,p.muted)
            }
            BatchAction(if(expanded)"Hide cost breakdown" else "Show cost breakdown","printbatch.breakdown.toggle",scale,p.surface,p.accent,Modifier.fillMaxWidth(),state=if(expanded)"Expanded" else "Collapsed",align=Alignment.CenterStart) { expanded=!expanded;onEvent("breakdownChanged",mapOf("expanded" to expanded)) }
            if(expanded) {
                Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    listOf(Triple("ink","Ink",inkCost),Triple("paper","Paper",sheetCount),Triple("priority","Priority",surcharge),Triple("total","Total",total)).forEach { (id,label,value) ->
                        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(12.dp),verticalAlignment=Alignment.Top) {
                            BatchText(label,"printbatch.breakdown.$id.label",12,scale,p.muted,modifier=Modifier.weight(1f))
                            BatchText("$value cr","printbatch.breakdown.$id.value",12,scale,p.muted)
                        }
                    }
                }
            }
            BatchText(balance,"printbatch.balance",14,scale,if(over&&count>0)p.error else p.text)
            BatchAction(approval,"printbatch.approve",scale,if(approvalEnabled)p.accent else p.muted.copy(alpha=.12f),if(approvalEnabled)p.onAccent else p.muted,Modifier.fillMaxWidth(),enabled=approvalEnabled) {
                onEvent("approve",mapOf("modelID" to model.modelID,"jobIDs" to chosen.map{it.id},"paperMode" to paperMode,"priority" to priority,"totalCredits" to total,"printedPages" to printed,"sheets" to sheetCount))
            }
        }
    }
}

@Composable
private fun BatchText(text: String,id: String,size: Int,scale: Double,color: Color,weight: FontWeight=FontWeight.Normal,modifier: Modifier=Modifier) {
    Text(text,modifier.testTag(id),color=color,fontSize=(size*scale).sp,fontWeight=weight,fontFamily=FontFamily.SansSerif)
}

@Composable
private fun BatchAction(label: String,id: String,scale: Double,background: Color,foreground: Color,modifier: Modifier=Modifier,enabled: Boolean=true,isSelected: Boolean?=null,state: String?=null,align: Alignment=Alignment.Center,onClick:()->Unit) {
    Box(modifier.heightIn(min=48.dp).background(background,RoundedCornerShape(10.dp)).testTag(id).semantics { if(isSelected!=null) selected=isSelected; if(state!=null)stateDescription=state }.clickable(enabled=enabled,role=Role.Button,onClick=onClick).padding(horizontal=8.dp,vertical=10.dp),contentAlignment=align) {
        Text(label,color=foreground,fontSize=(14*scale).sp,fontWeight=FontWeight.SemiBold,fontFamily=FontFamily.SansSerif)
    }
}
