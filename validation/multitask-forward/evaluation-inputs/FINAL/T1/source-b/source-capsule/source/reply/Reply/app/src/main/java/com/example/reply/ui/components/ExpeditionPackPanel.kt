package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

public data class ExpeditionPackItem(
    val id: String,
    val name: String,
    val grams: Int,
    val available: Boolean,
    val providesShelter: Boolean,
    val note: String,
)

public data class ExpeditionPackRequest(
    val id: String,
    val title: String,
    val context: String,
    val choiceWidth: Double,
    val notes: List<String>,
    val baseGrams: Int,
    val maxGrams: Int,
    val requiresShelter: Boolean,
    val coverGrams: Int,
    val selectedIDs: List<String>,
    val cover: Boolean,
    val items: List<ExpeditionPackItem>,
)

@Composable
public fun ExpeditionPackPanel(
    request: ExpeditionPackRequest,
    onConfirm: (String, List<String>, Boolean) -> Unit,
) {
    val seed = remember(request.id) {
        request.selectedIDs.toSet().intersect(request.items.filter { it.available }.map { it.id }.toSet())
    }
    var selectedIDs by remember(request.id) { mutableStateOf(seed) }
    var cover by remember(request.id) { mutableStateOf(request.cover && seed.isNotEmpty()) }
    var expanded by remember(request.id) { mutableStateOf(false) }
    val palette = PackPalette(dark = MaterialTheme.colorScheme.background.luminance() < 0.5f)
    val selectedItems = request.items.filter { it.id in selectedIDs }
    val totalGrams = request.baseGrams + selectedItems.sumOf { it.grams } + if (cover) request.coverGrams else 0
    val coverEnabled = selectedItems.isNotEmpty() && (cover || totalGrams + request.coverGrams <= request.maxGrams)
    val ready = selectedItems.isNotEmpty() && totalGrams <= request.maxGrams &&
        (!request.requiresShelter || selectedItems.any { it.providesShelter })
    val status = when {
        totalGrams > request.maxGrams -> "Capacity exceeded"
        selectedItems.isEmpty() -> "Choose shared equipment"
        request.requiresShelter && selectedItems.none { it.providesShelter } -> "Shelter required"
        else -> "Ready for departure"
    }
    val summary = "${selectedItems.size} ${if (selectedItems.size == 1) "item" else "items"} • $totalGrams g / ${request.maxGrams} g"
    val shape = RoundedCornerShape(12.dp)

    Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            PackText(request.title, 22, FontWeight.Bold, palette.ink, Modifier.testTag("pack.title"))
            PackText(request.context, 14, FontWeight.Normal, palette.muted, Modifier.testTag("pack.context"))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            request.items.take(2).forEachIndexed { index, item ->
                val selected = item.id in selectedIDs
                val enabled = selected || (item.available && totalGrams + item.grams <= request.maxGrams)
                Column(
                    modifier = Modifier
                        .width(request.choiceWidth.dp)
                        .heightIn(min = 90.dp)
                        .testTag(if (index == 0) "pack.choiceA" else "pack.choiceB")
                        .clip(shape)
                        .background(if (enabled) palette.surface else palette.border)
                        .border(1.dp, if (selected) palette.accent else palette.border, shape)
                        .selectable(selected = selected, enabled = enabled, role = Role.Checkbox) {
                            if (selected) {
                                val remaining = selectedIDs - item.id
                                selectedIDs = remaining
                                if (remaining.isEmpty()) cover = false
                            } else if (enabled) {
                                selectedIDs = selectedIDs + item.id
                            }
                        }
                        .padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    PackText(item.name + if (selected) " ✓" else "", 16, FontWeight.SemiBold, if (enabled) palette.ink else palette.muted)
                    PackText(item.note, 14, FontWeight.Normal, palette.muted)
                }
            }
        }
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp)
                .testTag("pack.extra")
                .clip(shape)
                .background(if (coverEnabled) palette.surface else palette.border)
                .border(1.dp, if (cover) palette.accent else palette.border, shape)
                .selectable(selected = cover, enabled = coverEnabled, role = Role.Checkbox) {
                    if (coverEnabled) cover = !cover
                }
                .padding(12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                PackText("Weather cover", 16, FontWeight.SemiBold, if (coverEnabled) palette.ink else palette.muted, Modifier.weight(1f))
                if (cover) PackText("✓", 16, FontWeight.SemiBold, palette.accent, Modifier.clearAndSetSemantics {})
            }
        }
        PackText(summary, 18, FontWeight.SemiBold, palette.ink, Modifier.testTag("pack.summary"))
        PackText(status, 14, FontWeight.Normal, palette.accent, Modifier.testTag("pack.status"))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp)
                .testTag("pack.disclosure")
                .clip(shape)
                .background(palette.surface)
                .border(1.dp, palette.border, shape)
                .clickable(role = Role.Button) { expanded = !expanded }
                .padding(12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            PackText(if (expanded) "Hide details" else "Show details", 16, FontWeight.SemiBold, palette.ink)
        }
        if (expanded) {
            PackText(
                if (request.requiresShelter) "Shelter needed for this route." else "Day route: no shelter required.",
                14, FontWeight.Normal, palette.muted, Modifier.testTag("pack.detail"),
            )
        }
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .testTag("pack.primary")
                .clip(shape)
                .background(if (ready) palette.accent else palette.border)
                .clickable(enabled = ready, role = Role.Button) {
                    if (ready) onConfirm(request.id, selectedIDs.sorted(), cover)
                }
                .padding(horizontal = 12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            PackText("Confirm pack", 16, FontWeight.SemiBold, if (ready) palette.primaryInk else palette.muted)
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            PackText("Before departure", 16, FontWeight.SemiBold, palette.ink, Modifier.testTag("pack.notes"))
            request.notes.forEach { paragraph ->
                PackText(paragraph, 14, FontWeight.Normal, palette.muted)
            }
        }
    }
}

@Composable
private fun PackText(
    text: String,
    size: Int,
    weight: FontWeight,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Text(
        text = text,
        modifier = modifier,
        color = color,
        softWrap = true,
        style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = size.sp, fontWeight = weight),
    )
}

private class PackPalette(dark: Boolean) {
    val surface = Color(if (dark) 0xFF16231C else 0xFFF4F7F3)
    val ink = Color(if (dark) 0xFFE9F2EC else 0xFF18251F)
    val muted = Color(if (dark) 0xFFB7C7BD else 0xFF53645B)
    val accent = Color(if (dark) 0xFF94D6AC else 0xFF276145)
    val border = Color(if (dark) 0xFF456251 else 0xFFC9D7CC)
    val primaryInk = Color(if (dark) 0xFF101A14 else 0xFFFFFFFF)
}
