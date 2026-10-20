package org.nativeobserver

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*

object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  val count=input["rows"]?.jsonPrimitive?.intOrNull ?: 1
  var expanded by remember { mutableStateOf(false) }
  Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
   Text("Generic observation surface",Modifier.testTag("gen.title"))
   Button({onEvent("delivered")},Modifier.testTag("gen.correct")){Text("Deliver correct event")}
   Button({onEvent("disabled")},Modifier.testTag("gen.disabled"),enabled=false){Text("Disabled event")}
   Button({},Modifier.testTag("gen.silent")){Text("Silent action")}
   Button({onEvent("different")},Modifier.testTag("gen.wrong")){Text("Wrong event")}
   repeat(count){n->Text("Native generic row $n",Modifier.heightIn(min=36.dp).testTag("gen.row.$n"))}
   if(expanded)Text("Expanded neutral measurement text. ".repeat(24),Modifier.testTag("gen.expanded"))
   Button({expanded=!expanded;onEvent("expanded")},Modifier.fillMaxWidth().heightIn(min=48.dp).testTag("gen.disclosure")){Text(if(expanded)"Collapse measured detail"else"Expand measured detail")}
   Text("Generic final label",Modifier.testTag("gen.tail"))
  }
 }
}
