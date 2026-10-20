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
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

data class ExpeditionPackItem(
    val id: String,
    val name: String,
    val grams: Int,
    val available: Boolean,
    val providesShelter: Boolean,
    val note: String,
)

data class ExpeditionPackRequest(
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

private fun ExpeditionPackRequest.seedSelection(): Set<String> {
    val available = items.filter { it.available }.map { it.id }.toSet()
    return selectedIDs.filter { it in available }.toSet()
}

@Composable
fun ExpeditionPackPanel(
    request: ExpeditionPackRequest,
    onConfirm: (String, List<String>, Boolean) -> Unit,
) {
    var selectedIDs by remember(request.id) { mutableStateOf(request.seedSelection()) }
    var cover by remember(request.id) {
        mutableStateOf(request.cover && request.seedSelection().isNotEmpty())
    }
    var detailsExpanded by remember(request.id) { mutableStateOf(false) }
    val selectedItems = request.items.filter { it.id in selectedIDs }
    val totalGrams = request.baseGrams + selectedItems.sumOf { it.grams } +
        if (cover) request.coverGrams else 0
    val canConfirm = selectedIDs.isNotEmpty() && totalGrams <= request.maxGrams &&
        (!request.requiresShelter || selectedItems.any { it.providesShelter })
    val canChangeCover = selectedIDs.isNotEmpty() &&
        (cover || totalGrams + request.coverGrams <= request.maxGrams)
    val status = when {
        totalGrams > request.maxGrams -> "Capacity exceeded"
        selectedIDs.isEmpty() -> "Choose shared equipment"
        request.requiresShelter && selectedItems.none { it.providesShelter } -> "Shelter required"
        else -> "Ready for departure"
    }
    val palette = packPalette(MaterialTheme.colorScheme.background.luminance() < 0.5f)
    val shape = RoundedCornerShape(12.dp)

    Column(
        modifier = Modifier.fillMaxWidth().background(palette.canvas),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            PackText(request.title, 22, FontWeight.Bold, palette.ink, Modifier.testTag("pack.title"))
            PackText(request.context, 14, FontWeight.Normal, palette.muted, Modifier.testTag("pack.context"))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            request.items.forEachIndexed { index, item ->
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
                            if (item.id in selectedIDs) {
                                selectedIDs = selectedIDs - item.id
                                if (selectedIDs.isEmpty()) cover = false
                            } else if (item.available && totalGrams + item.grams <= request.maxGrams) {
                                selectedIDs = selectedIDs + item.id
                            }
                        }
                        .padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.Top) {
                        PackText(
                            item.name, 16, FontWeight.SemiBold,
                            if (enabled) palette.ink else palette.muted,
                            Modifier.weight(1f),
                        )
                        if (selected) {
                            PackText("✓", 14, FontWeight.SemiBold, palette.accent, Modifier.clearAndSetSemantics {})
                        }
                    }
                    PackText(item.note, 14, FontWeight.Normal, palette.muted)
                }
            }
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp)
                .testTag("pack.extra")
                .clip(shape)
                .background(if (canChangeCover) palette.surface else palette.border)
                .border(1.dp, if (cover) palette.accent else palette.border, shape)
                .selectable(selected = cover, enabled = canChangeCover, role = Role.Checkbox) {
                    if (canChangeCover) cover = !cover
                }
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            PackText(
                "Weather cover", 16, FontWeight.SemiBold,
                if (canChangeCover) palette.ink else palette.muted, Modifier.weight(1f),
            )
            if (cover) {
                PackText("✓", 16, FontWeight.SemiBold, palette.accent, Modifier.clearAndSetSemantics {})
            }
        }
        PackText(
            "${selectedIDs.size} ${if (selectedIDs.size == 1) "item" else "items"} • $totalGrams g / ${request.maxGrams} g",
            18, FontWeight.SemiBold, palette.ink,
            Modifier.fillMaxWidth().testTag("pack.summary"),
        )
        PackText(status, 14, FontWeight.Normal, palette.accent, Modifier.testTag("pack.status"))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp)
                .testTag("pack.disclosure")
                .clip(shape)
                .background(palette.surface)
                .border(1.dp, palette.border, shape)
                .clickable(role = Role.Button) { detailsExpanded = !detailsExpanded }
                .padding(12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            PackText(if (detailsExpanded) "Hide details" else "Show details", 16, FontWeight.SemiBold, palette.ink)
        }
        if (detailsExpanded) {
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
                .background(if (canConfirm) palette.accent else palette.border)
                .clickable(enabled = canConfirm, role = Role.Button) {
                    if (canConfirm) onConfirm(request.id, selectedIDs.sorted(), cover)
                }
                .padding(horizontal = 12.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            PackText("Confirm pack", 16, FontWeight.SemiBold, if (canConfirm) palette.primaryInk else palette.muted)
        }
        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            PackText(
                "Before departure", 16, FontWeight.SemiBold, palette.ink,
                Modifier.testTag("pack.notes").semantics { heading() },
            )
            request.notes.forEach { note -> PackText(note, 14, FontWeight.Normal, palette.muted) }
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
        style = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = size.sp, fontWeight = weight, color = color),
        softWrap = true,
    )
}

private data class PackPalette(
    val canvas: Color,
    val surface: Color,
    val ink: Color,
    val muted: Color,
    val accent: Color,
    val border: Color,
    val primaryInk: Color,
)

private fun packPalette(dark: Boolean) = if (dark) {
    PackPalette(Color(0xFF101A14), Color(0xFF16231C), Color(0xFFE9F2EC), Color(0xFFB7C7BD), Color(0xFF94D6AC), Color(0xFF456251), Color(0xFF101A14))
} else {
    PackPalette(Color(0xFFFFFFFF), Color(0xFFF4F7F3), Color(0xFF18251F), Color(0xFF53645B), Color(0xFF276145), Color(0xFFC9D7CC), Color(0xFFFFFFFF))
}
