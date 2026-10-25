import SwiftUI

public struct ListeningBreakOption: Equatable {
    public let id: String
    public let title: String
    public let detail: String
    public let isAvailable: Bool

    public init(id: String, title: String, detail: String, isAvailable: Bool) {
        self.id = id
        self.title = title
        self.detail = detail
        self.isAvailable = isAvailable
    }
}

public struct ListeningBreakInput: Equatable {
    public let sessionID: String
    public let title: String
    public let introduction: String
    public let options: [ListeningBreakOption]
    public let quietNote: String
    public let footer: String

    public init(sessionID: String, title: String, introduction: String,
                options: [ListeningBreakOption], quietNote: String, footer: String) {
        self.sessionID = sessionID
        self.title = title
        self.introduction = introduction
        self.options = options
        self.quietNote = quietNote
        self.footer = footer
    }
}

public struct ListeningBreakPanel: View {
    private let input: ListeningBreakInput
    private let onStart: (String, String) -> Void
    private let onCancel: (String) -> Void

    public init(input: ListeningBreakInput,
                onStart: @escaping (String, String) -> Void,
                onCancel: @escaping (String) -> Void) {
        self.input = input
        self.onStart = onStart
        self.onCancel = onCancel
    }

    public var body: some View {
        // The stateful child belongs to the complete input value. This resets it
        // before new copy is rendered, while equal input preserves its state.
        ListeningBreakContent(input: input, onStart: onStart, onCancel: onCancel)
            .id(ListeningBreakIdentity(input: input))
    }
}

private struct ListeningBreakIdentity: Hashable {
    let input: ListeningBreakInput

    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.input == rhs.input
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(input.sessionID)
        hasher.combine(input.title)
        hasher.combine(input.introduction)
        hasher.combine(input.options.count)
        for option in input.options {
            hasher.combine(option.id)
            hasher.combine(option.title)
            hasher.combine(option.detail)
            hasher.combine(option.isAvailable)
        }
        hasher.combine(input.quietNote)
        hasher.combine(input.footer)
    }
}

private struct ListeningBreakContent: View {
    let input: ListeningBreakInput
    let onStart: (String, String) -> Void
    let onCancel: (String) -> Void

    @State private var selectedID: String?
    @State private var acknowledged = false
    @State private var started = false
    @State private var error: String?

