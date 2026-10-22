package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.RiverSensorTriageBoard
import com.example.reply.ui.components.RiverSensorTriageModel
import com.example.reply.ui.components.RiverSensorIncident
import kotlinx.serialization.json.*

// Adapter only. The production component owns all state and semantics.
object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        fun JsonObject.s(key: String): String = this[key]!!.jsonPrimitive.content
        val model = RiverSensorTriageModel(
            revision = input.s("revision"), title = input.s("title"), subtitle = input.s("subtitle"),
            notice = input.s("notice"), footer = input.s("footer"), guidance = input.s("guidance"),
            initialDetailsExpanded = input["initialDetailsExpanded"]!!.jsonPrimitive.boolean,
            initialSelectedID = input["initialSelectedID"]?.jsonPrimitive?.contentOrNull,
            incidents = input["incidents"]!!.jsonArray.map { item ->
                with(item.jsonObject) { RiverSensorIncident(id = s("id"), label = s("label"), detail = s("detail"), unavailableReason = s("unavailableReason"), available = this["available"]!!.jsonPrimitive.boolean, severity = s("severity")) }
            })
        RiverSensorTriageBoard(model = model,
            onSelect = { id -> onEvent("river:select:$id") },
            onDetailsChange = { expanded -> onEvent("river:details:${if (expanded) "open" else "closed"}") },
            onAcknowledge = { id -> onEvent("river:acknowledge:$id") })
    }
}
