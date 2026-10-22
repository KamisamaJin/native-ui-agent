import SwiftUI

public struct WorkshopSlot: Codable, Identifiable {
    public var id: String
    public var label: String
    public var detail: String
    public var available: Bool
    public var unavailableReason: String

    public init(id: String, label: String, detail: String, available: Bool, unavailableReason: String) {
        self.id = id
        self.label = label
        self.detail = detail
        self.available = available
        self.unavailableReason = unavailableReason
    }
}

public struct WorkshopSlotPlannerModel: Codable {
    public var revision: String
    public var title: String
    public var subtitle: String
    public var notice: String
    public var footer: String
    public var guidance: String
    public var initialSelectedID: String?
    public var initialDetailsExpanded: Bool
    public var slots: [WorkshopSlot]

    public init(revision: String, title: String, subtitle: String, notice: String,
                footer: String, guidance: String, initialSelectedID: String?,
                initialDetailsExpanded: Bool, slots: [WorkshopSlot]) {
        self.revision = revision
        self.title = title
        self.subtitle = subtitle
        self.notice = notice
        self.footer = footer
        self.guidance = guidance
        self.initialSelectedID = initialSelectedID
        self.initialDetailsExpanded = initialDetailsExpanded
        self.slots = slots
    }

    fileprivate var validInitialSelection: String? {
        slots.first { $0.id == initialSelectedID && $0.available }?.id
    }
}

