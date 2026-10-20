package org.nativeobserver

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.serialization.json.*

// Public controlled component; the bridge owns caller selection and replacement.
@Composable
fun ReadingChecklist(title: String, marked: Boolean, enabled: Boolean, onToggle: () -> Unit) {
    val ink = Color(0xFF1A292B)
    val teal = Color(0xFF006466)
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(title, fontSize = 24.sp, fontWeight = FontWeight.SemiBold, color = ink,
             modifier = Modifier.semantics { testTag = "reading.title" })
        Text(if (marked) "Section six marked" else "Nothing marked", fontSize = 16.sp, color = ink,
             modifier = Modifier.semantics { testTag = "reading.status" })
        (1..12).forEach { index ->
            Column(Modifier.fillMaxWidth().heightIn(min = 92.dp).background(Color(0xFFE6F0F0)).padding(12.dp),
                   verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Section $index", fontSize = 18.sp, fontWeight = FontWeight.SemiBold, color = ink)
                Text("Observe the shape of the path and note where it turns. Keep the description clear enough to revisit on another day.",
                     fontSize = 15.sp, color = ink)
            }
            if (index == 6) {
                Button(onClick = onToggle, enabled = enabled,
                       modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).semantics {
                           testTag = "reading.toggle"; selected = marked
                       }, colors = ButtonDefaults.buttonColors(containerColor = teal, contentColor = Color.White,
                            disabledContainerColor = Color.Gray, disabledContentColor = Color.White)) {
                    Text(if (marked) "Clear mark" else "Mark section six", fontSize = 16.sp,
                         fontWeight = FontWeight.SemiBold)
                }
            }
        }
        Text(if (marked) "Selection: section six" else "Selection: none", fontSize = 16.sp, color = ink,
             modifier = Modifier.semantics { testTag = "reading.footer" })
    }
}

object ObserverBridge {
    @Composable
    fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        var markedRevision by remember { mutableStateOf<String?>(null) }
        val revision = input["revision"]!!.jsonPrimitive.content
        val marked = markedRevision == revision
        ReadingChecklist(input["title"]!!.jsonPrimitive.content, marked, input["enabled"]!!.jsonPrimitive.boolean) {
            markedRevision = if (marked) null else revision
            onEvent("toggle-mark")
        }
    }
}
