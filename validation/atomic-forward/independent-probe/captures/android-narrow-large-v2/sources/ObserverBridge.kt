package org.nativeobserver
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import com.example.reply.ui.components.QuietMomentCard
import kotlinx.serialization.json.*
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  fun text(key:String)=input[key]!!.jsonPrimitive.content
  fun color(key:String)=Color((0xFF000000L or text(key).toLong(16)).toInt())
  QuietMomentCard(text("title"),text("body"),color("canvas"),color("band"),onAcknowledge={onEvent("acknowledged")})
 }
}
