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
    public let request: ExpeditionPackRequest
    private let onConfirm: (String, [String], Bool) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @State private var selectedIDs: Set<String>
    @State private var cover: Bool
    @State private var expanded = false
    @ScaledMetric(relativeTo: .body) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var summarySize: CGFloat = 18
    @ScaledMetric(relativeTo: .body) private var actionSize: CGFloat = 16
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 14

    public init(request: ExpeditionPackRequest, onConfirm: @escaping (String, [String], Bool) -> Void) {
        self.request = request
        self.onConfirm = onConfirm
        let seeds = Self.seedSelection(request)
        _selectedIDs = State(initialValue: seeds)
        _cover = State(initialValue: request.cover && !seeds.isEmpty)
    }

    private static func seedSelection(_ request: ExpeditionPackRequest) -> Set<String> {
        Set(request.selectedIDs).intersection(Set(request.items.filter { $0.available }.map { $0.id }))
    }

    private var palette: PackPalette { PackPalette(dark: colorScheme == .dark) }
    private var selectedItems: [ExpeditionPackItem] { request.items.filter { selectedIDs.contains($0.id) } }
    private var totalGrams: Int {
        request.baseGrams + selectedItems.reduce(0) { $0 + $1.grams } + (cover ? request.coverGrams : 0)
    }
    private var coverEnabled: Bool {
        !selectedItems.isEmpty && (cover || totalGrams + request.coverGrams <= request.maxGrams)
    }
    private var ready: Bool {
        !selectedItems.isEmpty && totalGrams <= request.maxGrams &&
            (!request.requiresShelter || selectedItems.contains { $0.providesShelter })
    }
    private var status: String {
        if totalGrams > request.maxGrams { return "Capacity exceeded" }
        if selectedItems.isEmpty { return "Choose shared equipment" }
        if request.requiresShelter && !selectedItems.contains(where: { $0.providesShelter }) { return "Shelter required" }
        return "Ready for departure"
    }
    private var summary: String {
        "\(selectedItems.count) \(selectedItems.count == 1 ? "item" : "items") • \(totalGrams) g / \(request.maxGrams) g"
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
            HStack(alignment: .top, spacing: 12) {
                ForEach(Array(request.items.prefix(2).enumerated()), id: \.offset) { index, item in
                    itemChoice(item, identifier: index == 0 ? "pack.choiceA" : "pack.choiceB")
                }
            }
            Button(action: {
                if coverEnabled { cover.toggle() }
            }) {
                HStack(alignment: .top, spacing: 8) {
                    Text("Weather cover").fixedSize(horizontal: false, vertical: true)
                    if cover { Text("✓").accessibilityHidden(true) }
                    Spacer(minLength: 0)
                }
                .font(.system(size: actionSize, weight: .semibold))
                .foregroundColor(coverEnabled ? palette.ink : palette.muted)
                .padding(12)
                .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                .background(coverEnabled ? palette.surface : palette.border)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(cover ? palette.accent : palette.border, lineWidth: 1))
                .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!coverEnabled)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("Weather cover")
            .accessibilityAddTraits(cover ? .isSelected : [])
            .accessibilityIdentifier("pack.extra")

            Text(summary)
                .font(.system(size: summarySize, weight: .semibold))
                .foregroundColor(palette.ink)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("pack.summary")
            Text(status)
                .font(.system(size: bodySize, weight: .regular))
                .foregroundColor(palette.accent)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("pack.status")
            Button(action: { expanded.toggle() }) {
                Text(expanded ? "Hide details" : "Show details")
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(12)
                    .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                    .background(palette.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(palette.border, lineWidth: 1))
                    .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .accessibilityIdentifier("pack.disclosure")
            if expanded {
                Text(request.requiresShelter ? "Shelter needed for this route." : "Day route: no shelter required.")
                    .font(.system(size: bodySize, weight: .regular))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("pack.detail")
            }
            Button(action: {
                if ready { onConfirm(request.id, selectedIDs.sorted(), cover) }
            }) {
                Text("Confirm pack")
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(ready ? palette.primaryInk : palette.muted)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .frame(height: 56)
                    .background(ready ? palette.accent : palette.border)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!ready)
            .accessibilityIdentifier("pack.primary")
            VStack(alignment: .leading, spacing: 16) {
                Text("Before departure")
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("pack.notes")
                ForEach(Array(request.notes.enumerated()), id: \.offset) { _, paragraph in
                    Text(paragraph)
                        .font(.system(size: bodySize, weight: .regular))
                        .foregroundColor(palette.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .onChange(of: request.id) { _ in
            let seeds = Self.seedSelection(request)
            selectedIDs = seeds
            cover = request.cover && !seeds.isEmpty
            expanded = false
        }
    }

    private func itemChoice(_ item: ExpeditionPackItem, identifier: String) -> some View {
        let selected = selectedIDs.contains(item.id)
        let enabled = selected || (item.available && totalGrams + item.grams <= request.maxGrams)
        return Button(action: {
            if selected {
                selectedIDs.remove(item.id)
                if selectedIDs.isEmpty { cover = false }
            } else if enabled {
                selectedIDs.insert(item.id)
            }
        }) {
            VStack(alignment: .leading, spacing: 8) {
                Text(item.name + (selected ? " ✓" : ""))
                    .font(.system(size: actionSize, weight: .semibold))
                    .foregroundColor(enabled ? palette.ink : palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                Text(item.note)
                    .font(.system(size: bodySize, weight: .regular))
                    .foregroundColor(palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(12)
            .frame(width: CGFloat(request.choiceWidth), alignment: .leading)
            .frame(minHeight: 90, alignment: .topLeading)
            .background(enabled ? palette.surface : palette.border)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected ? palette.accent : palette.border, lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(item.name + ", " + item.note)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier(identifier)
    }
}

private struct PackPalette {
    let dark: Bool
    var surface: Color { color(dark ? 0x16231C : 0xF4F7F3) }
    var ink: Color { color(dark ? 0xE9F2EC : 0x18251F) }
    var muted: Color { color(dark ? 0xB7C7BD : 0x53645B) }
    var accent: Color { color(dark ? 0x94D6AC : 0x276145) }
    var border: Color { color(dark ? 0x456251 : 0xC9D7CC) }
    var primaryInk: Color { color(dark ? 0x101A14 : 0xFFFFFF) }
    private func color(_ hex: UInt) -> Color {
        Color(.sRGB, red: Double((hex >> 16) & 255) / 255, green: Double((hex >> 8) & 255) / 255, blue: Double(hex & 255) / 255, opacity: 1)
    }
}
