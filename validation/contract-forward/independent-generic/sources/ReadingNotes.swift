import SwiftUI

public struct ReadingNotes: View {
 public let title: String
 public let footer: String
 public let prefix: String
 public let onOpen: () -> Void
 @State private var open = false
 private let ink = Color(red:32/255,green:75/255,blue:109/255)
 public init(title:String,footer:String,prefix:String,onOpen:@escaping()->Void) {
  self.title=title;self.footer=footer;self.prefix=prefix;self.onOpen=onOpen
 }
 public var body: some View {
  VStack(alignment:.leading,spacing:16) {
   Text(title).font(.system(size:26,weight:.semibold)).foregroundStyle(ink).accessibilityIdentifier("reading.heading")
   Text("A calm place to review one observation at a time.").font(.system(size:16)).foregroundStyle(ink).accessibilityIdentifier("reading.ink")
   HStack(spacing:12) {
    marker("Focus",identifier:"reading.markerA")
    marker("Notes",identifier:"reading.markerB")
   }
   Button {
    if !open { open=true; onOpen() }
   } label: {
    Text(open ? "Notes open" : "Open notes").font(.system(size:16,weight:.medium)).frame(maxWidth:.infinity).frame(height:48)
   }.buttonStyle(.plain).foregroundStyle(Color.white).background(ink).clipShape(RoundedRectangle(cornerRadius:12)).accessibilityIdentifier("reading.disclosure")
   Text(open ? "Notes open" : "Notes closed").font(.system(size:14,weight:.medium)).foregroundStyle(ink).accessibilityIdentifier("reading.status")
   ForEach(0..<12) { index in
    VStack(alignment:.leading,spacing:6) {
     Text("\(prefix) \(index+1)").font(.system(size:16,weight:.semibold)).foregroundStyle(ink)
     Text("Read the whole line, pause briefly, and leave room for a thoughtful response.").font(.system(size:14)).foregroundStyle(Color(red:65/255,green:81/255,blue:97/255))
    }.frame(maxWidth:.infinity,minHeight:80,alignment:.leading).padding(.horizontal,12).background(Color.white).clipShape(RoundedRectangle(cornerRadius:10)).accessibilityIdentifier("reading.row.\(index)")
   }
   Text(footer).font(.system(size:16,weight:.semibold)).foregroundStyle(ink).padding(.vertical,12).accessibilityIdentifier("reading.footer")
  }.frame(maxWidth:.infinity,alignment:.leading)
 }
 private func marker(_ title:String,identifier:String)->some View {
  Text(title).font(.system(size:14,weight:.medium)).foregroundStyle(ink).frame(width:72,height:32).background(Color(red:221/255,green:234/255,blue:244/255)).clipShape(RoundedRectangle(cornerRadius:8)).accessibilityElement(children:.ignore).accessibilityLabel(title).accessibilityIdentifier(identifier)
 }
}
