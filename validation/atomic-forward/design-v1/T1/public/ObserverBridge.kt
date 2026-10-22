package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.WorkshopSlotPlanner
import com.example.reply.ui.components.WorkshopSlotPlannerModel
import com.example.reply.ui.components.WorkshopSlot
import kotlinx.serialization.json.*

// Adapter only. The production component owns all state and semantics.
object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        fun JsonObject.s(key: String): String = this[key]!!.jsonPrimitive.content
        val model = WorkshopSlotPlannerModel(
            revision = input.s("revision"), title = input.s("title"), subtitle = input.s("subtitle"),
            notice = input.s("notice"), footer = input.s("footer"),
            initialDetailsExpanded = input["initialDetailsExpanded"]!!.jsonPrimitive.boolean,
            initialSelectedID = input["initialSelectedID"]?.jsonPrimitive?.contentOrNull,
            slots = input["slots"]!!.jsonArray.map { item ->
                with(item.jsonObject) { WorkshopSlot(id = s("id"), label = s("label"), detail = s("detail"), available = this["available"]!!.jsonPrimitive.boolean) }
            })
        WorkshopSlotPlanner(model = model,
            onSelect = { id -> onEvent("workshop:select:$id") },
            onDetailsChange = { expanded -> onEvent("workshop:details:${if (expanded) "open" else "closed"}") },
            onReserve = { id -> onEvent("workshop:reserve:$id") })
    }
}
