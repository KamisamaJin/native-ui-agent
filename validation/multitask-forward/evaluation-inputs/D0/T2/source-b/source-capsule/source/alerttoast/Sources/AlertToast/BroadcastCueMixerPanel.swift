import SwiftUI

public struct BroadcastMixChannel: Codable {
    public let id: String
    public let name: String
    public let caption: String
    public let level: Int
    public let muted: Bool
    public let locked: Bool

    public init(id: String, name: String, caption: String, level: Int, muted: Bool, locked: Bool) {
        self.id = id
        self.name = name
        self.caption = caption
        self.level = level
        self.muted = muted
        self.locked = locked
    }
}

public struct BroadcastCueMixerRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let maxLiveUnits: Int
    public let maxLevel: Int
    public let mode: String
    public let stepperWidth: Double
    public let notes: [String]
    public let channels: [BroadcastMixChannel]

    public init(id: String, title: String, context: String, maxLiveUnits: Int, maxLevel: Int, mode: String, stepperWidth: Double, notes: [String], channels: [BroadcastMixChannel]) {
        self.id = id
        self.title = title
        self.context = context
        self.maxLiveUnits = maxLiveUnits
        self.maxLevel = maxLevel
        self.mode = mode
        self.stepperWidth = stepperWidth
        self.notes = notes
        self.channels = channels
    }
}

