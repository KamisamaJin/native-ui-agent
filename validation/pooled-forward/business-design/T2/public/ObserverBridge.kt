package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.int
import com.example.reply.ui.theme.ContrastAwareReplyTheme
import com.example.reply.ui.components.business.*

private fun JsonObject.s(k: String) = getValue(k).jsonPrimitive.content
private fun JsonObject.i(k: String) = getValue(k).jsonPrimitive.int
private fun JsonObject.b(k: String) = getValue(k).jsonPrimitive.boolean

object ObserverBridge {
    @Composable
    fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val decoded = AppointmentRescheduleFixture(
            entityId = input.s("entityId"),
            entityTitle = input.s("entityTitle"),
            description = input.s("description"),
            allowVideo = input.b("allowVideo"),
            slots = input.getValue("slots").jsonArray.map { value ->
                val item = value.jsonObject
                RescheduleSlot(
                    id = item.s("id"),
                    label = item.s("label"),
                    detail = item.s("detail"),
                    available = item.b("available"),
                    modes = item.getValue("modes").jsonArray.map { it.jsonPrimitive.content },
                )
            },
        )
        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {
            AppointmentReschedulePanel(fixture = decoded, onEvent = onEvent)
        }
    }
}
