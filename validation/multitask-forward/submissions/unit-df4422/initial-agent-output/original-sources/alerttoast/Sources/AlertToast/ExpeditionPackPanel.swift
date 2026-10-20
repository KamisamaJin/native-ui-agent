import SwiftUI

public struct ExpeditionPackItem: Codable {
    public let id: String
    public let name: String
    public let grams: Int
    public let available: Bool
    public let providesShelter: Bool
    public let note: String

    public init(id: String, name: String, grams: Int, available: Bool, providesShelter: Bool, note: String) {
        self.id = id
        self.name = name
        self.grams = grams
        self.available = available
        self.providesShelter = providesShelter
        self.note = note
    }
}

public struct ExpeditionPackRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let choiceWidth: Double
    public let notes: [String]
    public let baseGrams: Int
    public let maxGrams: Int
    public let requiresShelter: Bool
    public let coverGrams: Int
    public let selectedIDs: [String]
    public let cover: Bool
    public let items: [ExpeditionPackItem]

    public init(id: String, title: String, context: String, choiceWidth: Double, notes: [String], baseGrams: Int, maxGrams: Int, requiresShelter: Bool, coverGrams: Int, selectedIDs: [String], cover: Bool, items: [ExpeditionPackItem]) {
        self.id = id
        self.title = title
        self.context = context
        self.choiceWidth = choiceWidth
        self.notes = notes
        self.baseGrams = baseGrams
        self.maxGrams = maxGrams
        self.requiresShelter = requiresShelter
        self.coverGrams = coverGrams
        self.selectedIDs = selectedIDs
        self.cover = cover
        self.items = items
    }
}

