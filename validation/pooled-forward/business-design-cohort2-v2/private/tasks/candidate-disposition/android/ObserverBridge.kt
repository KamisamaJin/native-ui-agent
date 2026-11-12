// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.int
import kotlinx.serialization.json.boolean
import com.example.reply.ui.components.business.CandidateDispositionInput
import com.example.reply.ui.components.business.CandidateDispositionReview
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val input = CandidateDispositionInput(
            entityID = fixture["entityID"]!!.jsonPrimitive.content,
            revision = fixture["revision"]!!.jsonPrimitive.int,
            title = fixture["title"]!!.jsonPrimitive.content,
            context = fixture["context"]!!.jsonPrimitive.content,
            notes = fixture["notes"]!!.jsonArray.map { it.jsonPrimitive.content },
            portfolioScore = fixture["portfolioScore"]!!.jsonPrimitive.int,
            reviewerCapacity = fixture["reviewerCapacity"]!!.jsonPrimitive.int,
            technicalSlots = fixture["technicalSlots"]!!.jsonPrimitive.int,
            recruiterSlots = fixture["recruiterSlots"]!!.jsonPrimitive.int,
            legalHold = fixture["legalHold"]!!.jsonPrimitive.boolean,
            assessmentCount = fixture["assessmentCount"]!!.jsonPrimitive.int,
            openRoleCount = fixture["openRoleCount"]!!.jsonPrimitive.int
        )
        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {
            CandidateDispositionReview(input = input, onEvent = onEvent)
        }
    }
}
