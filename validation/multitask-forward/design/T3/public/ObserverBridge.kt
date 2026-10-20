package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val request = CafeGroupOrderRequest(
            id = input["id"]!!.jsonPrimitive.content,
            title = input["title"]!!.jsonPrimitive.content,
            context = input["context"]!!.jsonPrimitive.content,
            choiceWidth = input["choiceWidth"]!!.jsonPrimitive.double,
            notes = input["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            maxServings = input["maxServings"]!!.jsonPrimitive.int,
            member = input["member"]!!.jsonPrimitive.boolean,
            discountThreshold = input["discountThreshold"]!!.jsonPrimitive.int,
            discountCents = input["discountCents"]!!.jsonPrimitive.int,
            reuseCreditCents = input["reuseCreditCents"]!!.jsonPrimitive.int,
            reuseAllowed = input["reuseAllowed"]!!.jsonPrimitive.boolean,
            selectedIDs = input["selectedIDs"]!!.jsonArray.map { it.jsonPrimitive.content },
            reuse = input["reuse"]!!.jsonPrimitive.boolean,
            drinks = input["drinks"]!!.jsonArray.map { value -> val item = value.jsonObject; CafeGroupDrink(id = item["id"]!!.jsonPrimitive.content, name = item["name"]!!.jsonPrimitive.content, cents = item["cents"]!!.jsonPrimitive.int, available = item["available"]!!.jsonPrimitive.boolean, supportsReuse = item["supportsReuse"]!!.jsonPrimitive.boolean, note = item["note"]!!.jsonPrimitive.content) }
        )
        CafeGroupOrderPanel(request = request, onConfirm = { id, ids, option ->
            onEvent("ordered:$id:${ids.sorted().joinToString(",")}:$option")
        })
    }
}
