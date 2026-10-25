import SwiftUI

/// Caller-owned copy for a single print collection request.
public struct CollectionAuthorizationData {
    public let requestID: String
    public let title: String
    public let jobSummary: String
    public let pickupWindow: String
    public let notesClosedTitle: String
    public let notesOpenTitle: String
    public let notesBody: String
    public let selfTitle: String
    public let selfDetail: String
    public let delegateTitle: String
    public let delegateDetail: String
    public let acknowledgement: String
    public let confirmTitle: String
    public let sentTitle: String
    public let readyMessage: String
    public let needsAcknowledgementMessage: String
    public let sentMessage: String
    public let delegateUnavailableMessage: String
    public let delegateAvailable: Bool

    public init(
        requestID: String, title: String, jobSummary: String, pickupWindow: String,
        notesClosedTitle: String, notesOpenTitle: String, notesBody: String,
        selfTitle: String, selfDetail: String, delegateTitle: String, delegateDetail: String,
        acknowledgement: String, confirmTitle: String, sentTitle: String,
        readyMessage: String, needsAcknowledgementMessage: String, sentMessage: String,
        delegateUnavailableMessage: String, delegateAvailable: Bool
    ) {
        self.requestID = requestID
        self.title = title
        self.jobSummary = jobSummary
        self.pickupWindow = pickupWindow
        self.notesClosedTitle = notesClosedTitle
        self.notesOpenTitle = notesOpenTitle
        self.notesBody = notesBody
        self.selfTitle = selfTitle
        self.selfDetail = selfDetail
        self.delegateTitle = delegateTitle
        self.delegateDetail = delegateDetail
        self.acknowledgement = acknowledgement
        self.confirmTitle = confirmTitle
        self.sentTitle = sentTitle
        self.readyMessage = readyMessage
        self.needsAcknowledgementMessage = needsAcknowledgementMessage
        self.sentMessage = sentMessage
        self.delegateUnavailableMessage = delegateUnavailableMessage
        self.delegateAvailable = delegateAvailable
    }
}

/// An intrinsically sized card. The caller owns scrolling and request replacement.
@available(iOS 14.0, macOS 11.0, *)
public struct CollectionAuthorizationCard: View {
    public let data: CollectionAuthorizationData
    private let onEvent: (String) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @State private var state: CollectionState
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var rowTitleSize: CGFloat = 16
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 15
    @ScaledMetric(relativeTo: .caption) private var metadataSize: CGFloat = 13

    public init(data: CollectionAuthorizationData, onEvent: @escaping (String) -> Void) {
        self.data = data
        self.onEvent = onEvent
        _state = State(initialValue: CollectionState(requestID: data.requestID))
    }

    // A replacement renders its initial state immediately, before onChange commits it.
    private var current: CollectionState {
        state.requestID == data.requestID ? state : CollectionState(requestID: data.requestID)
    }

    private var palette: CollectionPalette {
        colorScheme == .dark ? .dark : .light
    }

