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
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.floor
import kotlin.math.max

/** A caller-owned attachment transfer. Status, rather than progress, is authoritative. */
data class TransferItem(
    val id: String,
    val name: String,
    val status: String,
    val progress: Double,
)

private data class TransferPalette(val panel: Color, val border: Color, val primary: Color,
    val secondary: Color, val surface: Color, val track: Color, val accent: Color,
    val error: Color, val success: Color)

@Composable
private fun transferPalette() = if (isSystemInDarkTheme()) TransferPalette(
    Color(0xFF182235), Color(0xFF34445F), Color(0xFFF2F5FB), Color(0xFFB9C5D9),
    Color(0xFF24324A), Color(0xFF34445F), Color(0xFF9DBDFF), Color(0xFFFFADB3), Color(0xFF7CDDBB)
) else TransferPalette(
    Color(0xFFFFFFFF), Color(0xFFD7DFEB), Color(0xFF17243B), Color(0xFF526279),
    Color(0xFFF1F4F9), Color(0xFFE2E8F2), Color(0xFF275DD8), Color(0xFFB3313B), Color(0xFF13795B)
)

private fun safeTransferProgress(value: Double) = if (value.isFinite()) value.coerceIn(0.0, 1.0) else 0.0
private fun transferPercent(value: Double) = "${floor(value * 100.0 + 0.5).toInt()}%"
private fun transferStyle(size: Int, weight: FontWeight = FontWeight.Normal) = TextStyle(
    fontFamily = FontFamily.SansSerif, fontSize = size.sp, fontWeight = weight,
    lineHeight = (size + 4).sp,
)

@Composable
fun ReplyTransferPanel(
    items: List<TransferItem>,
    expanded: Boolean,
    onToggle: () -> Unit,
    onRetry: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = transferPalette()
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
        items.isEmpty() -> colors.secondary
        failed > 0 -> colors.error
        running > 0 -> colors.accent
        queued > 0 -> colors.secondary
        else -> colors.success
    }
    val aggregate = if (items.isEmpty()) 0.0 else items.sumOf {
        when (it.status) { "done" -> 1.0; "queued" -> 0.0; else -> safeTransferProgress(it.progress) }
    } / items.size
    val visible = if (items.size > 2 && !expanded) items.take(2) else items
    val largeText = LocalDensity.current.fontScale >= 1.6f

    Box(modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        BoxWithConstraints(Modifier.widthIn(max = 560.dp).fillMaxWidth()) {
            val compact = maxWidth <= 340.dp || largeText
            Column(
                Modifier.fillMaxWidth().testTag("transfer.panel")
                    .clip(RoundedCornerShape(20.dp)).background(colors.panel)
                    .border(1.dp, colors.border, RoundedCornerShape(20.dp)).padding(16.dp)
            ) {
                if (compact) {
                    Text("Attachment transfers", Modifier.testTag("transfer.title"), colors.primary,
                        style = transferStyle(20, FontWeight.SemiBold))
                    if (items.size > 2) TransferToggle(expanded, onToggle, colors)
                } else {
                    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Attachment transfers", Modifier.weight(1f).testTag("transfer.title"), colors.primary,
                            style = transferStyle(20, FontWeight.SemiBold))
                        if (items.size > 2) TransferToggle(expanded, onToggle, colors)
                    }
                }
                Spacer(Modifier.height(4.dp))
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.size(8.dp).background(tone, RoundedCornerShape(4.dp)))
                    Text(summary, Modifier.testTag("transfer.summary"), tone,
                        style = transferStyle(14, FontWeight.SemiBold))
                }
                Spacer(Modifier.height(12.dp))
                if (items.isEmpty()) {
                    Text("Add an attachment to get started.", Modifier.testTag("transfer.empty"), colors.secondary,
                        style = transferStyle(13))
                } else {
                    TransferCount("$done of ${items.size} complete", transferPercent(aggregate), colors)
                    Spacer(Modifier.height(6.dp))
                    TransferBar(aggregate, tone, colors.track, 6, "Overall transfer progress", "transfer.progress")
                    Spacer(Modifier.height(16.dp))
                    Column(Modifier.fillMaxWidth().testTag("transfer.list")) {
                        visible.forEachIndexed { index, item ->
                            TransferRow(item, compact, largeText, colors, onRetry)
                            if (index < visible.lastIndex) Box(Modifier.fillMaxWidth().height(1.dp).background(colors.track))
                        }
                    }
                    if (items.size > 2 && !expanded) {
                        val count = items.size - 2
                        Spacer(Modifier.height(8.dp))
                        Text(if (count == 1) "+1 more attachment" else "+$count more attachments",
                            Modifier.testTag("transfer.more"), colors.secondary, style = transferStyle(12))
                    }
                }
            }
        }
    }
}

@Composable
private fun TransferToggle(expanded: Boolean, onToggle: () -> Unit, colors: TransferPalette) {
    TextButton(onClick = onToggle,
        modifier = Modifier.heightIn(min = 48.dp).widthIn(min = 48.dp).testTag("transfer.toggle").semantics {
            contentDescription = if (expanded) "Show fewer attachments" else "Show all attachments"
            stateDescription = if (expanded) "Expanded" else "Collapsed"
        }, contentPadding = PaddingValues(0.dp),
        colors = ButtonDefaults.textButtonColors(contentColor = colors.accent)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(if (expanded) "Show less" else "Show all", Modifier.weight(1f, fill = false),
                style = transferStyle(14, FontWeight.SemiBold))
            Canvas(Modifier.size(12.dp)) {
                val path = Path().apply {
                    moveTo(size.width * .2f, size.height * if (expanded) .65f else .35f)
                    lineTo(size.width * .5f, size.height * if (expanded) .35f else .65f)
                    lineTo(size.width * .8f, size.height * if (expanded) .65f else .35f)
                }
                drawPath(path, colors.accent, style = Stroke(1.6.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round))
            }
        }
    }
}

