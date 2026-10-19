import SwiftUI
enum ObserverBridge {
 static func make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView { AnyView(VStack(alignment:.leading,spacing:16){
  Button(action:{onEvent("outer")}) { VStack { Text("Outer action"); Button("Inner action"){onEvent("inner")} } }.accessibilityIdentifier("nested")
  Button("Disabled"){onEvent("disabled")}.disabled(true).accessibilityIdentifier("disabled")
  Text("Tall non-control content").frame(height:720).accessibilityIdentifier("tall.text")
  Text("Static lower heading").accessibilityIdentifier("lower.heading")
  Button("Lower enabled action"){onEvent("lower")}.frame(maxWidth:.infinity).frame(height:48).accessibilityIdentifier("lower.button")
 }) }
}
