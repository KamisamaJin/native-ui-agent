import SwiftUI

enum ObserverBridge {
 static func make(fixture: [String:Any], onEvent: @escaping (String)->Void)->AnyView {
  AnyView(VStack(alignment:.leading,spacing:12) {
   Text(fixture["title"] as? String ?? "Probe").accessibilityIdentifier("cap.title")
   Button("Primary probe") { onEvent("cap.primary") }.frame(height:48).accessibilityIdentifier("cap.primary")
   ForEach(0..<8) { i in Text("Capability row \(i+1)").frame(maxWidth:.infinity,minHeight:70,alignment:.leading) }
   Button("Last probe") { onEvent("cap.last") }.frame(height:48).accessibilityIdentifier("cap.last")
  })
 }
}
