package org.nativeobserver

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*

object ObserverBridge {
 @Composable fun Content(input: JsonObject, onEvent: (String)->Unit) {
  val rows=input["rows"]?.jsonPrimitive?.intOrNull ?: 8
  val token=input["token"]?.jsonPrimitive?.content ?: "A"
  var expanded by remember { mutableStateOf(false) }
  Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
   Text("Panel $token",Modifier.testTag("probe.header"))
   Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
    Text("A",Modifier.size(72.dp,32.dp).testTag("probe.markerA"))
    Text("B",Modifier.size(72.dp,32.dp).testTag("probe.markerB"))
   }
   Text("Ink",Modifier.testTag("probe.ink"),color=androidx.compose.ui.graphics.Color(0xFF276145))
   Button({expanded=!expanded;onEvent("expanded")},Modifier.testTag("probe.disclosure")) {
    Text(if(expanded)"Hide sections" else "Show sections")
   }
   Button({onEvent("disabled")},Modifier.testTag("probe.disabled"),enabled=false){Text("Unavailable")}
   repeat(rows){n->Text("Section $n",Modifier.heightIn(min=48.dp).testTag("probe.row.$n"))}
   if(expanded)Text("Neutral section details. ".repeat(24),Modifier.testTag("probe.detail"))
   Text("End $token",Modifier.testTag("probe.footer"))
   Button({onEvent("secondary")},Modifier.testTag("probe.secondary")){Text("Continue $token")}
  }
 }
}
