import SwiftUI
enum ObserverBridge {
 static func make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView {
  AnyView(NeutralPanel(rows:fixture["rows"] as? Int ?? 16, base:fixture["height"] as? Int ?? 52, title:fixture["title"] as? String ?? "A",onEvent:onEvent))
 }
}
private struct NeutralPanel:View {
 let rows:Int;let base:Int;let title:String;let onEvent:(String)->Void
 @State private var expanded=false
 private func cell(_ label:String,_ id:String,_ action:@escaping()->Void)->some View {
  Button(action:action){Text(label).font(.system(size:14)).frame(width:84,height:CGFloat(base+(expanded ? 16:0))).background(Color.blue.opacity(0.2)).contentShape(Rectangle())}.buttonStyle(PlainButtonStyle()).accessibilityIdentifier(id)
 }
 var body:some View {
  VStack(alignment:.leading,spacing:12){
   Text("Measurements \(title)").accessibilityIdentifier("neutral.header")
   HStack(spacing:12){cell("Go","neutral.primary"){expanded.toggle();onEvent("expanded")};cell("Next","neutral.secondary"){onEvent("secondary")}}
   ForEach(0..<rows,id:\.self){n in Text("Neutral section \(n)").frame(minHeight:40)}
   cell("End","neutral.footer"){onEvent("footer")}
  }
 }
}
