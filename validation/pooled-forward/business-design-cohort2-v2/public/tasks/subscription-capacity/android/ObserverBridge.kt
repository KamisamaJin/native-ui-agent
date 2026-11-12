// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.int
import kotlinx.serialization.json.boolean
import com.example.reply.ui.components.business.SubscriptionCapacityInput
import com.example.reply.ui.components.business.SubscriptionCapacityChange
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = SubscriptionCapacityInput(
            entityID = fixture["entityID"]!!.jsonPrimitive.content,
            revision = fixture["revision"]!!.jsonPrimitive.int,
            title = fixture["title"]!!.jsonPrimitive.content,
            context = fixture["context"]!!.jsonPrimitive.content,
            notes = fixture["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            seatCount = fixture["seatCount"]!!.jsonPrimitive.int,
            teamQuota = fixture["teamQuota"]!!.jsonPrimitive.int,
            scaleQuota = fixture["scaleQuota"]!!.jsonPrimitive.int,
            prepaidMonths = fixture["prepaidMonths"]!!.jsonPrimitive.int,
            accountBalanceCents = fixture["accountBalanceCents"]!!.jsonPrimitive.int
        )
        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {
            SubscriptionCapacityChange(input = input, onEvent = onEvent)
        }
    }
}
