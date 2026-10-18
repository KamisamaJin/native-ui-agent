package com.example.reply

import android.view.View
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import app.cash.paparazzi.DeviceConfig
import app.cash.paparazzi.HtmlReportWriter
import app.cash.paparazzi.Paparazzi
import com.example.reply.data.local.LocalEmailsDataProvider
import com.example.reply.ui.components.ReplyEmailListItem
import com.example.reply.ui.theme.ContrastAwareReplyTheme
import java.io.File
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

/** This fixture calls the upstream production component, theme, data and resources. */
class ReplyNativeUiTest {
    private val output = File(requireNotNull(System.getenv("NATIVE_UI_OUTPUT")))
    private val scenario = System.getenv("NATIVE_UI_SCENARIO") ?: "normal"
    private var cardWidthDp = 0f
    private var cardHeightDp = 0f

    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_5.copy(
            screenWidth = 1080,
            screenHeight = 1200,
            softButtons = false
        ),
        showSystemUi = false,
        snapshotHandler = HtmlReportWriter(
            runName = scenario,
            rootDirectory = File(output, "paparazzi-report")
        )
    )

    @Test
    fun captureEmailCard() {
        val previewView = object : View(paparazzi.context) {
            override fun isInEditMode() = true
        }
        val email = LocalEmailsDataProvider.allEmails.first().copy(
            subject = if (scenario == "long") {
                "Your order is ready: please review the delivery instructions before tomorrow"
            } else {
                "Package shipped!"
            },
            body = "Your package is on the way. Open the tracking page for the latest delivery details.",
            createdAt = "20 mins ago",
            threads = emptyList()
        )
        paparazzi.snapshot(name = scenario) {
            // The upstream theme guards Activity/window side effects in Preview.
            CompositionLocalProvider(
                LocalInspectionMode provides true,
                LocalView provides previewView
            ) {
            val density = LocalDensity.current
            ContrastAwareReplyTheme(darkTheme = scenario == "dark", dynamicColor = false) {
                Box(
                    Modifier.fillMaxSize()
                        .background(MaterialTheme.colorScheme.background)
                        .padding(top = 24.dp)
                ) {
                    ReplyEmailListItem(
                        email = email,
                        navigateToDetail = {},
                        toggleSelection = {},
                        modifier = Modifier.onGloballyPositioned { coordinates ->
                            cardWidthDp = with(density) { coordinates.size.width.toDp().value }
                            cardHeightDp = with(density) { coordinates.size.height.toDp().value }
                        }
                    )
                }
            }
            }
        }
        assertTrue("The production component must complete native layout", cardHeightDp > 0f)
        File(output, "measurements.json").writeText(
            """{"card_width":{"value":""" + cardWidthDp +
                ""","unit":"dp","method":"Production ReplyEmailListItem LayoutCoordinates.size via its existing modifier parameter"},"card_height":{"value":""" +
                cardHeightDp + ""","unit":"dp","method":"Production ReplyEmailListItem LayoutCoordinates.size via its existing modifier parameter"}}"""
        )
        File(output, "native-test.json").writeText(
            """{"executed_test":"ReplyNativeUiTest.captureEmailCard","snapshot_calls":1,"scenario":"$scenario","production_component":"com.example.reply.ui.components.ReplyEmailListItem","local_inspection_mode":true,"preview_view_edit_mode":true,"excluded_scope":"Activity/window side effects; verified separately on emulator"}"""
        )
    }
}
