package org.nativeobserver
import androidx.compose.runtime.Composable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(16.dp)) {
   Text(input["title"]!!.jsonPrimitive.content,Modifier.testTag("probe.title"))
   Button(onClick={onEvent("probe.primary")},modifier=Modifier.testTag("probe.primary")){Text("Probe action")}
   repeat(12){Text("Capability row ${it+1}",Modifier.fillMaxWidth().height(64.dp))}
   Button(onClick={onEvent("probe.last")},modifier=Modifier.testTag("probe.last")){Text("Last native action")}
   Text(input["detail"]!!.jsonPrimitive.content,Modifier.testTag("probe.detail"))
  }
 }
}
