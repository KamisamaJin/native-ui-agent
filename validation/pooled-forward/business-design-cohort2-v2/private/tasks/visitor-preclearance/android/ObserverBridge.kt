// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.int
import kotlinx.serialization.json.boolean
import com.example.reply.ui.components.business.VisitorAccessInput
import com.example.reply.ui.components.business.VisitorAccessPreclearance
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = VisitorAccessInput(
            entityID = fixture["entityID"]!!.jsonPrimitive.content,
            revision = fixture["revision"]!!.jsonPrimitive.int,
            title = fixture["title"]!!.jsonPrimitive.content,
            context = fixture["context"]!!.jsonPrimitive.content,
            notes = fixture["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            guestCount = fixture["guestCount"]!!.jsonPrimitive.int,
            sponsorActive = fixture["sponsorActive"]!!.jsonPrimitive.boolean,
            badgeTrainingComplete = fixture["badgeTrainingComplete"]!!.jsonPrimitive.boolean,
            researchCapacity = fixture["researchCapacity"]!!.jsonPrimitive.int,
            officeCapacity = fixture["officeCapacity"]!!.jsonPrimitive.int,
            verifiedIDs = fixture["verifiedIDs"]!!.jsonPrimitive.int,
            labInductions = fixture["labInductions"]!!.jsonPrimitive.int,
            escortCount = fixture["escortCount"]!!.jsonPrimitive.int
        )
        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {
            VisitorAccessPreclearance(input = input, onEvent = onEvent)
        }
    }
}