public struct ExpeditionPackPanel: View {
    private let request: ExpeditionPackRequest
    private let onConfirm: (String, [String], Bool) -> Void
    @State private var selectedIDs: Set<String>
    @State private var cover: Bool
    @State private var detailsExpanded = false
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .headline) private var summarySize: CGFloat = 18
    @ScaledMetric(relativeTo: .body) private var actionSize: CGFloat = 16
    @ScaledMetric(relativeTo: .subheadline) private var bodySize: CGFloat = 14

    public init(request: ExpeditionPackRequest, onConfirm: @escaping (String, [String], Bool) -> Void) {
        self.request = request
        self.onConfirm = onConfirm
        let seed = Self.seedSelection(request)
        _selectedIDs = State(initialValue: seed)
        _cover = State(initialValue: request.cover && !seed.isEmpty)
    }

    private static func seedSelection(_ request: ExpeditionPackRequest) -> Set<String> {
        let available = Set(request.items.filter { $0.available }.map { $0.id })
        return Set(request.selectedIDs).intersection(available)
    }

    private var palette: PackPalette { PackPalette(dark: colorScheme == .dark) }
    private var selectedItems: [ExpeditionPackItem] {
        request.items.filter { selectedIDs.contains($0.id) }
    }
    private var totalGrams: Int {
        request.baseGrams + selectedItems.reduce(0) { $0 + $1.grams } + (cover ? request.coverGrams : 0)
    }
    private var hasShelter: Bool { selectedItems.contains { $0.providesShelter } }
    private var canConfirm: Bool {
        !selectedIDs.isEmpty && totalGrams <= request.maxGrams && (!request.requiresShelter || hasShelter)
    }
    private var canChangeCover: Bool {
        !selectedIDs.isEmpty && (cover || totalGrams + request.coverGrams <= request.maxGrams)
    }
    private var status: String {
        if totalGrams > request.maxGrams { return "Capacity exceeded" }
        if selectedIDs.isEmpty { return "Choose shared equipment" }
        if request.requiresShelter && !hasShelter { return "Shelter required" }
        return "Ready for departure"
    }
    private var summary: String {
        "\(selectedIDs.count) \(selectedIDs.count == 1 ? "item" : "items") • \(totalGrams) g / \(request.maxGrams) g"
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Text(request.title)
                    .font(.system(size: titleSize, weight: .bold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("pack.title")
                Text(request.context)
                    .font(.system(size: bodySize, weight: .regular))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("pack.context")
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            HStack(alignment: .top, spacing: 12) {
                ForEach(Array(request.items.enumerated()), id: \.offset) { index, item in
                    choice(item, identifier: index == 0 ? "pack.choiceA" : "pack.choiceB")
                }
            }

            Button(action: {
                guard canChangeCover else { return }
                cover.toggle()
            }) {
                HStack(alignment: .top, spacing: 8) {
                    Text("Weather cover")
                        .font(.system(size: actionSize, weight: .semibold))
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer(minLength: 0)
                    if cover {
                        Image(systemName: "checkmark")
                            .font(.system(size: actionSize, weight: .semibold))
                            .accessibilityHidden(true)
                    }
                }
                .foregroundColor(canChangeCover ? palette.ink : palette.muted)
                .padding(12)
                .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 12).fill(canChangeCover ? palette.surface : palette.border))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(cover ? palette.accent : palette.border, lineWidth: 1))
                .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!canChangeCover)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("Weather cover")
            .accessibilityAddTraits(cover ? .isSelected : [])
            .accessibilityIdentifier("pack.extra")

            Text(summary)
                .font(.system(size: summarySize, weight: .semibold))
                .foregroundColor(palette.ink)
                .frame(maxWidth: .infinity, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("pack.summary")

            Text(status)
                .font(.system(size: bodySize, weight: .regular))
                .foregroundColor(palette.accent)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("pack.status")

            Button(action: { detailsExpanded.toggle() }) {
                Text(detailsExpanded ? "Hide details" : "Show details")
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(12)
                    .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 12).fill(palette.surface))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(palette.border, lineWidth: 1))
                    .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .accessibilityIdentifier("pack.disclosure")

            if detailsExpanded {
                Text(request.requiresShelter ? "Shelter needed for this route." : "Day route: no shelter required.")
                    .font(.system(size: bodySize, weight: .regular))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("pack.detail")
            }

            Button(action: {
                guard canConfirm else { return }
                onConfirm(request.id, selectedIDs.sorted(), cover)
            }) {
                Text("Confirm pack")
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(canConfirm ? palette.primaryInk : palette.muted)
                    .padding(.horizontal, 12)
                    .frame(maxWidth: .infinity, minHeight: 56, maxHeight: 56, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 12).fill(canConfirm ? palette.accent : palette.border))
                    .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!canConfirm)
            .accessibilityIdentifier("pack.primary")

            VStack(alignment: .leading, spacing: 16) {
                Text("Before departure")
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityIdentifier("pack.notes")
                ForEach(Array(request.notes.enumerated()), id: \.offset) { _, note in
                    Text(note)
                        .font(.system(size: bodySize, weight: .regular))
                        .foregroundColor(palette.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.canvas)
        .onChange(of: request.id) { _ in
            selectedIDs = Self.seedSelection(request)
            cover = request.cover && !selectedIDs.isEmpty
            detailsExpanded = false
        }
    }

    private func canToggle(_ item: ExpeditionPackItem) -> Bool {
        selectedIDs.contains(item.id) || (item.available && totalGrams + item.grams <= request.maxGrams)
    }

    private func choice(_ item: ExpeditionPackItem, identifier: String) -> some View {
        let selected = selectedIDs.contains(item.id)
        let enabled = canToggle(item)
        return Button(action: {
            guard canToggle(item) else { return }
            if selectedIDs.contains(item.id) {
                selectedIDs.remove(item.id)
                if selectedIDs.isEmpty { cover = false }
            } else {
                selectedIDs.insert(item.id)
            }
        }) {
            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .top, spacing: 4) {
                    Text(item.name)
                        .font(.system(size: actionSize, weight: .semibold))
                        .fixedSize(horizontal: false, vertical: true)
                    if selected {
                        Image(systemName: "checkmark")
                            .font(.system(size: bodySize, weight: .semibold))
                            .foregroundColor(palette.accent)
                            .accessibilityHidden(true)
                    }
                }
                .foregroundColor(enabled ? palette.ink : palette.muted)
                Text(item.note)
                    .font(.system(size: bodySize, weight: .regular))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .frame(width: CGFloat(request.choiceWidth), alignment: .leading)
            .frame(minHeight: 90, alignment: .topLeading)
            .background(RoundedRectangle(cornerRadius: 12).fill(enabled ? palette.surface : palette.border))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected ? palette.accent : palette.border, lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(item.name), \(item.note)")
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier(identifier)
    }
}

private struct PackPalette {
    let canvas: Color
    let surface: Color
    let ink: Color
    let muted: Color
    let accent: Color
    let border: Color
    let primaryInk: Color

    init(dark: Bool) {
        canvas = Self.color(dark ? 0x101A14 : 0xFFFFFF)
        surface = Self.color(dark ? 0x16231C : 0xF4F7F3)
        ink = Self.color(dark ? 0xE9F2EC : 0x18251F)
        muted = Self.color(dark ? 0xB7C7BD : 0x53645B)
        accent = Self.color(dark ? 0x94D6AC : 0x276145)
        border = Self.color(dark ? 0x456251 : 0xC9D7CC)
        primaryInk = Self.color(dark ? 0x101A14 : 0xFFFFFF)
    }

    private static func color(_ rgb: UInt32) -> Color {
        Color(.sRGB, red: Double((rgb >> 16) & 0xFF) / 255, green: Double((rgb >> 8) & 0xFF) / 255, blue: Double(rgb & 0xFF) / 255, opacity: 1)
    }
}
