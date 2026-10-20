package org.nativeobserver

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable
    fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text(input["title"]!!.jsonPrimitive.content, Modifier.semantics { testTag = "probe.title" })
            Button(onClick = { onEvent("probe.activated") },
                   modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).semantics { testTag = "probe.action" }) {
                Text("Activate probe")
            }
            (1..8).forEach { i -> Text("Probe row $i", Modifier.fillMaxWidth().heightIn(min = 80.dp)) }
            Text(input["footer"]!!.jsonPrimitive.content, Modifier.semantics { testTag = "probe.footer" })
        }
    }
}
