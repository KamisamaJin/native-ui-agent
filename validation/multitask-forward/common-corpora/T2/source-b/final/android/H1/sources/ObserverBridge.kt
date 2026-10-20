package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val request = BroadcastCueMixerRequest(
            id = input["id"]!!.jsonPrimitive.content,
            title = input["title"]!!.jsonPrimitive.content,
            context = input["context"]!!.jsonPrimitive.content,
            maxLiveUnits = input["maxLiveUnits"]!!.jsonPrimitive.int,
            maxLevel = input["maxLevel"]!!.jsonPrimitive.int,
            mode = input["mode"]!!.jsonPrimitive.content,
            stepperWidth = input["stepperWidth"]!!.jsonPrimitive.double,
            notes = input["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            channels = input["channels"]!!.jsonArray.map { value -> val item = value.jsonObject; BroadcastMixChannel(id = item["id"]!!.jsonPrimitive.content, name = item["name"]!!.jsonPrimitive.content, caption = item["caption"]!!.jsonPrimitive.content, level = item["level"]!!.jsonPrimitive.int, muted = item["muted"]!!.jsonPrimitive.boolean, locked = item["locked"]!!.jsonPrimitive.boolean) }
        )
        BroadcastCueMixerPanel(request = request, onConfirm = { id, mode, channels ->
            val payload = channels.sortedBy { it.id }.joinToString(",") { "${it.id}=${it.level}/${it.muted}" }
            onEvent("mix:$id:$mode:$payload")
        })
    }
}
