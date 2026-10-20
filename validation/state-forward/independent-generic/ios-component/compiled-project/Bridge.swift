import SwiftUI

// Public controlled component: content and selection come from its caller.
struct ReadingChecklist: View {
    let title: String
    let marked: Bool
    let enabled: Bool
    let onToggle: () -> Void
    private let ink = Color(red: 0.10, green: 0.16, blue: 0.17)
    private let teal = Color(red: 0.00, green: 0.39, blue: 0.40)

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(title).font(.system(size: 24, weight: .semibold))
                .accessibilityIdentifier("reading.title")
            Text(marked ? "Section six marked" : "Nothing marked")
                .font(.system(size: 16)).accessibilityIdentifier("reading.status")
            ForEach(1...12, id: \.self) { index in
                VStack(alignment: .leading, spacing: 8) {
                    Text("Section \(index)").font(.system(size: 18, weight: .semibold))
                    Text("Observe the shape of the path and note where it turns. Keep the description clear enough to revisit on another day.")
                        .font(.system(size: 15)).fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, minHeight: 92, alignment: .leading)
                .padding(12).background(Color(red: 0.90, green: 0.94, blue: 0.94))
                if index == 6 {
                    Button(action: onToggle) {
                        Text(marked ? "Clear mark" : "Mark section six")
                            .font(.system(size: 16, weight: .semibold))
                            .frame(maxWidth: .infinity, minHeight: 48)
                            .foregroundStyle(.white)
                            .background(enabled ? teal : Color.gray)
                    }
                    .buttonStyle(.plain).disabled(!enabled)
                    .accessibilityIdentifier("reading.toggle")
                    .accessibilityAddTraits(marked ? .isSelected : [])
                }
            }
            Text(marked ? "Selection: section six" : "Selection: none")
                .font(.system(size: 16)).accessibilityIdentifier("reading.footer")
        }
        .foregroundStyle(ink)
    }
}

private struct ReadingCaller: View {
    let fixture: [String: Any]
    let onEvent: (String) -> Void
    @State private var markedRevision: String? = nil
    var body: some View {
        let revision = fixture["revision"] as? String ?? ""
        let marked = markedRevision == revision
        ReadingChecklist(title: fixture["title"] as? String ?? "", marked: marked,
                         enabled: fixture["enabled"] as? Bool ?? false) {
            markedRevision = marked ? nil : revision
            onEvent("toggle-mark")
        }
    }
}

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(ReadingCaller(fixture: fixture, onEvent: onEvent))
    }
}
