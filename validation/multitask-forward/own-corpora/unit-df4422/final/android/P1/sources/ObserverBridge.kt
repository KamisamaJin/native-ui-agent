package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val request = ExpeditionPackRequest(
            id = input["id"]!!.jsonPrimitive.content,
            title = input["title"]!!.jsonPrimitive.content,
            context = input["context"]!!.jsonPrimitive.content,
            choiceWidth = input["choiceWidth"]!!.jsonPrimitive.double,
            notes = input["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            baseGrams = input["baseGrams"]!!.jsonPrimitive.int,
            maxGrams = input["maxGrams"]!!.jsonPrimitive.int,
            requiresShelter = input["requiresShelter"]!!.jsonPrimitive.boolean,
            coverGrams = input["coverGrams"]!!.jsonPrimitive.int,
            selectedIDs = input["selectedIDs"]!!.jsonArray.map { it.jsonPrimitive.content },
            cover = input["cover"]!!.jsonPrimitive.boolean,
            items = input["items"]!!.jsonArray.map { value -> val item = value.jsonObject; ExpeditionPackItem(id = item["id"]!!.jsonPrimitive.content, name = item["name"]!!.jsonPrimitive.content, grams = item["grams"]!!.jsonPrimitive.int, available = item["available"]!!.jsonPrimitive.boolean, providesShelter = item["providesShelter"]!!.jsonPrimitive.boolean, note = item["note"]!!.jsonPrimitive.content) }
        )
        ExpeditionPackPanel(request = request, onConfirm = { id, ids, option ->
            onEvent("packed:$id:${ids.sorted().joinToString(",")}:$option")
        })
    }
}
