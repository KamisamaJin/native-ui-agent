import SwiftUI
private func rgb(_ value:UInt32)->Color { Color(red:Double((value>>16)&255)/255,green:Double((value>>8)&255)/255,blue:Double(value&255)/255) }
enum ObserverBridge {
 static func make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView {
  let changed=fixture["phase"] as? String == "B"
  return AnyView(VStack(alignment:.leading,spacing:16) {
   Text("Atomic color sample").font(.headline).accessibilityIdentifier("probe.title")
   Button(action:{onEvent("tone")}) { Text("Tone").font(.system(size:15)).foregroundColor(.white).frame(width:96,height:56).background(rgb(changed ? 0x976038:0x397A91)) }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("probe.tile")
   ForEach(0..<14,id:\.self) { i in Text("Neutral note \(i): a short observation line that can wrap with larger text.").font(.body).frame(maxWidth:.infinity,alignment:.leading) }
  }.padding(12).frame(maxWidth:.infinity,alignment:.leading).background(rgb(changed ? 0xECE2D1:0xD6E8F3)).accessibilityElement(children:.contain).accessibilityIdentifier("probe.canvas"))
 }
}
