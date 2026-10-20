package org.nativeobserver
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input: JsonObject,onEvent:(String)->Unit) {
  Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
   Text(input["title"]!!.jsonPrimitive.content,Modifier.testTag("cap.title"))
   Button({onEvent("cap.primary")},Modifier.height(48.dp).testTag("cap.primary")){Text("Primary probe")}
   repeat(8){Text("Capability row ${it+1}",Modifier.fillMaxWidth().height(70.dp))}
   Button({onEvent("cap.last")},Modifier.height(48.dp).testTag("cap.last")){Text("Last probe")}
  }
 }
}
