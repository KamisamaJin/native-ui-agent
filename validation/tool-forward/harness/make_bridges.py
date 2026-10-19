#!/usr/bin/env python3
"""Generate thin model decoders from the frozen PUBLIC API table; no UI or oracle."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent
brief=(R.parent/'design/size-revision/public/brief.md').read_text()
types={name:[(k,t)for k,t in re.findall(r'(\w+): ([A-Za-z<>?]+)',props)]for name,props in re.findall(r'\| `(ReturnResolution\w+)` \| `([^\n]+)` \|',brief)}
# The public table separates property code spans with commas.
types={}
for line in brief.splitlines():
 m=re.match(r'\| `(ReturnResolution\w+)` \| (.+) \|$',line)
 if m:types[m[1]]=re.findall(r'`(\w+): ([A-Za-z<>?]+)`',m[2])
assert len(types)==8 and len(types['ReturnResolutionModel'])==32,(len(types),types.get('ReturnResolutionModel'))
enums={'ReturnResolutionStatus','ReturnResolutionKind','ReturnResolutionAccent'}
def swexpr(key,t):
 null=t.endswith('?');t=t.rstrip('?');v=f'o["{key}"]'
 if t.startswith('List<'):
  item=t[5:-1]
  return f'({v} as? [String] ?? [])'if item=='String'else f'({v} as? [[String:Any]] ?? []).map {{ decode{item}($0) }}'
 if t=='String':return f'{v} as? String'+(''if null else' ?? ""')
 if t=='Bool':return f'{v} as? Bool ?? false'
 if t in enums:return f'["editing": {t}.editing, "submitting": .submitting, "complete": .complete][{v} as! String]!' if t=='ReturnResolutionStatus' else f'["refund": {t}.refund, "credit": .credit, "exchange": .exchange][{v} as! String]!' if t=='ReturnResolutionKind' else f'["teal": {t}.teal, "coral": .coral, "indigo": .indigo][{v} as! String]!'
 if null:return f'({v} as? [String:Any]).map {{ decode{t}($0) }}'
 return f'decode{t}({v} as! [String:Any])'
def ktexpr(key,t):
 null=t.endswith('?');t=t.rstrip('?');v=f'o["{key}"]'
 if t.startswith('List<'):
  item=t[5:-1]
  return f'{v}!!.jsonArray.map {{ it.jsonPrimitive.content }}'if item=='String'else f'{v}!!.jsonArray.map {{ decode{item}(it.jsonObject) }}'
 if t=='String':return f'{v}?.jsonPrimitive?.contentOrNull'if null else f'{v}!!.jsonPrimitive.content'
 if t=='Bool':return f'{v}!!.jsonPrimitive.boolean'
 if t in enums:return f'{t}.valueOf({v}!!.jsonPrimitive.content.uppercase())'
 if null:return f'{v}?.takeUnless {{ it is JsonNull }}?.jsonObject?.let {{ decode{t}(it) }}'
 return f'decode{t}({v}!!.jsonObject)'
sw='import SwiftUI\nimport AlertToast\nimport Foundation\n\n'
for name,fields in types.items():sw+=f'private func decode{name}(_ o:[String:Any]) -> {name} {{\n {name}(\n'+',\n'.join(f'  {k}: {swexpr(k,t)}'for k,t in fields)+'\n )\n}\n'
sw+='''private func event(_ a:ReturnResolutionAction)->String {
 var o:[String:Any]=[:]
 switch a {
 case let .selectOption(optionId): o=["type":"selectOption","optionId":optionId]
 case let .selectSize(sizeId): o=["type":"selectSize","sizeId":sizeId]
 case let .setAcknowledgement(accepted): o=["type":"setAcknowledgement","accepted":accepted]
 case let .setNotesExpanded(expanded): o=["type":"setNotesExpanded","expanded":expanded]
 case let .submit(optionId,sizeId,acknowledgementAccepted): o=["type":"submit","optionId":optionId,"sizeId":sizeId.map { $0 as Any } ?? NSNull(),"acknowledgementAccepted":acknowledgementAccepted]
 case .keepPurchase: o=["type":"keepPurchase"]
 case .done: o=["type":"done"]
 }
 return String(data:try! JSONSerialization.data(withJSONObject:o,options:[.sortedKeys]),encoding:.utf8)!
}
enum ObserverBridge {
 static func make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView {
  AnyView(ReturnResolutionCard(model:decodeReturnResolutionModel(fixture["model"] as! [String:Any]),onAction:{onEvent(event($0))}))
 }
}
'''
(R/'ReturnBridge.swift').write_text(sw)
kt='''package org.nativeobserver
import androidx.compose.runtime.Composable
import androidx.compose.material3.*
import androidx.compose.foundation.isSystemInDarkTheme
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*
'''
for name,fields in types.items():kt+=f'private fun decode{name}(o:JsonObject)={name}(\n'+',\n'.join(f' {k}={ktexpr(k,t)}'for k,t in fields)+'\n)\n'
kt+='''private fun event(a:ReturnResolutionAction):String=buildJsonObject{
 when(a){
 is ReturnResolutionAction.SelectOption->{put("type","selectOption");put("optionId",a.optionId)}
 is ReturnResolutionAction.SelectSize->{put("type","selectSize");put("sizeId",a.sizeId)}
 is ReturnResolutionAction.SetAcknowledgement->{put("type","setAcknowledgement");put("accepted",a.accepted)}
 is ReturnResolutionAction.SetNotesExpanded->{put("type","setNotesExpanded");put("expanded",a.expanded)}
 is ReturnResolutionAction.Submit->{put("type","submit");put("optionId",a.optionId);put("sizeId",a.sizeId?.let{JsonPrimitive(it)} ?: JsonNull);put("acknowledgementAccepted",a.acknowledgementAccepted)}
 ReturnResolutionAction.KeepPurchase->put("type","keepPurchase")
 ReturnResolutionAction.Done->put("type","done")
 }
}.toString()
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit){
  MaterialTheme(colorScheme=if(isSystemInDarkTheme())darkColorScheme()else lightColorScheme()){
   ReturnResolutionCard(model=decodeReturnResolutionModel(input["model"]!!.jsonObject),onAction={onEvent(event(it))})
  }
 }
}
'''
(R/'ObserverBridge.kt').write_text(kt)
print('Generated public-API-only bridge decoders',len(types))
