import SwiftUI

struct FoldBoard: View {
    let fixture: [String: Any]
    let onEvent: (String) -> Void
    @State private var opened = false
    var token: String { fixture["token"] as? String ?? "?" }
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(fixture["title"] as? String ?? "").font(.title2).accessibilityIdentifier("fold.title")
            Button("Locked action") { onEvent("locked:" + token) }
                .disabled(true).accessibilityIdentifier("fold.locked")
            if opened {
                Text("Expanded field remains open across caller replacement.")
                    .frame(maxWidth: .infinity, minHeight: 420, alignment: .topLeading)
                    .padding(.top, 12).background(Color.yellow.opacity(0.15))
                    .accessibilityIdentifier("fold.expansion")
            }
            Button(opened ? "Field opened" : "Open field") {
                opened = true
                onEvent("open:" + token)
            }.accessibilityIdentifier("fold.open")
            ForEach(0..<(fixture["count"] as? Int ?? 6), id: \.self) { index in
                Text("Section \(index + 1) of \(token). A neutral component has independent paragraphs that wrap naturally within the offered width. Continue through the field to inspect every section.")
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("fold.row.\(index)")
            }
            Button("Finish field " + token) { onEvent("finish:" + token) }
                .accessibilityIdentifier("fold.finish")
        }.frame(maxWidth: .infinity, alignment: .leading).foregroundColor(.black)
    }
}
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(FoldBoard(fixture: fixture, onEvent: onEvent))
    }
}
