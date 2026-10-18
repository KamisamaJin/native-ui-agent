package com.example.reply.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.floor
import kotlin.math.max

/** Caller-owned transfer data; status remains authoritative over progress. */
data class TransferItem(
    val id: String,
    val name: String,
    val status: String,
    val progress: Double,
)

private data class TransferPalette(
    val panel: Color, val border: Color, val primary: Color,
    val neutral: Color, val surface: Color, val track: Color,
    val accent: Color, val error: Color, val success: Color,
)

private fun transferPalette(dark: Boolean) = if (dark) TransferPalette(
    Color(0xFF182235), Color(0xFF34445F), Color(0xFFF2F5FB),
    Color(0xFFB9C5D9), Color(0xFF24324A), Color(0xFF34445F),
    Color(0xFF9DBDFF), Color(0xFFFFADB3), Color(0xFF7CDDBB),
) else TransferPalette(
    Color(0xFFFFFFFF), Color(0xFFD7DFEB), Color(0xFF17243B),
    Color(0xFF526279), Color(0xFFF1F4F9), Color(0xFFE2E8F2),
    Color(0xFF275DD8), Color(0xFFB3313B), Color(0xFF13795B),
)

private fun safeTransferProgress(value: Double): Double =
    if (value.isFinite()) value.coerceIn(0.0, 1.0) else 0.0

private fun transferPercent(value: Double) = "${floor(value * 100.0 + 0.5).toInt()}%"

@Composable
fun ReplyTransferPanel(
    items: List<TransferItem>,
    expanded: Boolean,
    onToggle: () -> Unit,
    onRetry: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val palette = transferPalette(isSystemInDarkTheme())
    val failed = items.count { it.status == "failed" }
    val running = items.count { it.status == "running" }
    val queued = items.count { it.status == "queued" }
    val done = items.count { it.status == "done" }
    val summary = when {
        items.isEmpty() -> "No transfers"
        failed == 1 -> "1 needs retry"
        failed > 1 -> "$failed need retry"
        running > 0 -> "$running transferring"
        queued > 0 -> "$queued waiting"
        else -> "All transfers complete"
    }
    val tone = when {
        items.isEmpty() -> palette.neutral
        failed > 0 -> palette.error
        running > 0 -> palette.accent
        queued > 0 -> palette.neutral
        else -> palette.success
    }
    val aggregate = if (items.isEmpty()) 0.0 else items.sumOf {
        when (it.status) {
            "queued" -> 0.0
            "done" -> 1.0
            else -> safeTransferProgress(it.progress)
        }
    } / items.size
    val fontScale = LocalDensity.current.fontScale
    val visibleItems = if (items.size > 2 && !expanded) items.take(2) else items

    Box(modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        BoxWithConstraints(Modifier.widthIn(max = 560.dp).fillMaxWidth()) {
            val compact = maxWidth <= 340.dp || fontScale >= 1.6f
            Column(
                Modifier.fillMaxWidth()
                    .clip(RoundedCornerShape(20.dp))
                    .background(palette.panel)
                    .border(1.dp, palette.border, RoundedCornerShape(20.dp))
                    .testTag("transfer.panel")
                    .padding(16.dp),
            ) {
                if (compact) {
                    Box(Modifier.heightIn(min = 48.dp), contentAlignment = Alignment.CenterStart) {
                        TransferTitle(palette)
                    }
                    if (items.size > 2) TransferToggle(expanded, onToggle, palette)
                } else {
                    Row(
                        Modifier.fillMaxWidth().heightIn(min = 48.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Box(Modifier.weight(1f)) { TransferTitle(palette) }
                        if (items.size > 2) TransferToggle(expanded, onToggle, palette)
                    }
                }
                Spacer(Modifier.height(4.dp))
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.size(8.dp).clip(RoundedCornerShape(50)).background(tone).clearAndSetSemantics {})
                    Text(summary, color = tone, fontSize = 14.sp, lineHeight = 18.sp,
                        fontWeight = FontWeight.SemiBold, modifier = Modifier.testTag("transfer.summary"))
                }
                if (items.isEmpty()) {
                    Spacer(Modifier.height(12.dp))
                    Text("Add an attachment to get started.", color = palette.neutral,
                        fontSize = 13.sp, lineHeight = 17.sp, modifier = Modifier.testTag("transfer.empty"))
                } else {
                    Spacer(Modifier.height(12.dp))
                    TransferCount(done, items.size, aggregate, palette)
                    Spacer(Modifier.height(6.dp))
                    TransferBar(aggregate, tone, palette.track, 6,
                        "Overall transfer progress", "transfer.progress")
                    Spacer(Modifier.height(16.dp))
                    Column(Modifier.fillMaxWidth().testTag("transfer.list")) {
                        visibleItems.forEachIndexed { index, item ->
                            TransferFileRow(item, compact, fontScale >= 1.6f, palette, onRetry)
                            if (index < visibleItems.lastIndex) {
                                Box(Modifier.fillMaxWidth().height(1.dp).background(palette.track))
                            }
                        }
                    }
                    if (items.size > 2 && !expanded) {
                        Spacer(Modifier.height(8.dp))
                        val extra = items.size - 2
                        Text("+$extra more ${if (extra == 1) "attachment" else "attachments"}",
                            color = palette.neutral, fontSize = 12.sp, lineHeight = 16.sp,
                            modifier = Modifier.testTag("transfer.more"))
                    }
                }
            }
        }
    }
}