    @ScaledMetric(relativeTo: .body) private var titleSize: CGFloat = 24
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .body) private var detailSize: CGFloat = 14

    private var selectedOption: ListeningBreakOption? {
        input.options.first { $0.id == selectedID && $0.isAvailable }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            copy(input.title, size: titleSize, color: ListeningBreakColors.title,
                 weight: .semibold)
                .accessibilityIdentifier("listening.title")

            copy(input.introduction, size: bodySize, color: ListeningBreakColors.body)
                .accessibilityIdentifier("listening.introduction")

            ForEach(input.options, id: \.id) { option in
                optionButton(option)
            }

            copy(input.quietNote, size: bodySize, color: ListeningBreakColors.body)
                .accessibilityIdentifier("listening.note")

            Toggle(isOn: Binding(
                get: { acknowledged },
                set: { value in
                    guard !started else { return }
                    acknowledged = value
                    error = nil
                }
            )) {
                copy("I have read the quiet-space note", size: bodySize,
                     color: ListeningBreakColors.body)
            }
            .toggleStyle(SwitchToggleStyle(tint: ListeningBreakColors.primary))
            .disabled(started)
            .accessibilityIdentifier("listening.acknowledge")

            copy(started ? "Your listening break is ready." : "Choose a soundscape for your break.",
                 size: bodySize, color: ListeningBreakColors.body)
                .accessibilityIdentifier("listening.status")

            if let error = error {
                copy(error, size: bodySize, color: ListeningBreakColors.error)
                    .accessibilityIdentifier("listening.error")
            }

            if started, let option = selectedOption {
                copy("Ready to begin: " + option.title, size: bodySize,
                     color: ListeningBreakColors.body)
                    .accessibilityIdentifier("listening.summary")
            }

            Button(action: primaryAction) {
                actionLabel(started ? "Choose again" : "Start listening",
                            ink: ListeningBreakColors.primaryInk,
                            fill: ListeningBreakColors.primary)
            }
            .buttonStyle(ListeningBreakButtonStyle())
            .accessibilityIdentifier("listening.primary")

            Button(action: {
                reset()
                onCancel(input.sessionID)
            }) {
                actionLabel("Cancel", ink: ListeningBreakColors.body,
                            fill: ListeningBreakColors.canvas)
            }
            .buttonStyle(ListeningBreakButtonStyle())
            .accessibilityIdentifier("listening.cancel")

            copy(input.footer, size: detailSize, color: ListeningBreakColors.muted)
                .accessibilityIdentifier("listening.footer")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(ListeningBreakColors.canvas)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("listening.canvas")
    }

    private func copy(_ value: String, size: CGFloat, color: Color,
                      weight: Font.Weight = .regular) -> some View {
        Text(verbatim: value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color)
            .multilineTextAlignment(.leading)
            .lineLimit(nil)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func optionButton(_ option: ListeningBreakOption) -> some View {
        let selected = selectedID == option.id
        let fill = !option.isAvailable ? ListeningBreakColors.unavailableOption
            : selected ? ListeningBreakColors.selectedOption : ListeningBreakColors.option

        return Button(action: {
            guard !started && option.isAvailable else { return }
            selectedID = option.id
            error = nil
        }) {
            VStack(alignment: .leading, spacing: 4) {
                copy(option.title, size: bodySize,
                     color: option.isAvailable ? ListeningBreakColors.body : ListeningBreakColors.muted,
                     weight: .semibold)
                copy(option.detail, size: detailSize, color: ListeningBreakColors.muted)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .frame(minHeight: 64, alignment: .leading)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 12, style: .circular).fill(fill))
            .overlay(RoundedRectangle(cornerRadius: 12, style: .circular)
                .strokeBorder(ListeningBreakColors.border, lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 12, style: .circular))
        }
        .buttonStyle(ListeningBreakButtonStyle())
        .disabled(started || !option.isAvailable)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(verbatim: option.title + " — " + option.detail))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("listening.option." + option.id)
    }

    private func actionLabel(_ value: String, ink: Color, fill: Color) -> some View {
        copy(value, size: bodySize, color: ink, weight: .semibold)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .frame(minWidth: 120, minHeight: 48, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 12, style: .circular).fill(fill))
            .contentShape(RoundedRectangle(cornerRadius: 12, style: .circular))
    }

    private func primaryAction() {
        if started {
            reset()
            return
        }

        guard let option = selectedOption else {
            error = acknowledged ? "Choose an available soundscape."
                : "Choose a soundscape and confirm the quiet-space note."
            return
        }
        guard acknowledged else {
            error = "Confirm the quiet-space note before starting."
            return
        }

        error = nil
        started = true
        onStart(input.sessionID, option.id)
    }

    private func reset() {
        selectedID = nil
        acknowledged = false
        error = nil
        started = false
    }
}

private struct ListeningBreakButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

private enum ListeningBreakColors {
    static let canvas = Color(.sRGB, red: 242 / 255, green: 246 / 255, blue: 244 / 255, opacity: 1)
    static let option = Color(.sRGB, red: 1, green: 1, blue: 1, opacity: 1)
    static let selectedOption = Color(.sRGB, red: 232 / 255, green: 243 / 255, blue: 239 / 255, opacity: 1)
    static let unavailableOption = Color(.sRGB, red: 240 / 255, green: 242 / 255, blue: 241 / 255, opacity: 1)
    static let primary = Color(.sRGB, red: 23 / 255, green: 107 / 255, blue: 88 / 255, opacity: 1)
    static let primaryInk = Color(.sRGB, red: 1, green: 1, blue: 1, opacity: 1)
    static let title = Color(.sRGB, red: 23 / 255, green: 47 / 255, blue: 42 / 255, opacity: 1)
    static let body = Color(.sRGB, red: 56 / 255, green: 86 / 255, blue: 78 / 255, opacity: 1)
    static let muted = Color(.sRGB, red: 104 / 255, green: 122 / 255, blue: 117 / 255, opacity: 1)
    static let error = Color(.sRGB, red: 176 / 255, green: 56 / 255, blue: 44 / 255, opacity: 1)
    static let border = Color(.sRGB, red: 171 / 255, green: 198 / 255, blue: 188 / 255, opacity: 1)
}
