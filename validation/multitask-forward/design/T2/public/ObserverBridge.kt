package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val request = PublicationRightsRequest(
            id = input["id"]!!.jsonPrimitive.content,
            title = input["title"]!!.jsonPrimitive.content,
            context = input["context"]!!.jsonPrimitive.content,
            choiceWidth = input["choiceWidth"]!!.jsonPrimitive.double,
            notes = input["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            baseCents = input["baseCents"]!!.jsonPrimitive.int,
            exclusiveCents = input["exclusiveCents"]!!.jsonPrimitive.int,
            exclusiveAllowed = input["exclusiveAllowed"]!!.jsonPrimitive.boolean,
            selectedIDs = input["selectedIDs"]!!.jsonArray.map { it.jsonPrimitive.content },
            exclusive = input["exclusive"]!!.jsonPrimitive.boolean,
            channels = input["channels"]!!.jsonArray.map { value -> val item = value.jsonObject; PublicationRightsChannel(id = item["id"]!!.jsonPrimitive.content, name = item["name"]!!.jsonPrimitive.content, cents = item["cents"]!!.jsonPrimitive.int, available = item["available"]!!.jsonPrimitive.boolean, note = item["note"]!!.jsonPrimitive.content) }
        )
        PublicationRightsPanel(request = request, onConfirm = { id, ids, option ->
            onEvent("licensed:$id:${ids.sorted().joinToString(",")}:$option")
        })
    }
}
