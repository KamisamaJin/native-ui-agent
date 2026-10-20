package org.nativeobserver
import androidx.compose.runtime.*
import com.example.readingnotes.ReadingNotes
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  ReadingNotes(title=input["title"]!!.jsonPrimitive.content,footer=input["footer"]!!.jsonPrimitive.content,prefix=input["prefix"]!!.jsonPrimitive.content,onOpen={onEvent("notes.open")})
 }
}
