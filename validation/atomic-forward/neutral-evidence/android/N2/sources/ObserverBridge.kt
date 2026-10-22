package org.nativeobserver
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  val changed=input["phase"]!!.jsonPrimitive.content == "B"
  Column(Modifier.fillMaxWidth().background(if(changed)Color(0xFFECE2D1)else Color(0xFFD6E8F3)).padding(12.dp).semantics{testTag="probe.canvas"},verticalArrangement=Arrangement.spacedBy(16.dp)) {
   Text("Atomic color sample",Modifier.semantics{testTag="probe.title"},fontSize=20.sp)
   Button(onClick={onEvent("tone")},modifier=Modifier.width(96.dp).height(56.dp).semantics{testTag="probe.tile"},shape=androidx.compose.ui.graphics.RectangleShape,colors=ButtonDefaults.buttonColors(containerColor=if(changed)Color(0xFF976038)else Color(0xFF397A91)),contentPadding=PaddingValues(0.dp)) { Text("Tone",fontSize=15.sp,color=Color.White) }
   repeat(14){ Text("Neutral note $it: a short observation line that can wrap with larger text.",fontSize=16.sp) }
  }
 }
}
