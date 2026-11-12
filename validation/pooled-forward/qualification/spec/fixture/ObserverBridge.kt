package org.nativeobserver

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTag
import androidx.compose.ui.unit.dp
import java.util.UUID
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive

// Qualification capability fixture only. Not an Activity/physical-touch probe.
object ObserverBridge {
    @Composable
    fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val marker = input["marker"]?.jsonPrimitive?.contentOrNull
            ?: error("Qualification fixture requires marker")
        val detail = input["detail"]?.jsonPrimitive?.contentOrNull
            ?: error("Qualification fixture requires detail")
        val instanceID = remember { UUID.randomUUID().toString() }
        var taps by remember { mutableStateOf(0) }

        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("Native capability qualification", tagged("probe.title"))
            Text(marker, tagged("probe.marker"))
            Text("Instance", tagged("probe.instance").semantics {
                contentDescription = "Instance: $instanceID"
            })
            Text("Tap count: $taps", tagged("probe.count"))
            Button(
                onClick = {
                    taps += 1
                    onEvent("probe.primary")
                },
                modifier = tagged("probe.primary").fillMaxWidth().height(48.dp)
            ) {
                Text("Primary native action")
            }
            Button(
                onClick = { onEvent("probe.disabled") },
                enabled = false,
                modifier = tagged("probe.disabled").fillMaxWidth().height(48.dp)
            ) {
                Text("Disabled native action")
            }
            repeat(18) { index ->
                Text(
                    "Native content row ${index + 1}",
                    tagged("probe.row.$index").fillMaxWidth().heightIn(min = 64.dp)
                )
            }
            Button(
                onClick = { onEvent("probe.last") },
                modifier = tagged("probe.last").fillMaxWidth().height(48.dp)
            ) {
                Text("Last native action")
            }
            Text(detail, tagged("probe.detail"))
        }
    }

    private fun tagged(identifier: String): Modifier = Modifier.semantics {
        testTag = identifier
    }
}
