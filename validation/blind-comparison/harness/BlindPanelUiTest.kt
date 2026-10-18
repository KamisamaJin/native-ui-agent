package com.example.reply

import android.view.View
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import app.cash.paparazzi.*
import com.android.resources.NightMode
import com.example.reply.ui.components.ReplyTransferPanel
import com.example.reply.ui.components.TransferItem
import com.example.reply.ui.theme.ContrastAwareReplyTheme
import java.io.File
import kotlinx.serialization.json.*
import org.junit.Rule
import org.junit.Test

class BlindPanelUiTest {
    private val output = File(requireNotNull(System.getenv("NATIVE_UI_OUTPUT")))
    private val fixture = Json.parseToJsonElement(File(requireNotNull(System.getenv("BENCH_FIXTURE"))).readText()).jsonObject
    private fun number(key: String, fallback: Float) = fixture[key]?.jsonPrimitive?.floatOrNull ?: fallback
    private fun flag(key: String) = fixture[key]?.jsonPrimitive?.booleanOrNull ?: false
    private fun nodes(node: SemanticsNode): List<SemanticsNode> = listOf(node) + node.children.flatMap { nodes(it) }
    private var rawNodes: List<SemanticsNode> = emptyList()
    private var exported: List<JsonObject> = emptyList()
    private val events = mutableListOf<String>()
    private var actualNightMask = -1
    private var actualDensity = 0f

    @get:Rule val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_5.copy(
            screenWidth = (number("width",390f) * 2.75f).toInt(),
            screenHeight = (number("height",620f) * 2.75f).toInt(),
            nightMode = if(flag("dark")) NightMode.NIGHT else NightMode.NOTNIGHT,
            fontScale = number("font_scale",1f), softButtons = false),
        showSystemUi = false,
        snapshotHandler = HtmlReportWriter(runName="capture",rootDirectory=File(output,"paparazzi-report")))

    @Test fun capture() {
        val items = fixture["items"]!!.jsonArray.map { entry ->
            val item = entry.jsonObject
            val value = item["progress"]!!.jsonPrimitive
            val progress = value.doubleOrNull ?: when(value.content.lowercase()) {
                "nan" -> Double.NaN; "infinity" -> Double.POSITIVE_INFINITY
                "-infinity" -> Double.NEGATIVE_INFINITY; else -> error("Bad fixture progress") }
            TransferItem(item["id"]!!.jsonPrimitive.content,item["name"]!!.jsonPrimitive.content,
                item["status"]!!.jsonPrimitive.content,progress)
        }
        val preview = object: View(paparazzi.context) { override fun isInEditMode()=true }
        paparazzi.snapshot(name="capture") {
            val root = LocalView.current as ViewRootForTest
            val density = LocalDensity.current.density
            actualDensity = density
            actualNightMask = LocalConfiguration.current.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK
            CompositionLocalProvider(LocalInspectionMode provides true, LocalView provides preview,
                LocalLayoutDirection provides if(flag("rtl")) LayoutDirection.Rtl else LayoutDirection.Ltr) {
                ContrastAwareReplyTheme(darkTheme=flag("dark"),dynamicColor=false) {
                    Box(Modifier.fillMaxSize().background(if(flag("dark")) Color(0xFF0C1424) else Color(0xFFEDF2F8))) {
                        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                            .padding(horizontal=16.dp).padding(top=24.dp,bottom=24.dp)
                            .onGloballyPositioned {
                                rawNodes = nodes(root.semanticsOwner.unmergedRootSemanticsNode)
                                exported = rawNodes.map { node ->
                                    val config=node.config
                                    val layouts=mutableListOf<TextLayoutResult>()
                                    config.getOrNull(SemanticsActions.GetTextLayoutResult)?.action?.invoke(layouts)
                                    buildJsonObject {
                                        put("node_id",node.id);put("parent_id",node.parent?.id ?: -1)
                                        put("tag",config.getOrNull(SemanticsProperties.TestTag) ?: "")
                                        put("text",config.getOrNull(SemanticsProperties.Text)?.joinToString { it.text } ?: "")
                                        put("content_description",config.getOrNull(SemanticsProperties.ContentDescription)?.joinToString() ?: "")
                                        put("state_description",config.getOrNull(SemanticsProperties.StateDescription) ?: "")
                                        put("role",config.getOrNull(SemanticsProperties.Role)?.toString() ?: "")
                                        put("clickable",config.getOrNull(SemanticsActions.OnClick)?.action != null)
                                        fun bounds(rect: androidx.compose.ui.geometry.Rect)=buildJsonArray {
                                            add(rect.left/density);add(rect.top/density);add(rect.right/density);add(rect.bottom/density)
                                        }
                                        put("bounds_dp",bounds(node.boundsInRoot));put("touch_bounds_dp",bounds(node.touchBoundsInRoot))
                                        config.getOrNull(SemanticsProperties.ProgressBarRangeInfo)?.let {
                                            if(it.current.isFinite()) put("progress",it.current)
                                            put("range_start",it.range.start);put("range_end",it.range.endInclusive)
                                        }
                                        layouts.firstOrNull()?.let { result ->
                                            if(result.layoutInput.style.fontSize.value.isFinite()) put("font_sp",result.layoutInput.style.fontSize.value)
                                            put("font_weight",result.layoutInput.style.fontWeight?.weight ?: -1)
                                            runCatching {result.layoutInput.style.color.toArgb().toLong() and 0xffffffffL}.getOrNull()?.let {put("color_argb",it)}
                                            put("lines",result.lineCount);put("overflow",result.hasVisualOverflow)
                                            put("ellipsized",(0 until result.lineCount).any { result.isLineEllipsized(it) })
                                        }
                                    }
                                }
                            }) {
                            ReplyTransferPanel(items,flag("expanded"),{events.add("toggle")},
                                { id -> events.add("retry:"+id) },Modifier.fillMaxWidth())
                        }
                    }
                }
            }
        }
        val actionTag=fixture["activate_id"]?.jsonPrimitive?.contentOrNull
        var activated=false
        if(actionTag!=null) {
            val target=rawNodes.firstOrNull { it.config.getOrNull(SemanticsProperties.TestTag)==actionTag }
            val descendant=target?.let { nodes(it).firstOrNull { node -> node.config.getOrNull(SemanticsActions.OnClick)?.action!=null } }
            val action=(descendant ?: target)?.config?.getOrNull(SemanticsActions.OnClick)?.action
            activated=action?.invoke() ?: false
        }
        File(output,"semantics.json").writeText(JsonArray(exported).toString())
        File(output,"native-report.json").writeText(buildJsonObject {
            put("native_test","BlindPanelUiTest.capture");put("nodes",exported.size)
            put("native_night_mode_mask",actualNightMask);put("density",actualDensity)
            put("font_scale",number("font_scale",1f));put("rtl",flag("rtl"));put("scroll_offset",0)
            put("activation_requested",actionTag ?: "");put("activation_executed",activated)
            put("events",buildJsonArray { events.forEach { add(it) } })
            put("action_method","native Compose accessibility OnClick action after layout; not physical touch")
            put("layout_scope","Real production component in scrollable preview host; Activity/window behavior excluded")
        }.toString())
    }
}
