package com.example.reply.ui.printbatch

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
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

private data class BatchColors(val surface: Color, val text: Color, val muted: Color, val accent: Color, val ready: Color, val error: Color, val background: Color, val onAccent: Color)

@Composable
fun PrintBatchApprovalCard(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: (String, Map<String, Any>) -> Unit, modifier: Modifier = Modifier) {
    var selected by remember(model.modelID) { mutableStateOf(model.jobs.filter { it.selected }.map { it.id }.toSet()) }
    var mode by remember(model.modelID) { mutableStateOf(model.initialPaperMode) }
    var priority by remember(model.modelID) { mutableStateOf(model.initialPriority) }
    var expanded by remember(model.modelID) { mutableStateOf(model.initialExpanded) }
    val c = if (presentation.isDark) BatchColors(Color(0xFF1B2532), Color(0xFFF2F5FA), Color(0xFFB7C4D5), Color(0xFF8BB0FF), Color(0xFF75D6AA), Color(0xFFFF9A96), Color(0xFF10161F), Color(0xFF14243A)) else BatchColors(Color.White, Color(0xFF14243A), Color(0xFF53657A), Color(0xFF265FE4), Color(0xFF167650), Color(0xFFB63835), Color(0xFFF5F7FA), Color.White)
    fun sheets(job: PrintBatchJob) = (if (mode == "duplex") (job.pages + 1) / 2 else job.pages) * job.copies
    fun ink(job: PrintBatchJob) = job.pages * job.copies * if (job.isColor) 3 else 1
    val jobs = model.jobs.filter { it.id in selected }
    val ids = jobs.map { it.id }
    val pageCount = jobs.sumOf { it.pages * it.copies }
    val sheetCount = jobs.sumOf { sheets(it) }
    val inkCost = jobs.sumOf { ink(it) }
    val surcharge = if (jobs.isNotEmpty() && priority) 6 else 0
    val total = inkCost + sheetCount + surcharge
    val over = total > model.budgetCredits
    val canApprove = jobs.isNotEmpty() && !over
    val status = if (jobs.isEmpty()) "No jobs" else if (over) "Over budget" else "Ready"
    val statusColor = if (jobs.isEmpty()) c.muted else if (over) c.error else c.ready
    val approveLabel = if (jobs.isEmpty()) "Select a job to approve" else if (over) "Over budget by ${total - model.budgetCredits} cr" else "Approve ${jobs.size} jobs · $total cr"
    val scale = presentation.textScale.toFloat()
    @Composable fun Label(text: String, id: String, size: Int = 14, weight: FontWeight = FontWeight.Normal, color: Color = c.text, mod: Modifier = Modifier) {
        Text(text, modifier = mod.testTag(id), fontSize = (size * scale).sp, lineHeight = (size * scale * 1.35f).sp, fontWeight = weight, fontFamily = FontFamily.SansSerif, color = color, softWrap = true)
    }
    CompositionLocalProvider(LocalLayoutDirection provides if (presentation.isRTL) LayoutDirection.Rtl else LayoutDirection.Ltr) {
        Column(modifier.fillMaxWidth().testTag("printbatch.card").semantics { testTagsAsResourceId = true }.clip(RoundedCornerShape(16.dp)).background(c.surface).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.Top) {
                Label("Print budget check", "printbatch.title", 20, FontWeight.SemiBold, mod = Modifier.weight(1f))
                Label(status, "printbatch.status", 12, FontWeight.SemiBold, statusColor, Modifier.clip(RoundedCornerShape(12.dp)).background(statusColor.copy(alpha = .13f)).padding(horizontal = 10.dp, vertical = 5.dp).widthIn(max = 105.dp))
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Label("Estimated charge", "printbatch.charge.caption", 12, color = c.muted)
                Label("$total cr", "printbatch.charge.value", 28, FontWeight.Bold)
                Label("${jobs.size} jobs • $pageCount pages • $sheetCount sheets", "printbatch.summary", 12, color = c.muted)
            }
            Column {
                model.jobs.forEachIndexed { index, job ->
                    val checked = job.id in selected
                    Row(Modifier.fillMaxWidth().padding(vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(48.dp).testTag("printbatch.job.${job.id}.toggle").toggleable(checked, enabled = !job.locked, role = Role.Checkbox) {
                            val next = if (checked) selected - job.id else selected + job.id
                            selected = next
                            onEvent("selectionChanged", mapOf("jobIDs" to model.jobs.filter { it.id in next }.map { it.id }))
                        }.semantics { contentDescription = "${if (checked) "Deselect" else "Select"} ${job.title}" }, contentAlignment = Alignment.Center) {
                            Box(Modifier.size(20.dp).clip(RoundedCornerShape(4.dp)).background(if (checked) c.accent.copy(alpha = if (job.locked) .45f else 1f) else c.surface).border(1.dp, if (checked) Color.Transparent else c.muted, RoundedCornerShape(4.dp))) {
                                if (checked) Canvas(Modifier.fillMaxSize()) {
                                    drawLine(c.onAccent, Offset(size.width * .2f, size.height * .52f), Offset(size.width * .43f, size.height * .74f), 2.dp.toPx(), StrokeCap.Round)
                                    drawLine(c.onAccent, Offset(size.width * .43f, size.height * .74f), Offset(size.width * .82f, size.height * .26f), 2.dp.toPx(), StrokeCap.Round)
                                }
                            }
                        }
                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Label(job.title, "printbatch.job.${job.id}.title", weight = FontWeight.SemiBold)
                            Label("${job.pages} pages × ${job.copies} copies • ${if (job.isColor) "Color" else "Mono"}${if (job.locked) " • Locked" else ""}", "printbatch.job.${job.id}.subtitle", 12, color = c.muted)
                        }
                        Label("${ink(job) + sheets(job)} cr", "printbatch.job.${job.id}.price")
                    }
                    if (index < model.jobs.lastIndex) HorizontalDivider(color = c.muted.copy(alpha = .25f))
                }
            }
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Label("Paper mode", "printbatch.mode.title", weight = FontWeight.SemiBold)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("single" to "Single-sided", "duplex" to "Duplex").forEach { (value, title) ->
                        val active = mode == value
                        Box(Modifier.weight(1f).heightIn(min = 48.dp).clip(RoundedCornerShape(10.dp)).background(if (active) c.accent else c.surface).border(1.dp, if (active) c.accent else c.muted.copy(alpha = .25f), RoundedCornerShape(10.dp)).testTag("printbatch.mode.$value").selectable(active, role = Role.Button) {
                            if (mode != value) { mode = value; onEvent("paperModeChanged", mapOf("paperMode" to value)) }
                        }.padding(8.dp), contentAlignment = Alignment.Center) {
                            Text(title, color = if (active) c.onAccent else c.text, fontSize = (14 * scale).sp, lineHeight = (19 * scale).sp, fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Priority handling", Modifier.weight(1f), color = if (model.allowPriority && jobs.isNotEmpty()) c.text else c.muted, fontSize = (14 * scale).sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.SansSerif)
                    Switch(checked = priority, onCheckedChange = { priority = it; onEvent("priorityChanged", mapOf("priority" to it)) }, enabled = model.allowPriority && jobs.isNotEmpty(), modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).testTag("printbatch.priority").semantics { contentDescription = "Priority handling" }, colors = SwitchDefaults.colors(checkedTrackColor = c.accent, checkedThumbColor = c.onAccent, uncheckedTrackColor = c.background, uncheckedBorderColor = c.muted, uncheckedThumbColor = c.muted, disabledCheckedTrackColor = c.muted.copy(alpha = .25f), disabledUncheckedTrackColor = c.muted.copy(alpha = .12f), disabledUncheckedThumbColor = c.muted))
                }
                Label(if (!model.allowPriority) "Priority unavailable for this batch." else if (priority) "Adds 6 cr to this batch." else "Add 6 cr for priority handling.", "printbatch.priority.helper", 12, color = c.muted)
            }
            TextButton(onClick = { expanded = !expanded; onEvent("breakdownChanged", mapOf("expanded" to expanded)) }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("printbatch.breakdown.toggle").semantics { stateDescription = if (expanded) "Expanded" else "Collapsed" }, contentPadding = PaddingValues(0.dp), colors = ButtonDefaults.textButtonColors(contentColor = c.accent)) {
                Text(if (expanded) "Hide cost breakdown" else "Show cost breakdown", Modifier.fillMaxWidth(), fontSize = (14 * scale).sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.SansSerif)
            }
            if (expanded) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    listOf(Triple("ink", "Ink", inkCost), Triple("paper", "Paper", sheetCount), Triple("priority", "Priority", surcharge), Triple("total", "Total", total)).forEach { (id, label, amount) ->
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Label(label, "printbatch.breakdown.$id.label", 12, color = c.muted, mod = Modifier.weight(1f))
                            Label("$amount cr", "printbatch.breakdown.$id.value", 12, color = c.muted)
                        }
                    }
                }
            }
            Label(if (jobs.isEmpty()) "No charge selected" else if (over) "Short by ${total - model.budgetCredits} cr" else "Balance after approval: ${model.budgetCredits - total} cr", "printbatch.balance", weight = FontWeight.SemiBold, color = if (over && jobs.isNotEmpty()) c.error else c.text)
            Button(onClick = { onEvent("approve", mapOf("modelID" to model.modelID, "jobIDs" to ids, "paperMode" to mode, "priority" to priority, "totalCredits" to total, "printedPages" to pageCount, "sheets" to sheetCount)) }, enabled = canApprove, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("printbatch.approve"), shape = RoundedCornerShape(10.dp), colors = ButtonDefaults.buttonColors(containerColor = c.accent, contentColor = c.onAccent, disabledContainerColor = c.muted.copy(alpha = .12f), disabledContentColor = c.muted), contentPadding = PaddingValues(horizontal = 12.dp, vertical = 12.dp)) {
                Text(approveLabel, fontSize = (14 * scale).sp, lineHeight = (19 * scale).sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.SansSerif)
            }
        }
    }
}
