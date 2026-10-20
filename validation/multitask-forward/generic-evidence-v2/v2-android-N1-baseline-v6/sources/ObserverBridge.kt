package org.nativeobserver
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.serialization.json.*
import java.io.File
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit){
  var expanded by remember { mutableStateOf(false) }
  val base=input["height"]!!.jsonPrimitive.int;val rows=input["rows"]!!.jsonPrimitive.int;val title=input["title"]!!.jsonPrimitive.content
  val density=LocalDensity.current.density
  @Composable fun Cell(label:String,id:String,action:()->Unit){
   Button(onClick=action,modifier=Modifier.width(84.dp).height((base+if(expanded)16 else 0).dp).semantics{testTag=id}.onGloballyPositioned{c->
    File(System.getenv("NATIVE_UI_OUTPUT"),"layout-witness.txt").appendText("$id|$title|$expanded|${c.size.width}|${c.size.height}|${density.toDouble()}\n")
   },contentPadding=PaddingValues(0.dp)){Text(label,fontSize=14.sp)}
  }
  Column(verticalArrangement=Arrangement.spacedBy(12.dp)){
   Text("Measurements $title",Modifier.semantics{testTag="neutral.header"})
   Row(horizontalArrangement=Arrangement.spacedBy(12.dp)){Cell("Go","neutral.primary"){expanded=!expanded;onEvent("expanded")};Cell("Next","neutral.secondary"){onEvent("secondary")}}
   repeat(rows){Text("Neutral section $it",Modifier.heightIn(min=40.dp))}
   Cell("End","neutral.footer"){onEvent("footer")}
  }
 }
}
