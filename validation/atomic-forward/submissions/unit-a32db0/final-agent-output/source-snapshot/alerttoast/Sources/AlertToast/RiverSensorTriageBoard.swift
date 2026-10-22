import SwiftUI

public struct RiverSensorIncident: Codable, Identifiable {
    public var id: String
    public var label: String
    public var detail: String
    public var available: Bool
    public var unavailableReason: String
    public var severity: String

    public init(id: String, label: String, detail: String, available: Bool, unavailableReason: String, severity: String) {
        self.id = id
        self.label = label
        self.detail = detail
        self.available = available
        self.unavailableReason = unavailableReason
        self.severity = severity
    }
}

public struct RiverSensorTriageModel: Codable {
    public var revision: String
    public var title: String
    public var subtitle: String
    public var notice: String
    public var footer: String
    public var guidance: String
    public var initialSelectedID: String?
    public var initialDetailsExpanded: Bool
    public var incidents: [RiverSensorIncident]

    public init(revision: String, title: String, subtitle: String, notice: String, footer: String, guidance: String, initialSelectedID: String?, initialDetailsExpanded: Bool, incidents: [RiverSensorIncident]) {
        self.revision = revision
        self.title = title
        self.subtitle = subtitle
        self.notice = notice
        self.footer = footer
        self.guidance = guidance
        self.initialSelectedID = initialSelectedID
        self.initialDetailsExpanded = initialDetailsExpanded
        self.incidents = incidents
    }
}

public struct RiverSensorTriageBoard: View {
    private let model: RiverSensorTriageModel
    private let onSelect: (String) -> Void
    private let onDetailsChange: (Bool) -> Void
    private let onAcknowledge: (String) -> Void

    public init(model: RiverSensorTriageModel, onSelect: @escaping (String) -> Void, onDetailsChange: @escaping (Bool) -> Void, onAcknowledge: @escaping (String) -> Void) {
        self.model = model
        self.onSelect = onSelect
        self.onDetailsChange = onDetailsChange
        self.onAcknowledge = onAcknowledge
    }

    public var body: some View {
        RiverSensorBoardContent(model: model, onSelect: onSelect, onDetailsChange: onDetailsChange, onAcknowledge: onAcknowledge)
            .id(model.revision)
    }
}