public struct BroadcastCueMixerPanel: View {
    private let request: BroadcastCueMixerRequest
    private let onConfirm: (String, String, [BroadcastMixChannel]) -> Void
    @State private var channels: [BroadcastMixChannel]
    @State private var mode: String
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .body) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 14
    @ScaledMetric(relativeTo: .body) private var rowSize: CGFloat = 16
    @ScaledMetric(relativeTo: .body) private var captionSize: CGFloat = 13
    @ScaledMetric(relativeTo: .body) private var summarySize: CGFloat = 18

    public init(request: BroadcastCueMixerRequest, onConfirm: @escaping (String, String, [BroadcastMixChannel]) -> Void) {
        self.request = request
        self.onConfirm = onConfirm
        _channels = State(initialValue: Self.seed(request))
        _mode = State(initialValue: request.mode)
    }

    private static func seed(_ request: BroadcastCueMixerRequest) -> [BroadcastMixChannel] {
        request.channels.map { channel in
            BroadcastMixChannel(id: channel.id, name: channel.name, caption: channel.caption,
                                level: min(max(channel.level, 0), max(request.maxLevel, 0)),
                                muted: channel.muted, locked: channel.locked)
        }
    }

    private var palette: MixerPalette { MixerPalette(dark: colorScheme == .dark) }
    private var load: Int { channels.filter { !$0.muted }.reduce(0) { $0 + $1.level } }
    private var audibleCount: Int { channels.filter { !$0.muted && $0.level > 0 }.count }
    private var headroom: Int { request.maxLiveUnits - load }
    private var canApply: Bool { audibleCount > 0 && (mode == "preview" || load <= request.maxLiveUnits) }

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Text(request.title)
                    .font(.system(size: titleSize, weight: .bold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.title")
                Text(request.context)
                    .font(.system(size: bodySize))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
            HStack(spacing: 8) {
                modeControl("Live", value: "live")
                modeControl("Preview", value: "preview")
            }
            VStack(alignment: .leading, spacing: 16) {
                Text("Channels")
                    .font(.system(size: rowSize, weight: .semibold))
                ForEach(channels, id: \.id) { channel in
                    channelRow(channel)
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                Text("\(audibleCount) audible • \(load) / \(request.maxLiveUnits) units")
                    .font(.system(size: summarySize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.summary")
                Text("Headroom: \(headroom) \(headroom == 1 ? "unit" : "units")")
                    .font(.system(size: bodySize))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.headroom")
                Text(mode == "preview" ? "Preview mode" : "Live mode")
                    .font(.system(size: bodySize, weight: .semibold))
                    .foregroundColor(palette.accent)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.modeLabel")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(palette.surface)
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(palette.border, lineWidth: 1))
            .cornerRadius(10)
            if load > request.maxLiveUnits {
                let excess = load - request.maxLiveUnits
                Text("Over live limit by \(excess) \(excess == 1 ? "unit" : "units")")
                    .font(.system(size: bodySize, weight: .semibold))
                    .foregroundColor(palette.accent)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.warning")
            }
            Button(action: confirm) {
                Text("Apply mix")
                    .font(.system(size: rowSize, weight: .semibold))
                    .foregroundColor(canApply ? palette.primaryInk : palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .frame(height: 56)
                    .background(canApply ? palette.accent : palette.border)
                    .cornerRadius(10)
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!canApply)
            .accessibilityIdentifier("mixer.primary")
            VStack(alignment: .leading, spacing: 16) {
                Text("Operator notes")
                    .font(.system(size: rowSize, weight: .semibold))
                    .accessibilityIdentifier("mixer.notes")
                ForEach(Array(request.notes.enumerated()), id: \.offset) { _, note in
                    Text(note)
                        .font(.system(size: bodySize))
                        .foregroundColor(palette.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .foregroundColor(palette.ink)
        .frame(maxWidth: .infinity, alignment: .leading)
        .onChange(of: request.id) { _ in
            channels = Self.seed(request)
            mode = request.mode
        }
    }

    private func modeControl(_ label: String, value: String) -> some View {
        let selected = mode == value
        return Button(action: { mode = value }) {
            Text(label)
                .font(.system(size: rowSize, weight: .semibold))
                .foregroundColor(palette.ink)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .frame(minHeight: 48)
                .background(palette.surface)
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(selected ? palette.accent : palette.border, lineWidth: 1))
                .overlay(selectionMarker(selected), alignment: .topTrailing)
                .cornerRadius(10)
                .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityIdentifier("mixer.\(value)")
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func channelRow(_ channel: BroadcastMixChannel) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(channel.name + (channel.locked ? " • Locked" : ""))
                .font(.system(size: rowSize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
            Text(channel.caption)
                .font(.system(size: captionSize))
                .foregroundColor(palette.muted)
                .fixedSize(horizontal: false, vertical: true)
            HStack(spacing: 0) {
                stepControl("−", channel: channel, delta: -1)
                Text("\(channel.level)")
                    .font(.system(size: rowSize, weight: .semibold))
                    .frame(width: 40)
                    .accessibilityIdentifier("mixer.\(channel.id)Level")
                stepControl("+", channel: channel, delta: 1)
                Spacer(minLength: 0)
                Button(action: { edit(channel.id, mute: !channel.muted) }) {
                    Text(channel.muted ? "Muted" : "Mute")
                        .font(.system(size: bodySize, weight: .semibold))
                        .foregroundColor(channel.locked ? palette.muted : palette.ink)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(12)
                        .frame(width: 90, alignment: .leading)
                        .frame(minHeight: 48)
                        .background(channel.locked ? palette.border : palette.surface)
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(channel.muted ? palette.accent : palette.border, lineWidth: 1))
                        .overlay(selectionMarker(channel.muted), alignment: .topTrailing)
                        .cornerRadius(10)
                        .contentShape(RoundedRectangle(cornerRadius: 10))
                }
                .buttonStyle(PlainButtonStyle())
                .disabled(channel.locked)
                .accessibilityIdentifier("mixer.\(channel.id)Mute")
                .accessibilityAddTraits(channel.muted ? .isSelected : [])
            }
        }
    }

    private func stepControl(_ label: String, channel: BroadcastMixChannel, delta: Int) -> some View {
        let enabled = !channel.locked && (delta < 0 ? channel.level > 0 : channel.level < request.maxLevel)
        return Button(action: { edit(channel.id, delta: delta) }) {
            Text(label)
                .font(.system(size: rowSize, weight: .semibold))
                .foregroundColor(enabled ? palette.ink : palette.muted)
                .frame(width: CGFloat(request.stepperWidth), height: 48)
                .background(enabled ? palette.surface : palette.border)
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(palette.border, lineWidth: 1))
                .cornerRadius(10)
                .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(delta < 0 ? "Decrease \(channel.name)" : "Increase \(channel.name)")
        .accessibilityIdentifier("mixer.\(channel.id)\(delta < 0 ? "Minus" : "Plus")")
    }

    private func selectionMarker(_ selected: Bool) -> some View {
        Circle().fill(palette.accent).frame(width: 4, height: 4)
            .padding(4).opacity(selected ? 1 : 0).accessibilityHidden(true)
    }

    private func edit(_ id: String, delta: Int = 0, mute: Bool? = nil) {
        guard let index = channels.firstIndex(where: { $0.id == id }), !channels[index].locked else { return }
        let channel = channels[index]
        let level = min(max(channel.level + delta, 0), max(request.maxLevel, 0))
        channels[index] = BroadcastMixChannel(id: channel.id, name: channel.name, caption: channel.caption,
                                              level: level, muted: mute ?? channel.muted, locked: channel.locked)
    }

    private func confirm() {
        guard canApply else { return }
        onConfirm(request.id, mode, channels.sorted { $0.id < $1.id })
    }
}

private struct MixerPalette {
    let surface: Color
    let ink: Color
    let muted: Color
    let accent: Color
    let border: Color
    let primaryInk: Color

    init(dark: Bool) {
        surface = Self.color(dark ? 0x17283C : 0xF0F5FA)
        ink = Self.color(dark ? 0xE1EDFA : 0x1E3652)
        muted = Self.color(dark ? 0xB4C7DD : 0x556B82)
        accent = Self.color(dark ? 0xA0CCFA : 0x245F9A)
        border = Self.color(dark ? 0x405971 : 0xC8D7E5)
        primaryInk = Self.color(dark ? 0x101B29 : 0xFFFFFF)
    }

    private static func color(_ rgb: UInt32) -> Color {
        Color(.sRGB, red: Double((rgb >> 16) & 255) / 255,
              green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255, opacity: 1)
    }
}
