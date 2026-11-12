// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import com.google.gson.JsonObject
import com.example.reply.ui.components.business.SubscriptionCapacityInput
import com.example.reply.ui.components.business.SubscriptionCapacityChange
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = SubscriptionCapacityInput(
            entityID = fixture.get("entityID").asString,
            revision = fixture.get("revision").asInt,
            title = fixture.get("title").asString,
            context = fixture.get("context").asString,
            notes = fixture.getAsJsonArray("notes").map { it.asString },
            seatCount = fixture.get("seatCount").asInt,
            teamQuota = fixture.get("teamQuota").asInt,
            scaleQuota = fixture.get("scaleQuota").asInt,
            prepaidMonths = fixture.get("prepaidMonths").asInt,
            accountBalanceCents = fixture.get("accountBalanceCents").asInt
        )
        ContrastAwareReplyTheme {
            SubscriptionCapacityChange(input = input, onEvent = onEvent)
        }
    }
}