@Composable
private fun TransferTitle(palette: TransferPalette) {
    Text("Attachment transfers", color = palette.primary, fontSize = 20.sp,
        lineHeight = 25.sp, fontWeight = FontWeight.SemiBold,
        modifier = Modifier.testTag("transfer.title"))
}

@Composable
private fun TransferToggle(expanded: Boolean, onToggle: () -> Unit, palette: TransferPalette) {
    TextButton(
        onClick = onToggle,
        modifier = Modifier.heightIn(min = 48.dp).semantics {
            contentDescription = if (expanded) "Show fewer attachments" else "Show all attachments"
            stateDescription = if (expanded) "Expanded" else "Collapsed"
        }.testTag("transfer.toggle"),
        colors = ButtonDefaults.textButtonColors(contentColor = palette.accent),
        contentPadding = PaddingValues(horizontal = 0.dp, vertical = 8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(if (expanded) "Show less" else "Show all", fontSize = 14.sp,
                lineHeight = 18.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f, fill = false))
            Canvas(Modifier.size(12.dp).clearAndSetSemantics {}) {
                val path = Path().apply {
                    moveTo(size.width * .15f, size.height * if (expanded) .65f else .35f)
                    lineTo(size.width * .5f, size.height * if (expanded) .3f else .7f)
                    lineTo(size.width * .85f, size.height * if (expanded) .65f else .35f)
                }
                drawPath(path, palette.accent, style = Stroke(1.6.dp.toPx(), cap = StrokeCap.Round))
            }
        }
    }
}

@Composable
private fun TransferCount(done: Int, total: Int, fraction: Double, palette: TransferPalette) {
    Layout(content = {
        Text("$done of $total complete", color = palette.neutral, fontSize = 13.sp,
            lineHeight = 17.sp, modifier = Modifier.testTag("transfer.count"))
        Text(transferPercent(fraction), color = palette.primary, fontSize = 13.sp,
            lineHeight = 17.sp, fontWeight = FontWeight.SemiBold,
            modifier = Modifier.testTag("transfer.percent"))
    }, modifier = Modifier.fillMaxWidth()) { measurables, constraints ->
        val loose = constraints.copy(minWidth = 0, minHeight = 0)
        val count = measurables[0].measure(loose)
        val percent = measurables[1].measure(loose)
        val width = constraints.maxWidth
        val inline = count.width + 12.dp.roundToPx() + percent.width <= width
        val gap = 4.dp.roundToPx()
        val height = if (inline) max(count.height, percent.height) else count.height + gap + percent.height
        layout(width, height) {
            count.placeRelative(0, 0)
            percent.placeRelative(width - percent.width, if (inline) 0 else count.height + gap)
        }
    }
}

