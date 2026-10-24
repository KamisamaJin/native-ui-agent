package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.*
import com.example.reply.ui.components.AudioTourChapter
import com.example.reply.ui.components.OfflineAudioTour
import com.example.reply.ui.components.OfflineAudioTourPanel

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val tour = OfflineAudioTour(
            id = fixture.getValue("id").jsonPrimitive.content,
            title = fixture.getValue("title").jsonPrimitive.content,
            language = fixture.getValue("language").jsonPrimitive.content,
            downloadSizeMB = fixture.getValue("downloadSizeMB").jsonPrimitive.int,
            availableMB = fixture.getValue("availableMB").jsonPrimitive.int,
            meteredConnection = fixture.getValue("meteredConnection").jsonPrimitive.boolean,
            chapters = fixture.getValue("chapters").jsonArray.map { value ->
                val row = value.jsonObject
                AudioTourChapter(row.getValue("id").jsonPrimitive.content,
                    row.getValue("title").jsonPrimitive.content, row.getValue("body").jsonPrimitive.content)
            })
        OfflineAudioTourPanel(tour = tour,
            onWifiOnlyChange = { wifiOnly -> onEvent("audio.wifiOnly:${tour.id}:$wifiOnly") },
            onDownload = { id, wifiOnly -> onEvent("audio.download:$id:${if (wifiOnly) "wifi" else "mobile"}") })
    }
}
