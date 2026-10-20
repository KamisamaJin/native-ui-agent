package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val request = CollectionConditionReviewRequest(
            id = input["id"]!!.jsonPrimitive.content,
            title = input["title"]!!.jsonPrimitive.content,
            context = input["context"]!!.jsonPrimitive.content,
            focusID = input["focusID"]!!.jsonPrimitive.content,
            queueWidth = input["queueWidth"]!!.jsonPrimitive.double,
            notes = input["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            objects = input["objects"]!!.jsonArray.map { value -> val item = value.jsonObject; CollectionConditionObject(id = item["id"]!!.jsonPrimitive.content, title = item["title"]!!.jsonPrimitive.content, material = item["material"]!!.jsonPrimitive.content, inspectionNote = item["inspectionNote"]!!.jsonPrimitive.content, status = item["status"]!!.jsonPrimitive.content, reason = item["reason"]?.jsonPrimitive?.contentOrNull, editable = item["editable"]!!.jsonPrimitive.boolean, required = item["required"]!!.jsonPrimitive.boolean) }
        )
        CollectionConditionReviewPanel(request = request, onConfirm = { id, decisions ->
            val payload = decisions.sortedBy { it.id }.joinToString(",") { "${it.id}=${it.status}/${it.reason ?: "-"}" }
            onEvent("condition:$id:$payload")
        })
    }
}
