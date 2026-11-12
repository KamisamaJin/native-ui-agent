// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import com.google.gson.JsonObject
import com.example.reply.ui.components.business.TrainingPathwayInput
import com.example.reply.ui.components.business.TrainingPathwayEnrollment
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = TrainingPathwayInput(
            entityID = fixture.get("entityID").asString,
            revision = fixture.get("revision").asInt,
            title = fixture.get("title").asString,
            context = fixture.get("context").asString,
            notes = fixture.getAsJsonArray("notes").map { it.asString },
            completedHours = fixture.get("completedHours").asInt,
            completedModules = fixture.getAsJsonArray("completedModules").map { it.asString },
            cohortSeats = fixture.get("cohortSeats").asInt,
            deviceCredits = fixture.get("deviceCredits").asInt,
            assessmentSlots = fixture.get("assessmentSlots").asInt,
            practiceSeats = fixture.get("practiceSeats").asInt
        )
        ContrastAwareReplyTheme {
            TrainingPathwayEnrollment(input = input, onEvent = onEvent)
        }
    }
}
