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

    public init(revision: String, title: String, subtitle: String, notice: String, footer: String, guidance: String, initialSelectedID: String?, initialDetailsExpanded: Bool, slots: [WorkshopSlot]) {
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
}

public struct WorkshopSlotPlanner: View {
    private let model: WorkshopSlotPlannerModel
    private let onSelect: (String) -> Void
    private let onDetailsChange: (Bool) -> Void
    private let onReserve: (String) -> Void

    public init(model: WorkshopSlotPlannerModel, onSelect: @escaping (String) -> Void, onDetailsChange: @escaping (Bool) -> Void, onReserve: @escaping (String) -> Void) {
        self.model = model
        self.onSelect = onSelect
        self.onDetailsChange = onDetailsChange
        self.onReserve = onReserve
    }

    public var body: some View {
        WorkshopPlannerContent(model: model, onSelect: onSelect, onDetailsChange: onDetailsChange, onReserve: onReserve)
            .id(model.revision)
    }
}

private struct WorkshopPlannerContent: View {
    let model: WorkshopSlotPlannerModel
    let onSelect: (String) -> Void
    let onDetailsChange: (Bool) -> Void
    let onReserve: (String) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.sizeCategory) private var sizeCategory
    @Environment(\.layoutDirection) private var layoutDirection
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .footnote) private var supportingSize: CGFloat = 14
    @State private var selectedID: String?
    @State private var detailsExpanded: Bool
    @State private var canvasWidth: CGFloat = 0

    init(model: WorkshopSlotPlannerModel, onSelect: @escaping (String) -> Void, onDetailsChange: @escaping (Bool) -> Void, onReserve: @escaping (String) -> Void) {
        self.model = model
        self.onSelect = onSelect
        self.onDetailsChange = onDetailsChange
        self.onReserve = onReserve
        _selectedID = State(initialValue: model.slots.first(where: { $0.id == model.initialSelectedID && $0.available })?.id)
        _detailsExpanded = State(initialValue: model.initialDetailsExpanded)
    }

    private var palette: WorkshopPalette { WorkshopPalette(dark: colorScheme == .dark) }
    private var selected: WorkshopSlot? { model.slots.first { $0.id == selectedID && $0.available } }
    private var summary: String { selected.map { "Draft station: \($0.label)" } ?? "No station selected" }
    private var ordinaryText: Bool {
        switch sizeCategory {
        case .extraSmall, .small, .medium, .large: return true
        default: return false
        }
    }
    private var twoColumns: Bool { canvasWidth >= 320 && ordinaryText }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                Text(model.title)
                    .font(.system(size: titleSize, weight: .semibold))
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("workshop.title")
                    .accessibilityAddTraits(.isHeader)
                bodyText(model.subtitle)
                VStack(alignment: .leading, spacing: 0) {
                    bodyText(model.notice)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(16)
                .background(palette.notice)
                .cornerRadius(10)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(Text(model.notice))
                .accessibilityIdentifier("workshop.notice")
            }

            slotGrid

            Text(summary)
                .font(.system(size: bodySize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("workshop.summary")

            VStack(alignment: .leading, spacing: 12) {
                Button {
                    detailsExpanded.toggle()
                    onDetailsChange(detailsExpanded)
                } label: {
                    Text(detailsExpanded ? "Hide safety briefing" : "Show safety briefing")
                        .font(.system(size: bodySize, weight: .semibold))
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .buttonStyle(WorkshopButtonStyle())
                .accessibilityIdentifier("workshop.disclosure")
                if detailsExpanded {
                    bodyText(model.guidance)
                }
            }

            Button {
                if let selected = selected { onReserve(selected.id) }
            } label: {
                Text("Request station")
                    .font(.system(size: bodySize, weight: .semibold))
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 16)
                    .frame(minHeight: 56)
                    .foregroundColor(palette.onAction)
                    .background(selected == nil ? palette.disabled : palette.enabled)
                    .cornerRadius(10)
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(WorkshopButtonStyle())
            .disabled(selected == nil)
            .accessibilityIdentifier("workshop.submit")

            Text(model.footer)
                .font(.system(size: supportingSize))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("workshop.footer")
        }
        .foregroundColor(palette.ink)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(palette.canvas)
        .cornerRadius(12)
        .background(GeometryReader { proxy in
            Color.clear
                .onAppear { canvasWidth = proxy.size.width }
                .onChange(of: proxy.size.width) { canvasWidth = $0 }
        })
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("workshop.canvas")
    }

    @ViewBuilder
    private var slotGrid: some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            WorkshopSlotGrid(ordinaryText: ordinaryText, direction: layoutDirection) {
                ForEach(model.slots) { slot in slotCard(slot) }
            }
            .frame(maxWidth: .infinity)
        } else {
            VStack(alignment: .leading, spacing: 12) {
                ForEach(0..<rowCount, id: \.self) { row in
                    HStack(alignment: .top, spacing: 12) {
                        slotCard(model.slots[row * columnCount])
                        if twoColumns {
                            if row * 2 + 1 < model.slots.count {
                                slotCard(model.slots[row * 2 + 1])
                            } else {
                                Color.clear.frame(maxWidth: .infinity)
                                    .accessibilityHidden(true)
                            }
                        }
                    }
                    .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private var columnCount: Int { twoColumns ? 2 : 1 }
    private var rowCount: Int { (model.slots.count + columnCount - 1) / columnCount }

    private func bodyText(_ value: String) -> some View {
        Text(value)
            .font(.system(size: bodySize))
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func slotCard(_ slot: WorkshopSlot) -> some View {
        Button {
            guard slot.available else { return }
            selectedID = slot.id
            onSelect(slot.id)
        } label: {
            VStack(alignment: .leading, spacing: 12) {
                Text(slot.available ? slot.label : "\(slot.label) · Unavailable")
                    .font(.system(size: bodySize, weight: .semibold))
                    .fixedSize(horizontal: false, vertical: true)
                if !slot.available {
                    Text(slot.unavailableReason)
                        .font(.system(size: supportingSize))
                        .fixedSize(horizontal: false, vertical: true)
                }
                Text(slot.detail)
                    .font(.system(size: supportingSize))
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .frame(minHeight: 56, maxHeight: .infinity, alignment: .topLeading)
            .background(selected?.id == slot.id ? palette.selected : palette.surface)
            .cornerRadius(10)
            .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(WorkshopButtonStyle())
        .disabled(!slot.available)
        .accessibilityIdentifier("workshop.choice.\(slot.id)")
        .accessibilityAddTraits(selected?.id == slot.id ? [.isSelected] : [])
    }
}

private struct WorkshopButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

@available(iOS 16.0, macOS 13.0, *)
private struct WorkshopSlotGrid: Layout {
    let ordinaryText: Bool
    let direction: LayoutDirection
    private let gap: CGFloat = 12
    private let canvasInsets: CGFloat = 32

    private func columns(for width: CGFloat) -> Int {
        ordinaryText && width + canvasInsets >= 320 ? 2 : 1
    }

    private func measurements(width: CGFloat, subviews: Subviews) -> (columns: Int, cardWidth: CGFloat, heights: [CGFloat]) {
        let count = columns(for: width)
        let cardWidth = max(0, (width - CGFloat(count - 1) * gap) / CGFloat(count))
        var heights: [CGFloat] = []
        for index in subviews.indices {
            let height = subviews[index].sizeThatFits(ProposedViewSize(width: cardWidth, height: nil)).height
            let row = index / count
            if row == heights.count { heights.append(height) }
            else { heights[row] = max(heights[row], height) }
        }
        return (count, cardWidth, heights)
    }

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? subviews.map { $0.sizeThatFits(.unspecified).width }.max() ?? 0
        let values = measurements(width: width, subviews: subviews)
        let height = values.heights.reduce(0, +) + CGFloat(max(0, values.heights.count - 1)) * gap
        return CGSize(width: width, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let values = measurements(width: bounds.width, subviews: subviews)
        var y = bounds.minY
        for row in values.heights.indices {
            for column in 0..<values.columns {
                let index = row * values.columns + column
                guard index < subviews.count else { continue }
                let offset = CGFloat(column) * (values.cardWidth + gap)
                let x = direction == .rightToLeft
                    ? bounds.maxX - values.cardWidth - offset
                    : bounds.minX + offset
                subviews[index].place(
                    at: CGPoint(x: x, y: y),
                    anchor: .topLeading,
                    proposal: ProposedViewSize(width: values.cardWidth, height: values.heights[row])
                )
            }
            y += values.heights[row] + gap
        }
    }
}

private struct WorkshopPalette {
    let dark: Bool
    var canvas: Color { color(0xF5F2EB, 0x14282D) }
    var notice: Color { color(0xE7DED0, 0x2D4245) }
    var enabled: Color { color(0x315F68, 0x8CC7C7) }
    var disabled: Color { color(0xAAA99F, 0x52666A) }
    var ink: Color { color(0x172D32, 0xE6F1EF) }
    var surface: Color { color(0xFFFFFF, 0x20383D) }
    var selected: Color { color(0xD6E6E5, 0x31575C) }
    var onAction: Color { color(0xF8FBFA, 0x102D30) }
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let value = dark ? darkValue : light
        return Color(.sRGB, red: Double((value >> 16) & 255) / 255, green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255, opacity: 1)
    }
}