    private var valid: Bool {
        current.collector == .personal || (data.delegateAvailable && current.acknowledged)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: CollectionLayout.sectionGap) {
            VStack(alignment: .leading, spacing: CollectionLayout.textGap) {
                Text(data.title)
                    .font(.system(size: titleSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("collection.title")
                metadata(data.jobSummary, identifier: "collection.summary")
                metadata(data.pickupWindow, identifier: "collection.window")
            }

            choice(.personal, title: data.selfTitle, detail: data.selfDetail,
                   identifier: "collection.self", available: true)
            choice(.delegate, title: data.delegateTitle, detail: data.delegateDetail,
                   identifier: "collection.delegate", available: data.delegateAvailable)

            if !data.delegateAvailable {
                Text(data.delegateUnavailableMessage)
                    .font(.system(size: metadataSize, weight: .regular))
                    .foregroundColor(palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("collection.unavailable")
            }

            if current.collector == .delegate {
                Toggle(isOn: acknowledgementBinding) {
                    Text(data.acknowledgement)
                        .font(.system(size: bodySize, weight: .regular))
                        .foregroundColor(palette.ink)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .toggleStyle(SwitchToggleStyle(tint: palette.accent))
                .disabled(current.submitted || !data.delegateAvailable)
                .accessibilityIdentifier("collection.ack")
            }

            Text(current.submitted ? data.sentMessage :
                    (valid ? data.readyMessage : data.needsAcknowledgementMessage))
                .font(.system(size: bodySize, weight: .regular))
                .foregroundColor(palette.secondary)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("collection.status")

            Button(action: toggleNotes) {
                HStack(spacing: CollectionLayout.textGap) {
                    Text(current.notesExpanded ? data.notesOpenTitle : data.notesClosedTitle)
                        .font(.system(size: bodySize, weight: .semibold))
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer(minLength: 0)
                    Image(systemName: current.notesExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: metadataSize, weight: .semibold))
                        .accessibilityHidden(true)
                }
                .foregroundColor(palette.accent)
                .frame(maxWidth: .infinity, minHeight: CollectionLayout.disclosureMinHeight,
                       alignment: .leading)
                .contentShape(Rectangle())
            }
            .buttonStyle(CollectionButtonStyle())
            .accessibilityIdentifier("collection.notes")

            if current.notesExpanded {
                Text(data.notesBody)
                    .font(.system(size: bodySize, weight: .regular))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityIdentifier("collection.notesBody")
            }

            Button(action: submit) {
                Text(current.submitted ? data.sentTitle : data.confirmTitle)
                    .font(.system(size: bodySize, weight: .semibold))
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .foregroundColor(primaryEnabled ? palette.primaryInk : palette.disabledInk)
                    .padding(.horizontal, CollectionLayout.rowPadding)
                    .padding(.vertical, CollectionLayout.sectionGap)
                    .frame(maxWidth: .infinity, minHeight: CollectionLayout.primaryMinHeight)
                    .background(RoundedRectangle(cornerRadius: CollectionLayout.controlRadius)
                        .fill(primaryEnabled ? palette.accent : palette.neutralRow))
                    .contentShape(RoundedRectangle(cornerRadius: CollectionLayout.controlRadius))
            }
            .buttonStyle(CollectionButtonStyle())
            .disabled(!primaryEnabled)
            .accessibilityIdentifier("collection.confirm")
        }
        .multilineTextAlignment(.leading)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(CollectionLayout.cardPadding)
        .background(RoundedRectangle(cornerRadius: CollectionLayout.cardRadius).fill(palette.surface))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("collection.card")
        .onChange(of: data.requestID) { requestID in
            state = CollectionState(requestID: requestID)
        }
    }

    private var primaryEnabled: Bool { !current.submitted && valid }

    private func metadata(_ text: String, identifier: String) -> some View {
        Text(text)
            .font(.system(size: metadataSize, weight: .regular))
            .foregroundColor(palette.secondary)
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityIdentifier(identifier)
    }

    private func choice(_ collector: CollectionCollector, title: String, detail: String,
                        identifier: String, available: Bool) -> some View {
        let selected = current.collector == collector
        let enabled = !current.submitted && available
        return Button(action: { choose(collector) }) {
            HStack(alignment: .top, spacing: CollectionLayout.textGap) {
                VStack(alignment: .leading, spacing: CollectionLayout.textGap) {
                    Text(title)
                        .font(.system(size: rowTitleSize, weight: .semibold))
                        .foregroundColor(enabled ? palette.ink : palette.disabledInk)
                    Text(detail)
                        .font(.system(size: metadataSize, weight: .regular))
                        .foregroundColor(enabled ? palette.secondary : palette.disabledInk)
                }
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                Image(systemName: selected ? "largecircle.fill.circle" : "circle")
                    .font(.system(size: 20, weight: .regular))
                    .foregroundColor(enabled ? palette.accent : palette.disabledInk)
                    .frame(width: 24, height: 24)
                    .accessibilityHidden(true)
            }
            .padding(CollectionLayout.rowPadding)
            .frame(maxWidth: .infinity, minHeight: CollectionLayout.rowMinHeight, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: CollectionLayout.controlRadius)
                .fill(selected ? palette.selectedRow : palette.neutralRow))
            .overlay(RoundedRectangle(cornerRadius: CollectionLayout.controlRadius)
                .strokeBorder(selected ? palette.accent : Color.clear,
                              lineWidth: CollectionLayout.selectedBorderWidth))
            .contentShape(RoundedRectangle(cornerRadius: CollectionLayout.controlRadius))
        }
        .buttonStyle(CollectionButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text("\(title), \(detail)"))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier(identifier)
    }

    private func choose(_ collector: CollectionCollector) {
        var next = current
        guard !next.submitted, collector != next.collector,
              collector != .delegate || data.delegateAvailable else { return }
        next.collector = collector
        // Each newly chosen delegate requires a fresh acknowledgment.
        next.acknowledged = false
        state = next
        onEvent("collector:\(data.requestID):\(collector.rawValue)")
    }

    private var acknowledgementBinding: Binding<Bool> {
        Binding(get: { current.acknowledged }, set: { value in
            var next = current
            guard !next.submitted, next.collector == .delegate,
                  data.delegateAvailable, next.acknowledged != value else { return }
            next.acknowledged = value
            state = next
            onEvent("ack:\(data.requestID):\(value ? "true" : "false")")
        })
    }

    private func toggleNotes() {
        var next = current
        next.notesExpanded.toggle()
        state = next
        onEvent("notes:\(data.requestID):\(next.notesExpanded ? "open" : "closed")")
    }

    private func submit() {
        var next = current
        guard !next.submitted, valid else { return }
        next.submitted = true
        state = next
        onEvent("submit:\(data.requestID):\(next.collector.rawValue)")
    }
}

private enum CollectionCollector: String {
    case personal = "self"
    case delegate
}

private struct CollectionState {
    let requestID: String
    var collector: CollectionCollector = .personal
    var acknowledged = false
    var submitted = false
    var notesExpanded = false
}

private enum CollectionLayout {
    static let cardPadding: CGFloat = 20
    static let rowPadding: CGFloat = 16
    static let sectionGap: CGFloat = 12
    static let textGap: CGFloat = 8
    static let cardRadius: CGFloat = 20
    static let controlRadius: CGFloat = 12
    static let selectedBorderWidth: CGFloat = 1
    static let rowMinHeight: CGFloat = 80
    static let primaryMinHeight: CGFloat = 48
    static let disclosureMinHeight: CGFloat = 48
}

private struct CollectionButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

private struct CollectionPalette {
    let surface: Color
    let ink: Color
    let secondary: Color
    let neutralRow: Color
    let selectedRow: Color
    let accent: Color
    let disabledInk: Color
    let primaryInk: Color

    static let light = CollectionPalette(
        surface: color(0xFFFFFFFF), ink: color(0xFF172B3A), secondary: color(0xFF526675),
        neutralRow: color(0xFFF1F5F8), selectedRow: color(0xFFDFF3EE), accent: color(0xFF007F78),
        disabledInk: color(0xFF687C8A), primaryInk: color(0xFFFFFFFF)
    )
    static let dark = CollectionPalette(
        surface: color(0xFF142232), ink: color(0xFFF3F6FA), secondary: color(0xFFB6C7D5),
        neutralRow: color(0xFF223548), selectedRow: color(0xFF164C50), accent: color(0xFF4FD1C5),
        disabledInk: color(0xFF8DA4B5), primaryInk: color(0xFF102C30)
    )

    private static func color(_ argb: UInt32) -> Color {
        Color(.sRGB, red: Double((argb >> 16) & 0xFF) / 255,
              green: Double((argb >> 8) & 0xFF) / 255,
              blue: Double(argb & 0xFF) / 255, opacity: Double((argb >> 24) & 0xFF) / 255)
    }
}
