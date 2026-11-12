// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import com.google.gson.JsonObject
import com.example.reply.ui.components.business.CateringPackageInput
import com.example.reply.ui.components.business.CateringPackagePlanner
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = CateringPackageInput(
            entityID = fixture.get("entityID").asString,
            revision = fixture.get("revision").asInt,
            title = fixture.get("title").asString,
            context = fixture.get("context").asString,
            notes = fixture.getAsJsonArray("notes").map { it.asString },
            guestCount = fixture.get("guestCount").asInt,
            vegetarianGuests = fixture.get("vegetarianGuests").asInt,
            vegetarianMeals = fixture.get("vegetarianMeals").asInt,
            buffetCapacity = fixture.get("buffetCapacity").asInt,
            boxedCapacity = fixture.get("boxedCapacity").asInt,
            reusableSets = fixture.get("reusableSets").asInt,
            compostableSets = fixture.get("compostableSets").asInt
        )
        ContrastAwareReplyTheme {
            CateringPackagePlanner(input = input, onEvent = onEvent)
        }
    }
}
