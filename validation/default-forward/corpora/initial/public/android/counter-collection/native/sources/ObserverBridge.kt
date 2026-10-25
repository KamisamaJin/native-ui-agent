package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.CollectionAuthorizationCard
import com.example.reply.ui.components.CollectionAuthorizationData
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.boolean

// Data conversion only; the production component owns presentation and interaction.
object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        fun string(key: String): String = fixture.getValue(key).jsonPrimitive.content
        val data = CollectionAuthorizationData(
            requestID = string("requestID"),
            title = string("title"),
            jobSummary = string("jobSummary"),
            pickupWindow = string("pickupWindow"),
            notesClosedTitle = string("notesClosedTitle"),
            notesOpenTitle = string("notesOpenTitle"),
            notesBody = string("notesBody"),
            selfTitle = string("selfTitle"),
            selfDetail = string("selfDetail"),
            delegateTitle = string("delegateTitle"),
            delegateDetail = string("delegateDetail"),
            acknowledgement = string("acknowledgement"),
            confirmTitle = string("confirmTitle"),
            sentTitle = string("sentTitle"),
            readyMessage = string("readyMessage"),
            needsAcknowledgementMessage = string("needsAcknowledgementMessage"),
            sentMessage = string("sentMessage"),
            delegateUnavailableMessage = string("delegateUnavailableMessage"),
            delegateAvailable = fixture.getValue("delegateAvailable").jsonPrimitive.boolean
        )
        CollectionAuthorizationCard(data = data, onEvent = onEvent)
    }
}
