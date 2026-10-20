import SwiftUI

public struct ReadingPanel: View {
    public let key: String
    public let title: String
    public let onEvent: (String) -> Void
    @State private var expanded = false
    @State private var selected = false
    @Environment(\.colorScheme) private var scheme
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
                    Text("Section \(i + 1)").font(.headline)
                    Text("Read at your own pace. These notes keep a steady rhythm, with enough detail to revisit the idea later.").font(.body).fixedSize(horizontal:false, vertical:true)
                }.foregroundColor(ink).frame(maxWidth:.infinity,alignment:.leading).padding(.vertical,8).accessibilityElement(children:.contain)
            }
            Text("End of reading notes").foregroundColor(ink).accessibilityIdentifier("reading.last")
        }.onChange(of:key) { _ in expanded=false; selected=false }
    }
}
