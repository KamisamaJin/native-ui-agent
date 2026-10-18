package com.example.reply

import android.view.View
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.ViewRootForTest
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsNode
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.dp
import app.cash.paparazzi.DeviceConfig
import app.cash.paparazzi.HtmlReportWriter
import app.cash.paparazzi.Paparazzi
import com.example.reply.data.local.LocalEmailsDataProvider
import com.example.reply.ui.components.ReplyEmailListItem
import com.example.reply.ui.theme.ContrastAwareReplyTheme
import java.io.File
import kotlinx.serialization.json.*
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

/** Observes actual production text semantics/layout results; adds no production IDs. */
class ReplyFeatureUiTest {
    private val output = File(requireNotNull(System.getenv("NATIVE_UI_OUTPUT")))
    private val scenario = System.getenv("NATIVE_UI_SCENARIO") ?: "normal"
    private val measurements = mutableMapOf<String, JsonObject>()
    private var textEvidence: List<JsonObject> = emptyList()

    @get:Rule val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_5.copy(
            screenWidth = if (scenario == "narrow") 880 else 1080,
            screenHeight = 1400, softButtons = false),
        showSystemUi = false,
        snapshotHandler = HtmlReportWriter(runName = scenario,
            rootDirectory = File(output, "paparazzi-report")))

    private fun measured(key: String, value: Number, unit: String, method: String) {
        measurements[key] = buildJsonObject {
            put("value", value); put("unit", unit); put("method", method)
        }
    }

    private fun descendants(node: SemanticsNode): List<SemanticsNode> =
        listOf(node) + node.children.flatMap { descendants(it) }

    @Test fun captureAttachments() {
        val preview = object : View(paparazzi.context) { override fun isInEditMode() = true }
        val original = LocalEmailsDataProvider.allEmails.first { it.attachments.isNotEmpty() }
        val description = if (scenario == "long" || scenario == "narrow")
            "Bridge in Paris at sunset - original high resolution photograph from our summer trip with family"
            else "Bridge in Paris"
        val email = original.copy(
            body = "Here are some great shots from my trip. See the attachments below.",
            createdAt = "20 mins ago", threads = emptyList(),
            attachments = if (scenario == "empty") emptyList() else original.attachments.mapIndexed { i, value ->
                if (i == 0) value.copy(contentDesc = description) else value
            })
        paparazzi.snapshot(name = scenario) {
            val actualRoot = LocalView.current as ViewRootForTest
            val density = LocalDensity.current.density
            CompositionLocalProvider(LocalInspectionMode provides true, LocalView provides preview) {
                ContrastAwareReplyTheme(darkTheme = scenario == "dark", dynamicColor = false) {
                    Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(top = 24.dp)) {
                        ReplyEmailListItem(email, {}, {}, modifier = Modifier.onGloballyPositioned {
                            val nodes = descendants(actualRoot.semanticsOwner.unmergedRootSemanticsNode)
                                .filter { it.config.getOrNull(SemanticsProperties.Text) != null }
                            fun text(node: SemanticsNode) = node.config[SemanticsProperties.Text].joinToString { it.text }
                            textEvidence = nodes.map { node ->
                                val layouts = mutableListOf<TextLayoutResult>()
                                node.config.getOrNull(SemanticsActions.GetTextLayoutResult)?.action?.invoke(layouts)
                                buildJsonObject {
                                    put("text", text(node))
                                    put("bounds_dp", buildJsonArray {
                                        add(node.boundsInRoot.left / density); add(node.boundsInRoot.top / density)
                                        add(node.boundsInRoot.right / density); add(node.boundsInRoot.bottom / density)
                                    })
                                    layouts.firstOrNull()?.let { result ->
                                        put("font_sp", result.layoutInput.style.fontSize.value)
                                        put("color_argb", result.layoutInput.style.color.toArgb().toLong() and 0xffffffffL)
                                        put("lines", result.lineCount)
                                        put("ellipsized", result.isLineEllipsized(0))
                                    }
                                }
                            }
                            val count = nodes.firstOrNull { text(it) == "4 attachments" }
                            measured("summary_visible", if (count == null) 0 else 1, "boolean",
                                "Actual unmerged production Compose text semantics; no test tags")
                            if (count != null) {
                                val desc = nodes.first { text(it) == description }
                                val body = nodes.first { text(it) == email.body }
                                val layout = mutableListOf<TextLayoutResult>()
                                count.config[SemanticsActions.GetTextLayoutResult].action!!.invoke(layout)
                                val descLayout = mutableListOf<TextLayoutResult>()
                                desc.config[SemanticsActions.GetTextLayoutResult].action!!.invoke(descLayout)
                                val method = "Actual production SemanticsNode boundsInRoot / native Density"
                                measured("text_gap", (desc.boundsInRoot.top - count.boundsInRoot.bottom) / density, "dp", method)
                                measured("count_body_offset", (count.boundsInRoot.left - body.boundsInRoot.left) / density, "dp", method)
                                measured("body_count_gap", (count.boundsInRoot.top - body.boundsInRoot.bottom) / density, "dp", method)
                                measured("count_font", layout.first().layoutInput.style.fontSize.value, "sp", "Native TextLayoutResult.layoutInput.style.fontSize")
                                measured("description_font", descLayout.first().layoutInput.style.fontSize.value, "sp", "Native TextLayoutResult.layoutInput.style.fontSize")
                                measured("count_color", layout.first().layoutInput.style.color.toArgb().toLong() and 0xffffffffL, "ARGB", "Native TextLayoutResult.layoutInput.style.color.toArgb")
                                measured("count_ellipsized", if (layout.first().isLineEllipsized(0)) 1 else 0, "boolean", "Native TextLayoutResult.isLineEllipsized")
                                measured("description_ellipsized", if (descLayout.first().isLineEllipsized(0)) 1 else 0, "boolean", "Native TextLayoutResult.isLineEllipsized")
                            }
                        })
                    }
                }
            }
        }
        assertTrue("Native text tree must have been read", textEvidence.isNotEmpty())
        File(output, "measurements.json").writeText(JsonObject(measurements).toString())
        File(output, "semantics.json").writeText(JsonArray(textEvidence).toString())
        File(output, "native-test.json").writeText(buildJsonObject {
            put("executed_test", "ReplyFeatureUiTest.captureAttachments")
            put("scenario", scenario); put("production_component", "ReplyEmailListItem")
            put("inspection_mode", true); put("window_side_effects", "excluded; real Activity checked separately")
        }.toString())
    }
}
