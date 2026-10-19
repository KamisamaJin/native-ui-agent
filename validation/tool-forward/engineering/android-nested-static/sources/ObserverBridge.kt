package org.nativeobserver
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit){ Column {
  Column(Modifier.testTag("nested").clickable{onEvent("outer")}){Text("Outer action");Button({onEvent("inner")},Modifier.testTag("inner")){Text("Inner action")}}
  repeat(8){Text("Long plain content $it",Modifier.height(72.dp))}
  Text("Lower non-control heading",Modifier.testTag("heading"))
  Button({onEvent("last")},Modifier.testTag("last")){Text("Last action")}
 } }
}
