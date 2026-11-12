// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import com.google.gson.JsonObject
import com.example.reply.ui.components.business.VisitorAccessInput
import com.example.reply.ui.components.business.VisitorAccessPreclearance
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = VisitorAccessInput(
            entityID = fixture.get("entityID").asString,
            revision = fixture.get("revision").asInt,
            title = fixture.get("title").asString,
            context = fixture.get("context").asString,
            notes = fixture.getAsJsonArray("notes").map { it.asString },
            guestCount = fixture.get("guestCount").asInt,
            sponsorActive = fixture.get("sponsorActive").asBoolean,
            badgeTrainingComplete = fixture.get("badgeTrainingComplete").asBoolean,
            researchCapacity = fixture.get("researchCapacity").asInt,
            officeCapacity = fixture.get("officeCapacity").asInt,
            verifiedIDs = fixture.get("verifiedIDs").asInt,
            labInductions = fixture.get("labInductions").asInt,
            escortCount = fixture.get("escortCount").asInt
        )
        ContrastAwareReplyTheme {
            VisitorAccessPreclearance(input = input, onEvent = onEvent)
        }
    }
}
