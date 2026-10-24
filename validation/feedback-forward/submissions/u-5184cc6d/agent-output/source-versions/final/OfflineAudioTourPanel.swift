import SwiftUI

/// A chapter supplied by the audio-tour caller.
public struct AudioTourChapter: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let body: String

    public init(id: String, title: String, body: String) {
        self.id = id
        self.title = title
        self.body = body
    }
}

/// Whole decimal MB quantities and connection information are supplied by the caller.
public struct OfflineAudioTour: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let language: String
    public let downloadSizeMB: Int
    public let availableMB: Int
    public let meteredConnection: Bool
    public let chapters: [AudioTourChapter]

    public init(id: String, title: String, language: String, downloadSizeMB: Int,
                availableMB: Int, meteredConnection: Bool, chapters: [AudioTourChapter]) {
        self.id = id
        self.title = title
        self.language = language
        self.downloadSizeMB = downloadSizeMB
        self.availableMB = availableMB
        self.meteredConnection = meteredConnection
        self.chapters = chapters
    }
}

/// Records a download request. Scrolling and the actual download belong to the caller.
public struct OfflineAudioTourPanel: View {
    private let tour: OfflineAudioTour
    private let onWifiOnlyChange: (Bool) -> Void
    private let onDownload: (String, Bool) -> Void

    public init(tour: OfflineAudioTour, onWifiOnlyChange: @escaping (Bool) -> Void,
                onDownload: @escaping (String, Bool) -> Void) {
        self.tour = tour
        self.onWifiOnlyChange = onWifiOnlyChange
        self.onDownload = onDownload
    }

    public var body: some View {
        // Identity is owned here, so replacing the model resets all three local
        // preferences together without running any of the caller's callbacks.
        AudioTourPanelContent(tour: tour, onWifiOnlyChange: onWifiOnlyChange,
                              onDownload: onDownload)
            .id(tour.id)
    }
}

private struct AudioTourPanelContent: View {
    let tour: OfflineAudioTour
    let onWifiOnlyChange: (Bool) -> Void
    let onDownload: (String, Bool) -> Void

    @State private var chaptersOpen = false
    @State private var wifiOnly = true
    @State private var requested = false

    private var canDownload: Bool {
        tour.availableMB >= tour.downloadSizeMB &&
            !(tour.meteredConnection && wifiOnly) && !requested
    }

    private var status: AudioTourStatus {
        if tour.availableMB < tour.downloadSizeMB { return .storage }
        if requested { return .requested }
        if tour.meteredConnection && wifiOnly { return .waiting }
        return .ready
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            surface
        }
        .padding(8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            Rectangle()
                .fill(AudioTourColors.canvas)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(Text("Panel background"))
        )
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text("Offline audio tour"))
        .accessibilityIdentifier("audio.canvas")
    }

    private var surface: some View {
        VStack(alignment: .leading, spacing: 12) {
            Rectangle()
                .fill(AudioTourColors.ink)
                .frame(width: 6, height: 40)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(Text("Ink accent"))
                .accessibilityIdentifier("audio.inkMark")

            Text(tour.title)
                .font(.title2.weight(.semibold))
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityIdentifier("audio.title")

            Text(tour.language + " · " + String(tour.downloadSizeMB) + " MB")
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityIdentifier("audio.subtitle")

            statusBand

            Button(action: { chaptersOpen.toggle() }) {
                Text(chaptersOpen ? "Hide chapters" : "Review chapters")
                    .font(.body)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                    .contentShape(Rectangle())
            }
            .buttonStyle(AudioTourButtonStyle())
            .accessibilityIdentifier("audio.disclosure")

            if chaptersOpen {
                VStack(alignment: .leading, spacing: 16) {
                    ForEach(Array(tour.chapters.enumerated()), id: \.element.id) { index, chapter in
                        VStack(alignment: .leading, spacing: 12) {
                            Text(chapter.title)
                                .font(.headline)
                                .fixedSize(horizontal: false, vertical: true)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .accessibilityIdentifier("audio.section.\(index).heading")
                            Text(chapter.body)
                                .font(.body)
                                .fixedSize(horizontal: false, vertical: true)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .accessibilityIdentifier("audio.section.\(index).body")
                        }
                    }
                }
            }

            choiceButton
            primaryButton
        }
        .lineLimit(nil)
        .multilineTextAlignment(.leading)
        .foregroundColor(AudioTourColors.ink)
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AudioTourColors.surface)
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text("Tour content"))
        .accessibilityIdentifier("audio.surface")
    }

    private var statusBand: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(status.label)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityIdentifier("audio.statusText")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
        .background(status.fill)
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text(status.label))
        .accessibilityIdentifier("audio.status")
    }

    private var choiceButton: some View {
        Button(action: {
            guard !requested else { return }
            wifiOnly.toggle()
            onWifiOnlyChange(wifiOnly)
        }) {
            HStack(alignment: .center, spacing: 8) {
                Image(systemName: wifiOnly ? "checkmark.square" : "square")
                    .accessibilityHidden(true)
                Text("Wi-Fi only")
                    .font(.body)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(AudioTourButtonStyle())
        .disabled(requested)
        .accessibilityLabel(Text("Wi-Fi only"))
        .accessibilityAddTraits(wifiOnly ? [.isSelected] : [])
        .accessibilityIdentifier("audio.choice")
    }

    private var primaryButton: some View {
        Button(action: {
            guard canDownload else { return }
            requested = true
            onDownload(tour.id, wifiOnly)
        }) {
            Text(requested ? "Requested" : "Get audio")
                .font(.body.weight(.semibold))
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity)
                .frame(height: 56)
                .foregroundColor(canDownload ? .white : AudioTourColors.ink)
                .background(canDownload ? AudioTourColors.enabled : AudioTourColors.disabled)
                .contentShape(Rectangle())
        }
        .buttonStyle(AudioTourButtonStyle())
        .disabled(!canDownload)
        .accessibilityIdentifier("audio.primary")
    }
}

/// Keep the authored opaque fills intact in both native enabled states.
private struct AudioTourButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View { configuration.label }
}

private enum AudioTourStatus {
    case storage, requested, waiting, ready

    var label: String {
        switch self {
        case .storage: return "Storage needed"
        case .requested: return "Download requested"
        case .waiting: return "Wi-Fi required"
        case .ready: return "Ready to download"
        }
    }

    var fill: Color {
        switch self {
        case .storage: return AudioTourColors.blocked
        case .requested: return AudioTourColors.requested
        case .waiting: return AudioTourColors.waiting
        case .ready: return AudioTourColors.ready
        }
    }
}

private enum AudioTourColors {
    static let canvas = rgb(0xF4F6FA)
    static let surface = rgb(0xFFFFFF)
    static let ink = rgb(0x172B4D)
    static let waiting = rgb(0xE9EFF8)
    static let ready = rgb(0xDDF4EC)
    static let requested = rgb(0xDDEBFF)
    static let blocked = rgb(0xFFE5B3)
    static let enabled = rgb(0x2463C5)
    static let disabled = rgb(0xD8DEE8)

    private static func rgb(_ value: UInt32) -> Color {
        Color(.sRGB, red: Double((value >> 16) & 255) / 255,
              green: Double((value >> 8) & 255) / 255,
              blue: Double(value & 255) / 255, opacity: 1)
    }
}
