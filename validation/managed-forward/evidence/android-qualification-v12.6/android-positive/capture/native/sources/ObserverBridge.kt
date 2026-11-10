package org.nativeobserver
import androidx.compose.runtime.Composable
import com.example.reply.ui.components.NeutralCounter
import kotlinx.serialization.json.*
object ObserverBridge {
    @Composable fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        NeutralCounter(fixture["seed"]!!.jsonPrimitive.int, onEvent)
    }
}
