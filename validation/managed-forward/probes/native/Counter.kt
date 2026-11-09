package com.example.reply.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTag
import androidx.compose.ui.unit.dp

@Composable
fun NeutralCounter(seed: Int, onEvent: (String) -> Unit) {
    var count by remember(seed) { mutableStateOf(seed) }
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Tally: $count", Modifier.semantics { testTag = "counter.tally" })
        Button(onClick = { count++; onEvent("increment") }, modifier = Modifier.height(48.dp).semantics { testTag = "counter.increment" }) { Text("Count") }
        Button(onClick = { onEvent("disabled") }, enabled = false, modifier = Modifier.height(48.dp).semantics { testTag = "counter.disabled" }) { Text("Unavailable by design") }
        Row(Modifier.semantics { testTag = "counter.pair" }) {
            Button(onClick = { onEvent("left") }) { Text("Left") }
            Button(onClick = { onEvent("right") }) { Text("Right") }
        }
        Button(onClick = { onEvent("continue") }, enabled = count > 0, modifier = Modifier.height(48.dp).semantics { testTag = "counter.continue" }) { Text("Continue") }
    }
}
