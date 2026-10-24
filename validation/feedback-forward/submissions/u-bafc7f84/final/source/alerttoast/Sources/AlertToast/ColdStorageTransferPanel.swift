import SwiftUI

/// One caller-supplied step in the transfer's handling instructions.
public struct TransferHandlingNote: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let body: String

    public init(id: String, title: String, body: String) {
        self.id = id
        self.title = title
        self.body = body
    }
}

/// A release request records intent; physical inventory and handoff remain external.
public struct ColdStorageTransfer: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let destination: String
    public let temperatureRange: String
    public let sealIntact: Bool
    public let coolantReady: Bool
    public let notes: [TransferHandlingNote]

    public init(id: String, title: String, destination: String, temperatureRange: String,
                sealIntact: Bool, coolantReady: Bool, notes: [TransferHandlingNote]) {
        self.id = id
        self.title = title
        self.destination = destination
        self.temperatureRange = temperatureRange
        self.sealIntact = sealIntact
        self.coolantReady = coolantReady
        self.notes = notes
    }
}

/// An embeddable panel. Its parent supplies scrolling and receives business actions.
@available(iOS 14, macOS 11, *)
public struct ColdStorageTransferPanel: View {
    private let transfer: ColdStorageTransfer
    private let onAcknowledgementChange: (Bool) -> Void
    private let onRelease: (String) -> Void

    public init(transfer: ColdStorageTransfer,
                onAcknowledgementChange: @escaping (Bool) -> Void,
                onRelease: @escaping (String) -> Void) {
        self.transfer = transfer
        self.onAcknowledgementChange = onAcknowledgementChange
        self.onRelease = onRelease
    }

    public var body: some View {
        // The production component owns this identity boundary: replacing a transfer
        // creates fresh local state in the same public panel, without business events.
        TransferPanelContent(transfer: transfer,
                             onAcknowledgementChange: onAcknowledgementChange,
                             onRelease: onRelease)
            .id(transfer.id)
    }
}

@available(iOS 14, macOS 11, *)
private struct TransferPanelContent: View {
    let transfer: ColdStorageTransfer
    let onAcknowledgementChange: (Bool) -> Void
    let onRelease: (String) -> Void

