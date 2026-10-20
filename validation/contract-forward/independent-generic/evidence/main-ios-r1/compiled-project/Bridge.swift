import SwiftUI
import ReadingNotes

enum ObserverBridge {
 static func make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView {
  AnyView(ReadingNotes(title:fixture["title"] as? String ?? "",footer:fixture["footer"] as? String ?? "",prefix:fixture["prefix"] as? String ?? "",onOpen:{onEvent("notes.open")}))
 }
}