private struct RiverSensorBoardContent: View {
    let model: RiverSensorTriageModel
    let onSelect: (String) -> Void
    let onDetailsChange: (Bool) -> Void
    let onAcknowledge: (String) -> Void
    @State private var selectedID: String?
    @State private var detailsExpanded: Bool
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .subheadline) private var supportingSize: CGFloat = 14
    @ScaledMetric(relativeTo: .caption) private var severitySize: CGFloat = 12

    init(model: RiverSensorTriageModel, onSelect: @escaping (String) -> Void, onDetailsChange: @escaping (Bool) -> Void, onAcknowledge: @escaping (String) -> Void) {
        self.model = model
        self.onSelect = onSelect
        self.onDetailsChange = onDetailsChange
        self.onAcknowledge = onAcknowledge
        _selectedID = State(initialValue: model.incidents.first(where: { $0.id == model.initialSelectedID && $0.available })?.id)
        _detailsExpanded = State(initialValue: model.initialDetailsExpanded)
    }

    private var palette: RiverSensorPalette { RiverSensorPalette(dark: colorScheme == .dark) }
    private var selected: RiverSensorIncident? { model.incidents.first { $0.id == selectedID && $0.available } }
    private var disclosureLabel: String { detailsExpanded ? "Hide reading dossier" : "Show reading dossier" }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            VStack(alignment: .leading, spacing: 12) {
                copy(model.title, size: titleSize, weight: .semibold)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityIdentifier("river.title")
                copy(model.subtitle)
                VStack(alignment: .leading, spacing: 0) { copy(model.notice) }
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(palette.notice)
                    .cornerRadius(10)
                    .accessibilityElement(children: .combine)
                    .accessibilityLabel(model.notice)
                    .accessibilityIdentifier("river.notice")
            }
            .padding(.bottom, 20)

            Button(action: {
                detailsExpanded.toggle()
                onDetailsChange(detailsExpanded)
            }) {
                copy(disclosureLabel, weight: .semibold)
                    .padding(.vertical, 4)
                    .contentShape(Rectangle())
            }
            .buttonStyle(RiverSensorButtonStyle())
            .accessibilityLabel(disclosureLabel)
            .accessibilityIdentifier("river.disclosure")
            .padding(.bottom, 12)

            if detailsExpanded && selected == nil {
                copy(model.guidance)
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(palette.surface)
                    .cornerRadius(10)
                    .padding(.bottom, 12)
            }

            VStack(alignment: .leading, spacing: 12) {
                ForEach(model.incidents) { incident in
                    VStack(alignment: .leading, spacing: 12) {
                        HStack(alignment: .top, spacing: 2) {
                            Color.clear.frame(width: 10)
                            Button(action: {
                                guard incident.available else { return }
                                selectedID = incident.id
                                onSelect(incident.id)
                            }) {
                                VStack(alignment: .leading, spacing: 12) {
                                    copy(incident.label + (incident.available ? "" : " · Unavailable"), weight: .semibold)
                                    copy(incident.severity.uppercased(), size: severitySize, weight: .semibold)
                                    if !incident.available {
                                        copy(incident.unavailableReason, size: supportingSize)
                                    }
                                }
                                .padding(16)
                                .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
                                .background(selected?.id == incident.id ? palette.selected : palette.surface)
                                .cornerRadius(10)
                                .contentShape(RoundedRectangle(cornerRadius: 10))
                            }
                            .buttonStyle(RiverSensorButtonStyle())
                            .disabled(!incident.available)
                            .accessibilityAddTraits(selected?.id == incident.id ? .isSelected : [])
                            .accessibilityIdentifier("river.choice.\(incident.id)")
                        }
                        .overlay(
                            RiverSensorTimelineRail().fill(palette.action).frame(width: 2)
                                .padding(.leading, 4)
                                .accessibilityHidden(true),
                            alignment: .leading
                        )
                        if detailsExpanded && selected?.id == incident.id {
                            copy(incident.detail)
                                .padding(.leading, 24)
                                .padding(.trailing, 12)
                                .padding(.vertical, 4)
                        }
                    }
                }
            }
            .padding(.bottom, 20)

            copy(selected.map { "Reviewing: \($0.label)" } ?? "No alert selected", weight: .semibold)
                .accessibilityIdentifier("river.summary")
                .padding(.bottom, 20)

            Button(action: {
                if let selected = selected { onAcknowledge(selected.id) }
            }) {
                copy("Acknowledge alert", weight: .semibold, color: palette.onAction)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 16)
                    .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
                    .background(selected == nil ? palette.disabled : palette.action)
                    .cornerRadius(10)
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(RiverSensorButtonStyle())
            .disabled(selected == nil)
            .accessibilityLabel("Acknowledge alert")
            .accessibilityIdentifier("river.submit")
            .padding(.bottom, 20)

            copy(model.footer, size: supportingSize)
                .accessibilityIdentifier("river.footer")
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.canvas)
        .cornerRadius(12)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("river.canvas")
    }

    private func copy(_ value: String, size: CGFloat? = nil, weight: Font.Weight = .regular, color: Color? = nil) -> some View {
        Text(value)
            .font(.system(size: size ?? bodySize, weight: weight))
            .foregroundColor(color ?? palette.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct RiverSensorPalette {
    let dark: Bool
    var canvas: Color { color(dark ? 0x14282D : 0xF5F2EB) }
    var notice: Color { color(dark ? 0x2D4245 : 0xE7DED0) }
    var action: Color { color(dark ? 0x8CC7C7 : 0x315F68) }
    var disabled: Color { color(dark ? 0x52666A : 0xAAA99F) }
    var ink: Color { color(dark ? 0xE6F1EF : 0x172D32) }
    var surface: Color { color(dark ? 0x20383D : 0xFFFFFF) }
    var selected: Color { color(dark ? 0x31575C : 0xD6E6E5) }
    var onAction: Color { color(dark ? 0x102D30 : 0xF8FBFA) }
    private func color(_ rgb: UInt32) -> Color {
        Color(.sRGB, red: Double((rgb >> 16) & 255) / 255, green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255, opacity: 1)
    }
}

private struct RiverSensorTimelineRail: Shape {
    func path(in rect: CGRect) -> Path {
        Path(CGRect(x: rect.minX, y: rect.minY, width: rect.width, height: rect.height + 12))
    }
}

private struct RiverSensorButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}
