// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.int
import kotlinx.serialization.json.boolean
import com.example.reply.ui.components.business.CateringPackageInput
import com.example.reply.ui.components.business.CateringPackagePlanner
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = CateringPackageInput(
            entityID = fixture["entityID"]!!.jsonPrimitive.content,
            revision = fixture["revision"]!!.jsonPrimitive.int,
            title = fixture["title"]!!.jsonPrimitive.content,
            context = fixture["context"]!!.jsonPrimitive.content,
            notes = fixture["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            guestCount = fixture["guestCount"]!!.jsonPrimitive.int,
            vegetarianGuests = fixture["vegetarianGuests"]!!.jsonPrimitive.int,
            vegetarianMeals = fixture["vegetarianMeals"]!!.jsonPrimitive.int,
            buffetCapacity = fixture["buffetCapacity"]!!.jsonPrimitive.int,
            boxedCapacity = fixture["boxedCapacity"]!!.jsonPrimitive.int,
            reusableSets = fixture["reusableSets"]!!.jsonPrimitive.int,
            compostableSets = fixture["compostableSets"]!!.jsonPrimitive.int
        )
        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {
            CateringPackagePlanner(input = input, onEvent = onEvent)
        }
    }
}
