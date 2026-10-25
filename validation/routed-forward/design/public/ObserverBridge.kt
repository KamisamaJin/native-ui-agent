package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.ListeningBreakInput
import com.example.reply.ui.components.ListeningBreakOption
import com.example.reply.ui.components.ListeningBreakPanel
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Caller adaptation only; no remember, replacement key or product UI is supplied here.
object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        fun text(key: String) = fixture.getValue(key).jsonPrimitive.content
        val options = fixture.getValue("options").jsonArray.map { value ->
            val item = value.jsonObject
            ListeningBreakOption(id = item.getValue("id").jsonPrimitive.content,
                title = item.getValue("title").jsonPrimitive.content,
                detail = item.getValue("detail").jsonPrimitive.content,
                isAvailable = item.getValue("isAvailable").jsonPrimitive.boolean)
        }
        val input = ListeningBreakInput(sessionID = text("sessionID"), title = text("title"),
            introduction = text("introduction"), options = options,
            quietNote = text("quietNote"), footer = text("footer"))
        ListeningBreakPanel(input = input,
            onStart = { sessionID, optionID -> onEvent("listening.started:$sessionID:$optionID") },
            onCancel = { sessionID -> onEvent("listening.canceled:$sessionID") })
    }
}
