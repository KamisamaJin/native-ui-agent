// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import com.google.gson.JsonObject
import com.example.reply.ui.components.business.CandidateDispositionInput
import com.example.reply.ui.components.business.CandidateDispositionReview
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = CandidateDispositionInput(
            entityID = fixture.get("entityID").asString,
            revision = fixture.get("revision").asInt,
            title = fixture.get("title").asString,
            context = fixture.get("context").asString,
            notes = fixture.getAsJsonArray("notes").map { it.asString },
            portfolioScore = fixture.get("portfolioScore").asInt,
            reviewerCapacity = fixture.get("reviewerCapacity").asInt,
            technicalSlots = fixture.get("technicalSlots").asInt,
            recruiterSlots = fixture.get("recruiterSlots").asInt,
            legalHold = fixture.get("legalHold").asBoolean,
            assessmentCount = fixture.get("assessmentCount").asInt,
            openRoleCount = fixture.get("openRoleCount").asInt
        )
        ContrastAwareReplyTheme {
            CandidateDispositionReview(input = input, onEvent = onEvent)
        }
    }
}
