import SwiftUI

// Self-contained production component for this neutral forward test.
// The bridge only decodes caller values and forwards the component's real event.
enum ObserverBridge {
    static func make(fixture: [String: Any],
                     onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(NeutralNotesPanel(model: NotesInput(fixture), onReview: onEvent))
    }
}

private struct NotesSection: Identifiable {
    let number: Int
    let title: String
    let body: String
    var id: Int { number }
    var heading: String { String(format: "%02d", number) + " · " + title }
}

private struct NotesInput {
    let title: String
    let summary: String
    let revision: String
    let canReview: Bool
    let sections: [NotesSection]

    init(_ fixture: [String: Any]) {
        title = fixture["title"] as? String ?? ""
        summary = fixture["summary"] as? String ?? ""
        revision = fixture["revision"] as? String ?? ""
        canReview = fixture["can_review"] as? Bool ?? false
        sections = (fixture["sections"] as? [[String: Any]] ?? []).map {
            NotesSection(number: $0["number"] as? Int ?? 0,
                         title: $0["title"] as? String ?? "",
                         body: $0["body"] as? String ?? "")
        }
    }
}

private enum NotesPalette {
    static let main = Color(red: 23.0 / 255, green: 33.0 / 255, blue: 43.0 / 255)
    static let secondary = Color(red: 67.0 / 255, green: 81.0 / 255, blue: 94.0 / 255)
    static let surface = Color(red: 244.0 / 255, green: 246.0 / 255, blue: 248.0 / 255)
    static let action = Color(red: 38.0 / 255, green: 55.0 / 255, blue: 70.0 / 255)
    static let disabled = Color(red: 220.0 / 255, green: 226.0 / 255, blue: 231.0 / 255)
    static let disabledText = Color(red: 85.0 / 255, green: 97.0 / 255, blue: 108.0 / 255)
}

private struct NeutralNotesPanel: View {
    let model: NotesInput
    let onReview: (String) -> Void
    @State private var reviewCount = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text(model.title)
                .font(.title2.weight(.semibold))
                .foregroundStyle(NotesPalette.main)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("notes.title")
            Text(model.summary)
                .font(.body)
                .foregroundStyle(NotesPalette.secondary)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("notes.summary")
            Text("Input revision: \(model.revision)")
                .font(.subheadline)
                .foregroundStyle(NotesPalette.secondary)
                .accessibilityIdentifier("notes.revision")
            Text("Review count: \(reviewCount)")
                .font(.headline)
                .foregroundStyle(NotesPalette.main)
                .accessibilityIdentifier("notes.status")

            ForEach(model.sections) { section in
                card(section)
                if section.number == 6 {
                    reviewAction
                }
            }

            Text("End note: revision \(model.revision); review count \(reviewCount)")
                .font(.subheadline)
                .foregroundStyle(NotesPalette.secondary)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.vertical, 12)
                .accessibilityIdentifier("notes.footer")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func card(_ section: NotesSection) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(section.heading)
                .font(.headline)
                .foregroundStyle(NotesPalette.main)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier(headingIdentifier(section.number))
            Text(section.body)
                .font(.body)
                .foregroundStyle(NotesPalette.secondary)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("notes.body.\(section.number)")
        }
        .padding(16)
        .frame(maxWidth: .infinity, minHeight: 180, alignment: .topLeading)
        .background(NotesPalette.surface, in: RoundedRectangle(cornerRadius: 12))
    }

    private var reviewAction: some View {
        Button {
            reviewCount += 1
            onReview("notes.reviewed.\(model.revision)")
        } label: {
            Text(reviewCount == 0 ? "Mark notes reviewed" : "Review marked")
                .font(.headline)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, minHeight: 52)
                .foregroundStyle(model.canReview ? Color.white : NotesPalette.disabledText)
                .background(model.canReview ? NotesPalette.action : NotesPalette.disabled,
                            in: RoundedRectangle(cornerRadius: 12))
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(!model.canReview)
        .accessibilityIdentifier("notes.action")
    }

    private func headingIdentifier(_ number: Int) -> String {
        switch number {
        case 1: return "notes.opening"
        case 5: return "notes.middle"
        case 10: return "notes.closing"
        default: return "notes.heading.\(number)"
        }
    }
}