@Composable
private fun TransferCount(count: String, percent: String, colors: TransferPalette) {
    Layout(modifier = Modifier.fillMaxWidth(), content = {
        Text(count, Modifier.testTag("transfer.count"), colors.secondary, style = transferStyle(13))
        Text(percent, Modifier.testTag("transfer.percent"), colors.primary, style = transferStyle(13, FontWeight.SemiBold))
    }) { measurables, constraints ->
        val countPlaceable = measurables[0].measure(constraints.copy(minWidth = 0, minHeight = 0))
        val percentPlaceable = measurables[1].measure(constraints.copy(minWidth = 0, minHeight = 0))
        val together = countPlaceable.width + 8.dp.roundToPx() + percentPlaceable.width <= constraints.maxWidth
        val height = if (together) max(countPlaceable.height, percentPlaceable.height)
            else countPlaceable.height + 4.dp.roundToPx() + percentPlaceable.height
        layout(constraints.maxWidth, height) {
            countPlaceable.placeRelative(0, 0)
            percentPlaceable.placeRelative(constraints.maxWidth - percentPlaceable.width,
                if (together) 0 else countPlaceable.height + 4.dp.roundToPx())
        }
    }
}

@Composable
private fun TransferRow(item: TransferItem, compact: Boolean, largeText: Boolean,
    colors: TransferPalette, onRetry: (String) -> Unit) {
    val progress = safeTransferProgress(item.progress)
    val tone = when (item.status) {
        "done" -> colors.success; "running" -> colors.accent; "failed" -> colors.error; else -> colors.secondary
    }
    val status = when (item.status) {
        "done" -> "Complete"; "running" -> "${transferPercent(progress)} sent"
        "failed" -> "Failed · retry available"; else -> "Waiting"
    }
    Row(Modifier.fillMaxWidth().testTag("transfer.row.${item.id}").padding(vertical = 12.dp),
        verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        TransferDocument(tone, colors.surface)
        Column(Modifier.weight(1f)) {
            Text(item.name, Modifier.fillMaxWidth().testTag("transfer.name.${item.id}")
                .semantics { contentDescription = item.name }, colors.primary,
                style = transferStyle(16, FontWeight.Medium), maxLines = if (largeText) 3 else 2,
                overflow = TextOverflow.Ellipsis)
            Spacer(Modifier.height(4.dp))
            Text(status, Modifier.testTag("transfer.status.${item.id}"), tone, style = transferStyle(13))
            if (item.status == "running") {
                Spacer(Modifier.height(8.dp))
                TransferBar(progress, tone, colors.track, 4, "${item.name} transfer progress", "transfer.progress.${item.id}")
            }
            if (compact && item.status == "failed") {
                Spacer(Modifier.height(8.dp))
                TransferRetry(item, colors, onRetry)
            }
        }
        if (!compact && item.status == "failed") TransferRetry(item, colors, onRetry)
    }
}

@Composable
private fun TransferRetry(item: TransferItem, colors: TransferPalette, onRetry: (String) -> Unit) {
    OutlinedButton(onClick = { onRetry(item.id) },
        modifier = Modifier.widthIn(min = 72.dp).heightIn(min = 48.dp).testTag("transfer.retry.${item.id}")
            .semantics { contentDescription = "Retry ${item.name}" },
        shape = RoundedCornerShape(10.dp), border = androidx.compose.foundation.BorderStroke(1.dp, colors.error),
        colors = ButtonDefaults.outlinedButtonColors(containerColor = colors.panel, contentColor = colors.error),
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp)) {
        Text("Retry", style = transferStyle(14, FontWeight.SemiBold))
    }
}

@Composable
private fun TransferBar(value: Double, tone: Color, track: Color, height: Int, label: String, tag: String) {
    Canvas(Modifier.fillMaxWidth().height(height.dp).testTag(tag).semantics {
        contentDescription = label
        stateDescription = transferPercent(value)
        progressBarRangeInfo = ProgressBarRangeInfo(value.toFloat(), 0f..1f)
    }) {
        val radius = CornerRadius(size.height / 2)
        drawRoundRect(track, cornerRadius = radius)
        if (value > 0.0) {
            val width = size.width * value.toFloat()
            drawRoundRect(tone, Offset(if (layoutDirection == LayoutDirection.Rtl) size.width - width else 0f, 0f),
                Size(width, size.height), radius)
        }
    }
}

@Composable
private fun TransferDocument(tone: Color, surface: Color) {
    Box(Modifier.size(32.dp).background(surface, RoundedCornerShape(8.dp)), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(22.dp)) {
            val scale = size.width / 22f
            val path = Path().apply {
                moveTo(5f * scale, 1f * scale); lineTo(12f * scale, 1f * scale)
                lineTo(18f * scale, 7f * scale); lineTo(18f * scale, 21f * scale)
                lineTo(5f * scale, 21f * scale); close()
                moveTo(12f * scale, 1f * scale); lineTo(12f * scale, 7f * scale); lineTo(18f * scale, 7f * scale)
                moveTo(8f * scale, 12f * scale); lineTo(15f * scale, 12f * scale)
                moveTo(8f * scale, 16f * scale); lineTo(14f * scale, 16f * scale)
            }
            drawPath(path, tone, style = Stroke(1.5.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round))
        }
    }
}
