package org.nativeobserver
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit){
  var selected by remember(input){mutableStateOf(false)}
  Column{
   Button({selected=!selected;onEvent("probe.click")},Modifier.fillMaxWidth().height(48.dp).semantics{testTag="probe.button"},enabled=input["enabled"]?.jsonPrimitive?.boolean ?: true){Text(if(selected)"Selected"else"Choose")}
   repeat(input["rows"]?.jsonPrimitive?.int ?: 3){i->Text("Generic native row $i",Modifier.fillMaxWidth().height(72.dp))}
   Button({onEvent("probe.last")},Modifier.fillMaxWidth().height(48.dp).semantics{testTag="probe.last"}){Text("Last action")}
  }
 }
}
