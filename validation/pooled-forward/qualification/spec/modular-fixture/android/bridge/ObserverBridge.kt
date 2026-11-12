package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive
import org.nativequalification.NativeQualificationProbe

// Test-input decoding only. No component state, control or callback implementation.
object ObserverBridge {
    @Composable
    fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val marker = input["marker"]?.jsonPrimitive?.contentOrNull
            ?: error("Qualification fixture requires marker")
        val detail = input["detail"]?.jsonPrimitive?.contentOrNull
            ?: error("Qualification fixture requires detail")
        NativeQualificationProbe(marker = marker, detail = detail, onEvent = onEvent)
    }
}
