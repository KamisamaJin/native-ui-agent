package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.BicycleServiceIntake
import com.example.reply.ui.components.BicycleServiceIntakeModel
import com.example.reply.ui.components.BicycleServiceOption
import kotlinx.serialization.json.*

// Adapter only. The production component owns all state and semantics.
object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        fun JsonObject.s(key: String): String = this[key]!!.jsonPrimitive.content
        val model = BicycleServiceIntakeModel(
            revision = input.s("revision"), title = input.s("title"), subtitle = input.s("subtitle"),
            notice = input.s("notice"), footer = input.s("footer"),
            initialDetailsExpanded = input["initialDetailsExpanded"]!!.jsonPrimitive.boolean,
            initialSelectedIDs = input["initialSelectedIDs"]!!.jsonArray.map { it.jsonPrimitive.content },
            services = input["services"]!!.jsonArray.map { item ->
                with(item.jsonObject) { BicycleServiceOption(id = s("id"), label = s("label"), detail = s("detail"), available = this["available"]!!.jsonPrimitive.boolean, minutes = this["minutes"]!!.jsonPrimitive.int) }
            })
        BicycleServiceIntake(model = model,
            onToggle = { id, selected -> onEvent("bicycle:toggle:$id:$selected") },
            onDetailsChange = { expanded -> onEvent("bicycle:details:${if (expanded) "open" else "closed"}") },
            onSubmit = { ids -> onEvent("bicycle:submit:${ids.sorted().joinToString(",")}") })
    }
}