    @State private var handlingOpen = false
    @State private var acknowledged = false
    @State private var requested = false

    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .headline) private var headingSize: CGFloat = 17
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 17

    private var canRelease: Bool {
        transfer.sealIntact && transfer.coolantReady && acknowledged && !requested
    }

    private var status: (label: String, fill: Color) {
        if !transfer.sealIntact {
            return ("Seal needs attention", TransferPanelPalette.blocked)
        } else if !transfer.coolantReady {
            return ("Coolant not ready", TransferPanelPalette.blocked)
        } else if requested {
            return ("Release requested", TransferPanelPalette.requested)
        } else if acknowledged {
            return ("Ready for release", TransferPanelPalette.ready)
        } else {
            return ("Awaiting check", TransferPanelPalette.waiting)
        }
    }

    private var disclosureLabel: String { handlingOpen ? "Hide handling" : "Review handling" }
    private var choiceLabel: String { acknowledged ? "Seal check confirmed" : "Confirm seal checked" }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            surface
        }
        .padding(8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            // The real painted background is a second accessible child. This keeps
            // .contain from reusing the sole surface container and its identifier.
            TransferPanelPalette.canvas
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(Text("Transfer panel background"))
        )
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("transfer.canvas")
    }

    private var surface: some View {
        VStack(alignment: .leading, spacing: 12) {
            Rectangle()
                .fill(TransferPanelPalette.ink)
                .frame(width: 6, height: 40)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(Text("Ink accent"))
                .accessibilityIdentifier("transfer.inkMark")

            Text(transfer.title)
                .font(.system(size: titleSize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("transfer.title")

            Text(transfer.destination + " · " + transfer.temperatureRange)
                .font(.system(size: bodySize))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("transfer.subtitle")

            statusBand

            Button(action: { handlingOpen.toggle() }) {
                Text(disclosureLabel)
                    .font(.system(size: headingSize, weight: .semibold))
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                    .contentShape(Rectangle())
            }
            .buttonStyle(TransferPanelButtonStyle())
            .accessibilityLabel(Text(disclosureLabel))
            .accessibilityIdentifier("transfer.disclosure")

            if handlingOpen {
                VStack(alignment: .leading, spacing: 16) {
                    ForEach(Array(transfer.notes.enumerated()), id: \.element.id) { index, note in
                        VStack(alignment: .leading, spacing: 8) {
                            Text(note.title)
                                .font(.system(size: headingSize, weight: .semibold))
                                .fixedSize(horizontal: false, vertical: true)
                                .accessibilityAddTraits(.isHeader)
                                .accessibilityIdentifier("transfer.section.\(index).heading")
                            Text(note.body)
                                .font(.system(size: bodySize))
                                .fixedSize(horizontal: false, vertical: true)
                                .accessibilityIdentifier("transfer.section.\(index).body")
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }

            Button(action: toggleAcknowledgement) {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: acknowledged ? "checkmark.square.fill" : "square")
                        .accessibilityHidden(true)
                    Text(choiceLabel)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .font(.system(size: bodySize))
                .padding(.vertical, 8)
                .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                .contentShape(Rectangle())
            }
            .buttonStyle(TransferPanelButtonStyle())
            .disabled(requested)
            .accessibilityLabel(Text(choiceLabel))
            .accessibilityAddTraits(acknowledged ? .isSelected : [])
            .accessibilityIdentifier("transfer.choice")

            Button(action: requestRelease) {
                Text(requested ? "Requested" : "Release transfer")
                    .font(.system(size: headingSize, weight: .semibold))
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .foregroundColor(canRelease ? .white : TransferPanelPalette.ink)
                    .background(canRelease ? TransferPanelPalette.enabled : TransferPanelPalette.disabled)
                    .contentShape(Rectangle())
            }
            .buttonStyle(TransferPanelButtonStyle())
            .disabled(!canRelease)
            .accessibilityIdentifier("transfer.primary")
        }
        .lineLimit(nil)
        .foregroundColor(TransferPanelPalette.ink)
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("transfer.surface")
    }

    private var statusBand: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(status.label)
                .font(.system(size: headingSize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("transfer.statusText")
        }
        .padding(16)
        .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
        .background(status.fill)
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text(status.label))
        .accessibilityIdentifier("transfer.status")
    }

    private func toggleAcknowledgement() {
        guard !requested else { return }
        acknowledged.toggle()
        onAcknowledgementChange(acknowledged)
    }

    private func requestRelease() {
        guard canRelease else { return }
        requested = true
        onRelease(transfer.id)
    }
}

// Preserve each Button's own native enabled/selected behavior while leaving the
// caller-independent opaque palette and rectangular label allocations intact.
private struct TransferPanelButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

private enum TransferPanelPalette {
    static let canvas = Color(.sRGB, red: 244 / 255, green: 246 / 255, blue: 250 / 255, opacity: 1)
    static let ink = Color(.sRGB, red: 23 / 255, green: 43 / 255, blue: 77 / 255, opacity: 1)
    static let waiting = Color(.sRGB, red: 233 / 255, green: 239 / 255, blue: 248 / 255, opacity: 1)
    static let ready = Color(.sRGB, red: 221 / 255, green: 244 / 255, blue: 236 / 255, opacity: 1)
    static let requested = Color(.sRGB, red: 221 / 255, green: 235 / 255, blue: 255 / 255, opacity: 1)
    static let blocked = Color(.sRGB, red: 255 / 255, green: 229 / 255, blue: 179 / 255, opacity: 1)
    static let enabled = Color(.sRGB, red: 36 / 255, green: 99 / 255, blue: 197 / 255, opacity: 1)
    static let disabled = Color(.sRGB, red: 216 / 255, green: 222 / 255, blue: 232 / 255, opacity: 1)
}
