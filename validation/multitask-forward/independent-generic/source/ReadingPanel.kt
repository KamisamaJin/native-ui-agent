package org.neutral
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable fun ReadingPanel(key: String, title: String, onEvent:(String)->Unit) {
 var expanded by remember(key) { mutableStateOf(false) }
 var selected by remember(key) { mutableStateOf(false) }
 val dark = MaterialTheme.colorScheme.background.red < 0.5f
 val ink = if(dark) Color(0xFFE6EAF0) else Color(0xFF233347)
 Column(Modifier.fillMaxWidth(), verticalArrangement=Arrangement.spacedBy(16.dp)) {
  Text(title, color=ink, fontSize=22.sp, fontWeight=FontWeight.SemiBold, modifier=Modifier.testTag("reading.title"))
  Text("A quiet place to keep useful notes.",color=ink)
  Row(Modifier.fillMaxWidth().height(if(expanded)72.dp else 48.dp).background(if(dark)Color(0xFF29323D) else Color(0xFFF0F2F4)).clickable(role=Role.Button) {expanded=!expanded;onEvent("expanded")}.testTag("reading.expand").padding(horizontal=12.dp), verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
   Text(if(expanded) "Hide status" else "Show status",color=ink);Spacer(Modifier.weight(1f));Text(if(expanded) "-" else "+",color=ink)
  }
  if(expanded)Text("Ready to read. Your notes are available on this device.",color=ink,modifier=Modifier.testTag("reading.status"))
  Row(Modifier.fillMaxWidth().heightIn(min=48.dp).selectable(selected=selected,role=Role.RadioButton) {selected=!selected;onEvent("selected")}.testTag("reading.choice").padding(12.dp)) {
   Text(if(selected) "[x]  Keep this reading option" else "[ ]  Keep this reading option",color=ink)
  }
  Text("Export unavailable", color=Color.Gray, modifier=Modifier.fillMaxWidth().height(48.dp).clickable(enabled=false,role=Role.Button){onEvent("export")}.testTag("reading.disabled").padding(12.dp))
  repeat(12) { i ->
   Column(Modifier.fillMaxWidth().padding(vertical=8.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
    Text("Section ${i+1}",color=ink,fontWeight=FontWeight.SemiBold)
    Text("Read at your own pace. These notes keep a steady rhythm, with enough detail to revisit the idea later.",color=ink)
   }
  }
  Text("End of reading notes",color=ink,modifier=Modifier.testTag("reading.last"))
 }
}
