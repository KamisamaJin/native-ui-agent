package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.MenuChangeModel
import com.example.reply.ui.components.MenuChangeReviewPanel
import com.example.reply.ui.components.MenuReplacementOption
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        fun text(key: String) = fixture.getValue(key).jsonPrimitive.content
        fun integer(key: String) = fixture.getValue(key).jsonPrimitive.int
        val model = MenuChangeModel(
            requestID = text("requestID"),
            revision = integer("revision"),
            orderReference = text("orderReference"),
            venue = text("venue"),
            occasion = text("occasion"),
            originalDish = text("originalDish"),
            respondBy = text("respondBy"),
            requestedServings = integer("requestedServings"),
            prepaidTotalCents = integer("prepaidTotalCents"),
            trayReturnCreditCents = integer("trayReturnCreditCents"),
            notice = text("notice"),
            options = fixture.getValue("options").jsonArray.map { element ->
                val option = element.jsonObject
                MenuReplacementOption(
                    id = option.getValue("id").jsonPrimitive.content,
                    title = option.getValue("title").jsonPrimitive.content,
                    detail = option.getValue("detail").jsonPrimitive.content,
                    pricePerServingCents = option.getValue("pricePerServingCents").jsonPrimitive.int,
                    minimumServings = option.getValue("minimumServings").jsonPrimitive.int,
                    maximumServings = option.getValue("maximumServings").jsonPrimitive.int,
                    available = option.getValue("available").jsonPrimitive.boolean
                )
            },
            kitchenNotes = fixture.getValue("kitchenNotes").jsonArray.map { it.jsonPrimitive.content }
        )
        MenuChangeReviewPanel(model = model, onSubmit = { onEvent(it.wireValue) })
    }
}
