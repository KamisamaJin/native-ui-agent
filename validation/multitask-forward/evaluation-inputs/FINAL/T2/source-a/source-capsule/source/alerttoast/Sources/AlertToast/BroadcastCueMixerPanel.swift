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
    public let request: BroadcastCueMixerRequest
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
                modeButton("Live", value: "live")
                modeButton("Preview", value: "preview")
            }
            VStack(alignment: .leading, spacing: 16) {
                Text("Channels")
                    .font(.system(size: rowSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                ForEach(channels.indices, id: \.self) { index in
                    channelRow(index)
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                Text("\(audibleCount) audible • \(load) / \(request.maxLiveUnits) units")
                    .font(.system(size: summarySize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.summary")
                Text("Headroom: \(headroom) \(unit(headroom))")
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
                Text("Over live limit by \(excess) \(unit(excess))")
                    .font(.system(size: bodySize, weight: .semibold))
                    .foregroundColor(palette.accent)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("mixer.warning")
            }
            Button(action: {
                guard canApply else { return }
                onConfirm(request.id, mode, channels.sorted { $0.id < $1.id })
            }) {
                Text("Apply mix")
                    .font(.system(size: rowSize, weight: .semibold))
                    .foregroundColor(canApply ? palette.primaryInk : palette.muted)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .frame(height: 56)
                    .background(canApply ? palette.accent : palette.border)
                    .cornerRadius(10)
                    .contentShape(Rectangle())
            }
            .buttonStyle(MixerPaletteButtonStyle())
            .disabled(!canApply)
            .accessibilityIdentifier("mixer.primary")
            VStack(alignment: .leading, spacing: 16) {
                Text("Operator notes")
                    .font(.system(size: rowSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .accessibilityIdentifier("mixer.notes")
                ForEach(request.notes.indices, id: \.self) { index in
                    Text(request.notes[index])
                        .font(.system(size: bodySize))
                        .foregroundColor(palette.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .onChange(of: MixerRequestRevision(request: request)) { revision in
            channels = Self.seed(revision.request)
            mode = revision.request.mode
        }
    }

    private func unit(_ value: Int) -> String { value == 1 ? "unit" : "units" }

    private func modeButton(_ label: String, value: String) -> some View {
        let isSelected = mode == value
        return Button(action: { mode = value }) {
            Text(label)
                .font(.system(size: rowSize, weight: .semibold))
                .foregroundColor(palette.ink)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .frame(minHeight: 48)
                .background(palette.surface)
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(isSelected ? palette.accent : palette.border, lineWidth: 1))
                .overlay(Group {
                    if isSelected {
                        Circle().fill(palette.accent).frame(width: 5, height: 5).padding(5)
                    }
                }, alignment: .topTrailing)
                .cornerRadius(10)
                .contentShape(Rectangle())
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityIdentifier("mixer.\(value)")
        .accessibilityAddTraits(isSelected ? [.isSelected] : [])
    }

    private func channelRow(_ index: Int) -> some View {
        let channel = channels[index]
        return VStack(alignment: .leading, spacing: 8) {
            Text(channel.name + (channel.locked ? " • Locked" : ""))
                .font(.system(size: rowSize, weight: .semibold))
                .foregroundColor(palette.ink)
                .fixedSize(horizontal: false, vertical: true)
            Text(channel.caption)
                .font(.system(size: captionSize))
                .foregroundColor(palette.muted)
                .fixedSize(horizontal: false, vertical: true)
            HStack(spacing: 0) {
                rowButton("−", id: "mixer.\(channel.id)Minus", enabled: !channel.locked && channel.level > 0,
                          width: CGFloat(request.stepperWidth), fontSize: rowSize) {
                    change(index, level: channel.level - 1, muted: channel.muted)
                }
                .accessibilityLabel("Decrease \(channel.name)")
                Text("\(channel.level)")
                    .font(.system(size: rowSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .frame(width: 40)
                    .accessibilityIdentifier("mixer.\(channel.id)Level")
                rowButton("+", id: "mixer.\(channel.id)Plus", enabled: !channel.locked && channel.level < request.maxLevel,
                          width: CGFloat(request.stepperWidth), fontSize: rowSize) {
                    change(index, level: channel.level + 1, muted: channel.muted)
                }
                .accessibilityLabel("Increase \(channel.name)")
                Spacer(minLength: 8)
                rowButton(channel.muted ? "Muted" : "Mute", id: "mixer.\(channel.id)Mute", enabled: !channel.locked,
                          width: 90, fontSize: bodySize, selected: channel.muted) {
                    change(index, level: channel.level, muted: !channel.muted)
                }
            }
        }
    }

    private func rowButton(_ label: String, id: String, enabled: Bool, width: CGFloat,
                           fontSize: CGFloat, selected: Bool = false, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: fontSize, weight: .semibold))
                .foregroundColor(enabled ? palette.ink : palette.muted)
                .fixedSize(horizontal: false, vertical: true)
                .frame(width: width, height: 48)
                .background(enabled ? palette.surface : palette.border)
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(selected ? palette.accent : palette.border, lineWidth: 1))
                .overlay(Group {
                    if selected { Circle().fill(palette.accent).frame(width: 5, height: 5).padding(5) }
                }, alignment: .topTrailing)
                .cornerRadius(10)
                .contentShape(Rectangle())
        }
        .buttonStyle(MixerPaletteButtonStyle())
        .disabled(!enabled)
        .accessibilityIdentifier(id)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    private func change(_ index: Int, level: Int, muted: Bool) {
        let old = channels[index]
        guard !old.locked else { return }
        channels[index] = BroadcastMixChannel(id: old.id, name: old.name, caption: old.caption,
                                              level: min(max(level, 0), max(request.maxLevel, 0)),
                                              muted: muted, locked: old.locked)
    }
}

private struct MixerRequestRevision: Equatable {
    let request: BroadcastCueMixerRequest

    static func == (lhs: MixerRequestRevision, rhs: MixerRequestRevision) -> Bool {
        lhs.request.id == rhs.request.id
    }
}

private struct MixerPaletteButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
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
        Color(red: Double((rgb >> 16) & 255) / 255, green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255)
    }
}
