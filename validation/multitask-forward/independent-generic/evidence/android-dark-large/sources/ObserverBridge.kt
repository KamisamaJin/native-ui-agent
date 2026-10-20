package org.nativeobserver
import androidx.compose.runtime.Composable
import kotlinx.serialization.json.*
import org.neutral.ReadingPanel
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  ReadingPanel(input["key"]!!.jsonPrimitive.content,input["title"]!!.jsonPrimitive.content,onEvent)
 }
}