@Composable
private fun TransferFileRow(
    item: TransferItem, compact: Boolean, largeText: Boolean,
    palette: TransferPalette, onRetry: (String) -> Unit,
) {
    val progress = safeTransferProgress(item.progress)
    val tone = when (item.status) {
        "running" -> palette.accent
        "failed" -> palette.error
        "done" -> palette.success
        else -> palette.neutral
    }
    val status = when (item.status) {
        "running" -> "${transferPercent(progress)} sent"
        "failed" -> "Failed · retry available"
        "done" -> "Complete"
        else -> "Waiting"
    }
    Row(
        Modifier.fillMaxWidth().testTag("transfer.row.${item.id}").padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Box(Modifier.size(32.dp).clip(RoundedCornerShape(8.dp)).background(palette.surface)
            .clearAndSetSemantics {}, contentAlignment = Alignment.Center) {
            Canvas(Modifier.size(22.dp, 24.dp)) {
                val path = Path().apply {
                    moveTo(size.width * .2f, size.height * .08f)
                    lineTo(size.width * .61f, size.height * .08f)
                    lineTo(size.width * .84f, size.height * .3f)
                    lineTo(size.width * .84f, size.height * .94f)
                    lineTo(size.width * .2f, size.height * .94f)
                    close()
                    moveTo(size.width * .61f, size.height * .08f)
                    lineTo(size.width * .61f, size.height * .3f)
                    lineTo(size.width * .84f, size.height * .3f)
                }
                drawPath(path, tone, style = Stroke(1.5.dp.toPx()))
                drawLine(tone, Offset(size.width * .33f, size.height * .52f),
                    Offset(size.width * .7f, size.height * .52f), 1.5.dp.toPx())
                drawLine(tone, Offset(size.width * .33f, size.height * .72f),
                    Offset(size.width * .67f, size.height * .72f), 1.5.dp.toPx())
            }
        }
        Column(Modifier.weight(1f)) {
            Text(item.name, color = palette.primary, fontSize = 16.sp, lineHeight = 20.sp,
                fontWeight = FontWeight.Medium, maxLines = if (largeText) 3 else 2,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.testTag("transfer.name.${item.id}").semantics { contentDescription = item.name })
            Spacer(Modifier.height(4.dp))
            Text(status, color = tone, fontSize = 13.sp, lineHeight = 17.sp,
                modifier = Modifier.testTag("transfer.status.${item.id}"))
            if (item.status == "running") {
                Spacer(Modifier.height(8.dp))
                TransferBar(progress, tone, palette.track, 4,
                    "${item.name} transfer progress", "transfer.progress.${item.id}")
            }
            if (item.status == "failed" && compact) {
                Spacer(Modifier.height(8.dp))
                TransferRetry(item, palette, onRetry)
            }
        }
        if (item.status == "failed" && !compact) {
            Box(Modifier.align(Alignment.CenterVertically)) { TransferRetry(item, palette, onRetry) }
        }
    }
}

@Composable
private fun TransferRetry(item: TransferItem, palette: TransferPalette, onRetry: (String) -> Unit) {
    OutlinedButton(
        onClick = { onRetry(item.id) },
        modifier = Modifier.defaultMinSize(minWidth = 72.dp, minHeight = 48.dp)
            .testTag("transfer.retry.${item.id}").semantics { contentDescription = "Retry ${item.name}" },
        shape = RoundedCornerShape(10.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, palette.error),
        colors = ButtonDefaults.outlinedButtonColors(containerColor = palette.panel, contentColor = palette.error),
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp),
    ) {
        Text("Retry", fontSize = 14.sp, lineHeight = 18.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun TransferBar(
    fraction: Double, fill: Color, track: Color, height: Int, label: String, tag: String,
) {
    Box(Modifier.fillMaxWidth().height(height.dp).clip(RoundedCornerShape(50))
        .background(track).testTag(tag).semantics {
            contentDescription = label
            stateDescription = transferPercent(fraction)
            progressBarRangeInfo = ProgressBarRangeInfo(fraction.toFloat(), 0f..1f)
        }) {
        if (fraction > 0.0) Box(Modifier.align(Alignment.CenterStart)
            .fillMaxWidth(fraction.toFloat()).fillMaxHeight()
            .clip(RoundedCornerShape(50)).background(fill))
    }
}
