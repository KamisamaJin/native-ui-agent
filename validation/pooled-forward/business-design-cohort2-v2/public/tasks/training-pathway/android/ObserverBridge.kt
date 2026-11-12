// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.int
import kotlinx.serialization.json.boolean
import com.example.reply.ui.components.business.TrainingPathwayInput
import com.example.reply.ui.components.business.TrainingPathwayEnrollment
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = TrainingPathwayInput(
            entityID = fixture["entityID"]!!.jsonPrimitive.content,
            revision = fixture["revision"]!!.jsonPrimitive.int,
            title = fixture["title"]!!.jsonPrimitive.content,
            context = fixture["context"]!!.jsonPrimitive.content,
            notes = fixture["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            completedHours = fixture["completedHours"]!!.jsonPrimitive.int,
            completedModules = fixture["completedModules"]!!.jsonArray.map { it.jsonPrimitive.content },
            cohortSeats = fixture["cohortSeats"]!!.jsonPrimitive.int,
            deviceCredits = fixture["deviceCredits"]!!.jsonPrimitive.int,
            assessmentSlots = fixture["assessmentSlots"]!!.jsonPrimitive.int,
            practiceSeats = fixture["practiceSeats"]!!.jsonPrimitive.int
        )
        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {
            TrainingPathwayEnrollment(input = input, onEvent = onEvent)
        }
    }
}
