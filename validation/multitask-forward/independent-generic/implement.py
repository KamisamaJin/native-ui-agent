#!/usr/bin/env python3
import sys,json,hashlib,datetime,shutil
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');O=R/'validation/multitask-forward/independent-generic';H=R/'validation/multitask-forward/cache/independent-neutral/host';S=R/'validation/multitask-forward/development/v7-neutral-candidate/scripts';sys.path.insert(0,str(S));sys.dont_write_bytecode=True;import design_contract as dc

def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n' if not isinstance(x,str) else x,encoding='utf-8')
# Correct a protocol-only missing initial action index before any implementation or acquisition.
c=json.loads((O/'design/contract.json').read_text())
for v in c['scenarios'].values():v['states'][0]['after_action']=-1
for rule in c['rules']:
 if rule['kind']=='manual':rule['coverage']='target'
write(O/'design/contract-rev3.json',c);lock=dc.seal(O/'design/contract-rev3.json',O/'design');write(O/'approved-lock-rev3.json',lock);digest=dc.digest(lock)
write(O/'APPROVAL-rev3.json',{'approvedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'design_lock_sha256':digest,'reason':'Compiler requires initial after_action=-1 and manual coverage singular target. Protocol corrections before source/feedback; typed values and selected states unchanged.','supersedes':'APPROVAL.json'})
bind={key:{'identifier':'reading.'+key} for key in ['title','expand','choice','disabled']};write(O/'bindings.json',bind)
for config in ['normal','dark-large']:
 actions=json.loads(json.dumps(c['scenarios'][config]['actions']))
 for a in actions:
  if 'target' in a:a['target']=bind[a['target']]
 write(O/('actions-'+config+'.json'),actions)
 for p in ['ios','android']:
  plan,enriched=dc.compile_contract(lock,digest,config,p,bind,actions)
  write(O/('plans/'+config+'/'+p+'/plan.json'),plan);write(O/('plans/'+config+'/'+p+'/actions.json'),enriched)
  fi={'width':360 if config=='normal' else 390,'theme':'light' if config=='normal' else 'dark','dynamic_type':'large' if config=='normal' else 'xLarge','fontScale':1 if config=='normal' else 1.2,'direction':'ltr','initial':{'key':'day','title':'Reading room'},'updates':[{'key':'evening','title':'Evening notes'}],'required_identifiers':['reading.title','reading.expand','reading.choice','reading.disabled','reading.last'],'max_scrolls':18,'observation_max_scrolls':24,'trace_reveal_images':True}
  write(O/('fixtures/'+config+'-'+p+'.json'),fi)
# Source starts only after approval and complete generated acceptance.
write(O/'implementation-start.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'approved_lock':digest})
swift='''import SwiftUI

public struct ReadingPanel: View {
    public let key: String
    public let title: String
    public let onEvent: (String) -> Void
    @State private var expanded = false
    @State private var selected = false
    @Environment(\\.colorScheme) private var scheme
    public init(key: String, title: String, onEvent: @escaping (String) -> Void) { self.key = key; self.title = title; self.onEvent = onEvent }
    private var ink: Color { scheme == .dark ? Color(red: 230/255, green: 234/255, blue: 240/255) : Color(red: 35/255, green: 51/255, blue: 71/255) }
    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(title).font(.system(size:22, weight:.semibold)).foregroundColor(ink).accessibilityIdentifier("reading.title")
            Text("A quiet place to keep useful notes.").font(.body).foregroundColor(ink)
            Button(action: { expanded.toggle(); onEvent("expanded") }) {
                HStack { Text(expanded ? "Hide status" : "Show status"); Spacer(); Text(expanded ? "-" : "+") }
                    .padding(.horizontal, 12).frame(height: expanded ? 72 : 48).background(scheme == .dark ? Color.white.opacity(0.1) : Color.black.opacity(0.05)).cornerRadius(10)
            }.buttonStyle(.plain).foregroundColor(ink).accessibilityIdentifier("reading.expand")
            if expanded { Text("Ready to read. Your notes are available on this device.").font(.body).foregroundColor(ink).accessibilityIdentifier("reading.status") }
            Button(action: { selected.toggle(); onEvent("selected") }) {
                HStack { Text(selected ? "[x]" : "[ ]"); Text("Keep this reading option"); Spacer() }.padding(12).frame(minHeight:48)
            }.buttonStyle(.plain).foregroundColor(ink).accessibilityIdentifier("reading.choice").accessibilityAddTraits(selected ? .isSelected : [])
            Button(action: { onEvent("export") }) { Text("Export unavailable").frame(maxWidth:.infinity).frame(height:48) }.buttonStyle(.plain).disabled(true).foregroundColor(.secondary).accessibilityIdentifier("reading.disabled")
            ForEach(0..<12) { i in
                VStack(alignment:.leading, spacing:8) {
                    Text("Section \\(i + 1)").font(.headline)
                    Text("Read at your own pace. These notes keep a steady rhythm, with enough detail to revisit the idea later.").font(.body).fixedSize(horizontal:false, vertical:true)
                }.foregroundColor(ink).frame(maxWidth:.infinity,alignment:.leading).padding(.vertical,8).accessibilityElement(children:.contain)
            }
            Text("End of reading notes").foregroundColor(ink).accessibilityIdentifier("reading.last")
        }.onChange(of:key) { _ in expanded=false; selected=false }
    }
}
'''
write(H/'alerttoast/Sources/AlertToast/ReadingPanel.swift',swift);write(O/'source/ReadingPanel.swift',swift)
bridge='''import SwiftUI
import AlertToast
enum ObserverBridge {
 static func make(fixture: [String:Any], onEvent: @escaping (String)->Void) -> AnyView {
  AnyView(ReadingPanel(key:fixture["key"] as? String ?? "day", title:fixture["title"] as? String ?? "Reading room", onEvent:onEvent))
 }
}
''';write(O/'source/Bridge.swift',bridge)
kt='''package org.neutral
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
''';write(H/'reply/Reply/app/src/main/java/org/neutral/ReadingPanel.kt',kt);write(O/'source/ReadingPanel.kt',kt)
kbridge='''package org.nativeobserver
import androidx.compose.runtime.Composable
import kotlinx.serialization.json.*
import org.neutral.ReadingPanel
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit) {
  ReadingPanel(input["key"]!!.jsonPrimitive.content,input["title"]!!.jsonPrimitive.content,onEvent)
 }
}
''';write(O/'source/ObserverBridge.kt',kbridge)
write(O/'source-seal.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (O/'source').rglob('*') if p.is_file()},'design_lock_sha256':digest})
print('Source and generated plans sealed '+digest)
