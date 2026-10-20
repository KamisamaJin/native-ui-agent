import SwiftUI
import AlertToast
enum ObserverBridge {
 static func make(fixture: [String:Any], onEvent: @escaping (String)->Void) -> AnyView {
  AnyView(ReadingPanel(key:fixture["key"] as? String ?? "day", title:fixture["title"] as? String ?? "Reading room", onEvent:onEvent))
 }
}
