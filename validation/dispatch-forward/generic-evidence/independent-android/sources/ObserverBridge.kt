package org.nativeobserver

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*

@Composable private fun FoldBoard(input: JsonObject, onEvent: (String) -> Unit) {
    var opened by remember { mutableStateOf(false) }
    val token = input["token"]!!.jsonPrimitive.content
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Text(input["title"]!!.jsonPrimitive.content, Modifier.testTag("fold.title"), style = MaterialTheme.typography.titleLarge)
        Button(onClick = { onEvent("locked:$token") }, enabled = false, modifier = Modifier.testTag("fold.locked")) { Text("Locked action") }
        if (opened) {
            Text("Expanded field remains open across caller replacement.", Modifier.fillMaxWidth().heightIn(min = 420.dp).background(Color(0xFFFFF9D9)).padding(top = 12.dp).testTag("fold.expansion"))
        }
        Button(onClick = { opened = true; onEvent("open:$token") }, modifier = Modifier.testTag("fold.open")) { Text(if (opened) "Field opened" else "Open field") }
        repeat(input["count"]!!.jsonPrimitive.int) { index ->
            Text("Section ${index + 1} of $token. A neutral component has independent paragraphs that wrap naturally within the offered width. Continue through the field to inspect every section.", Modifier.testTag("fold.row.$index"))
        }
        Button(onClick = { onEvent("finish:$token") }, modifier = Modifier.testTag("fold.finish")) { Text("Finish field $token") }
    }
}
object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        MaterialTheme(colorScheme = lightColorScheme()) { FoldBoard(input, onEvent) }
    }
}