public struct WorkshopSlotPlanner: View {
    public let model: WorkshopSlotPlannerModel
    private let onSelect: (String) -> Void
    private let onDetailsChange: (Bool) -> Void
    private let onReserve: (String) -> Void

    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.sizeCategory) private var sizeCategory
    @ScaledMetric(relativeTo: .title3) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .footnote) private var supportingSize: CGFloat = 14
    @State private var selectedID: String?
    @State private var detailsExpanded: Bool
    @State private var stateRevision: String
    @State private var componentWidth: CGFloat = 0

    public init(model: WorkshopSlotPlannerModel, onSelect: @escaping (String) -> Void,
                onDetailsChange: @escaping (Bool) -> Void, onReserve: @escaping (String) -> Void) {
        self.model = model
        self.onSelect = onSelect
        self.onDetailsChange = onDetailsChange
        self.onReserve = onReserve
        _selectedID = State(initialValue: model.validInitialSelection)
        _detailsExpanded = State(initialValue: model.initialDetailsExpanded)
        _stateRevision = State(initialValue: model.revision)
    }

    private var palette: WorkshopPalette { WorkshopPalette(dark: colorScheme == .dark) }
    private var currentID: String? { stateRevision == model.revision ? selectedID : model.validInitialSelection }
    private var currentSlot: WorkshopSlot? { model.slots.first { $0.id == currentID && $0.available } }
    private var isExpanded: Bool { stateRevision == model.revision ? detailsExpanded : model.initialDetailsExpanded }
    private var columns: Int { componentWidth >= 320 && sizeCategory <= .large ? 2 : 1 }
    private var summary: String { currentSlot.map { "Draft station: \($0.label)" } ?? "No station selected" }
    private var disclosureLabel: String { isExpanded ? "Hide safety briefing" : "Show safety briefing" }

    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                readable(model.title, size: titleSize, weight: .semibold)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityIdentifier("workshop.title")
                readable(model.subtitle, size: bodySize)
                VStack(alignment: .leading, spacing: 0) {
                    readable(model.notice, size: bodySize)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(palette.notice)
                .cornerRadius(10)
                .accessibilityElement(children: .combine)
                .accessibilityLabel(Text(model.notice))
                .accessibilityIdentifier("workshop.notice")
            }
            stationGrid
            readable(summary, size: bodySize, weight: .semibold)
                .accessibilityIdentifier("workshop.summary")
            VStack(alignment: .leading, spacing: 12) {
                Button(action: {
                    let next = !isExpanded
                    synchronizeRevision()
                    detailsExpanded = next
                    onDetailsChange(next)
                }) {
                    readable(disclosureLabel, size: bodySize, weight: .semibold)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .buttonStyle(WorkshopPlainButtonStyle())
                .accessibilityLabel(Text(disclosureLabel))
                .accessibilityIdentifier("workshop.disclosure")
                if isExpanded {
                    readable(model.guidance, size: bodySize)
                }
            }
            Button(action: {
                if let slot = currentSlot { onReserve(slot.id) }
            }) {
                readable("Request station", size: bodySize, weight: .semibold, color: palette.onAction)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 16)
                    .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
                    .background(currentSlot == nil ? palette.disabled : palette.enabled)
                    .cornerRadius(10)
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(WorkshopPlainButtonStyle())
            .disabled(currentSlot == nil)
            .accessibilityLabel(Text("Request station"))
            .accessibilityIdentifier("workshop.submit")
            readable(model.footer, size: supportingSize)
                .accessibilityIdentifier("workshop.footer")
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.canvas)
        .cornerRadius(12)
        .background(GeometryReader { proxy in
            Color.clear.preference(key: WorkshopWidthPreference.self, value: proxy.size.width)
        })
        .onPreferenceChange(WorkshopWidthPreference.self) { componentWidth = $0 }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("workshop.canvas")
        .onChange(of: model.revision) { _ in synchronizeRevision() }
    }

    private var stationGrid: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(0..<((model.slots.count + columns - 1) / columns), id: \.self) { row in
                HStack(alignment: .top, spacing: 12) {
                    ForEach(0..<columns, id: \.self) { column in
                        let index = row * columns + column
                        if index < model.slots.count {
                            stationCard(model.slots[index])
                        } else {
                            Color.clear.frame(maxWidth: .infinity)
                        }
                    }
                }
                .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private func stationCard(_ slot: WorkshopSlot) -> some View {
        let selected = currentSlot?.id == slot.id
        return Button(action: {
            guard slot.available else { return }
            synchronizeRevision()
            selectedID = slot.id
            onSelect(slot.id)
        }) {
            VStack(alignment: .leading, spacing: 12) {
                readable(slot.available ? slot.label : slot.label + " · Unavailable", size: bodySize, weight: .semibold)
                if !slot.available {
                    readable(slot.unavailableReason, size: supportingSize)
                }
                readable(slot.detail, size: supportingSize)
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 56, maxHeight: .infinity, alignment: .topLeading)
            .background(selected ? palette.selected : palette.surface)
            .cornerRadius(10)
            .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(WorkshopPlainButtonStyle())
        .disabled(!slot.available)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("workshop.choice.\(slot.id)")
    }

    private func readable(_ value: String, size: CGFloat, weight: Font.Weight = .regular, color: Color? = nil) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color ?? palette.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func synchronizeRevision() {
        if stateRevision != model.revision {
            selectedID = model.validInitialSelection
            detailsExpanded = model.initialDetailsExpanded
            stateRevision = model.revision
        }
    }
}

private struct WorkshopWidthPreference: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) { value = nextValue() }
}

private struct WorkshopPlainButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View { configuration.label }
}

private struct WorkshopPalette {
    let dark: Bool
    var canvas: Color { color(dark ? 0x14282D : 0xF5F2EB) }
    var notice: Color { color(dark ? 0x2D4245 : 0xE7DED0) }
    var enabled: Color { color(dark ? 0x8CC7C7 : 0x315F68) }
    var disabled: Color { color(dark ? 0x52666A : 0xAAA99F) }
    var ink: Color { color(dark ? 0xE6F1EF : 0x172D32) }
    var surface: Color { color(dark ? 0x20383D : 0xFFFFFF) }
    var selected: Color { color(dark ? 0x31575C : 0xD6E6E5) }
    var onAction: Color { color(dark ? 0x102D30 : 0xF8FBFA) }
    private func color(_ value: UInt) -> Color {
        Color(.sRGB, red: Double((value >> 16) & 255) / 255,
              green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255, opacity: 1)
    }
}
